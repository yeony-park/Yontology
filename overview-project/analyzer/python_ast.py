"""Read JSON source input; return symbols and references without importing user code."""
import ast
import json
import sys


def analyze(path, source):
    nodes, refs, imports = [], [], []
    tree = ast.parse(source, filename=path)
    file_id = 'file:' + path
    scope = [file_id]
    names = []
    classes = []
    local_scopes = []

    class Visitor(ast.NodeVisitor):
        def definition(self, node, kind):
            name = node.name
            qualified = '.'.join(names + [name])
            ident = path + '::' + qualified
            nodes.append(dict(id=ident, name=name, qualified=qualified, kind=kind,
                              file=path, line=node.lineno, endLine=node.end_lineno,
                              parent=scope[-1], language='python'))
            return ident

        def visit_ClassDef(self, node):
            ident = self.definition(node, 'class')
            for base in node.bases:
                refs.append(dict(source=ident, name=ast.unparse(base), kind='inherits', line=node.lineno))
            classes.append(node.name)
            scope.append(ident)
            names.append(node.name)
            for child in node.body:
                self.visit(child)
            names.pop()
            scope.pop()
            classes.pop()

        def visit_FunctionDef(self, node):
            kind = 'test' if node.name.startswith('test_') else ('method' if classes else 'function')
            ident = self.definition(node, kind)
            args = node.args
            positional = args.posonlyargs + args.args
            defaults = [None] * (len(positional) - len(args.defaults)) + args.defaults
            params = []
            for arg, default in zip(positional, defaults):
                params.append(dict(name=arg.arg, type=ast.unparse(arg.annotation) if arg.annotation else None,
                                   default=ast.unparse(default) if default is not None else None))
            for arg, default in zip(args.kwonlyargs, args.kw_defaults):
                params.append(dict(name=arg.arg, type=ast.unparse(arg.annotation) if arg.annotation else None,
                                   default=ast.unparse(default) if default is not None else None, keywordOnly=True))
            for arg, prefix in [(args.vararg, '*'), (args.kwarg, '**')]:
                if arg:
                    params.append(dict(name=prefix + arg.arg, type=ast.unparse(arg.annotation) if arg.annotation else None))
            returns, calls = [], []
            class Returns(ast.NodeVisitor):
                def visit_FunctionDef(self, child):
                    pass
                visit_AsyncFunctionDef = visit_FunctionDef
                visit_ClassDef = visit_FunctionDef
                visit_Lambda = visit_FunctionDef
                def visit_Call(self, child):
                    calls.append(dict(name=ast.unparse(child.func), line=child.lineno))
                    self.generic_visit(child)
                def visit_Return(self, child):
                    returns.append(dict(expression=ast.unparse(child.value) if child.value else 'None', line=child.lineno))
                    self.generic_visit(child)
                def visit_Yield(self, child):
                    returns.append(dict(expression=ast.unparse(child.value) if child.value else 'None', line=child.lineno, kind='yield'))
                visit_YieldFrom = visit_Yield
            for child in node.body:
                Returns().visit(child)
            nodes[-1]['contract'] = dict(parameters=params, returns=returns, calls=calls,
                                         returnType=ast.unparse(node.returns) if node.returns else None,
                                         documentation=ast.get_docstring(node) or '',
                                         asyncFunction=isinstance(node, ast.AsyncFunctionDef))
            local_names = {a.arg for a in positional + args.kwonlyargs}
            if args.vararg: local_names.add(args.vararg.arg)
            if args.kwarg: local_names.add(args.kwarg.arg)
            global_names = set()
            class Bindings(ast.NodeVisitor):
                def visit_Name(self, child):
                    if isinstance(child.ctx, ast.Store): local_names.add(child.id)
                def visit_Global(self, child): global_names.update(child.names)
                def visit_Nonlocal(self, child): local_names.update(child.names)
                def visit_FunctionDef(self, child): local_names.add(child.name)
                visit_AsyncFunctionDef = visit_FunctionDef
                visit_ClassDef = visit_FunctionDef
                def visit_Import(self, child):
                    for alias in child.names: local_names.add(alias.asname or alias.name.split('.')[0])
                def visit_ImportFrom(self, child):
                    for alias in child.names: local_names.add(alias.asname or alias.name)
            for child in node.body: Bindings().visit(child)
            local_scopes.append(local_names - global_names)
            scope.append(ident)
            names.append(node.name)
            for child in node.body:
                self.visit(child)
            names.pop()
            scope.pop()
            local_scopes.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Import(self, node):
            for alias in node.names:
                imports.append(dict(module=alias.name, local=alias.asname or alias.name.split('.')[0],
                                    imported='*', level=0, line=node.lineno))

        def visit_ImportFrom(self, node):
            for alias in node.names:
                imports.append(dict(module=node.module or '', local=alias.asname or alias.name,
                                    imported=alias.name, level=node.level, line=node.lineno))

        def visit_Call(self, node):
            name = ast.unparse(node.func)
            if classes and name.startswith(('self.', 'cls.')):
                name = classes[-1] + '.' + name.split('.', 1)[1]
            refs.append(dict(source=scope[-1], name=name, kind='calls', line=node.lineno,
                             call=dict(expression=ast.unparse(node), arguments=[ast.unparse(a) for a in node.args] +
                                       [(k.arg + '=' if k.arg else '**') + ast.unparse(k.value) for k in node.keywords])))
            self.generic_visit(node)

        def visit_Name(self, node):
            refs.append(dict(source=scope[-1], name=node.id,
                             kind='writes' if isinstance(node.ctx, ast.Store) else 'reads', line=node.lineno,
                             shadowed=any(node.id in names for names in local_scopes)))
            if len(scope) == 1 and isinstance(node.ctx, ast.Store):
                ident = path + '::' + node.id
                if not any(n['id'] == ident for n in nodes):
                    nodes.append(dict(id=ident, name=node.id, qualified=node.id, kind='variable',
                                      file=path, line=node.lineno, endLine=node.end_lineno,
                                      parent=file_id, language='python'))

    Visitor().visit(tree)
    return dict(nodes=nodes, refs=refs, imports=imports)


if __name__ == '__main__':
    result = {}
    for item in json.load(sys.stdin):
        try:
            result[item['path']] = analyze(item['path'], item['source'])
        except (SyntaxError, ValueError, RecursionError) as exc:
            result[item['path']] = dict(nodes=[], refs=[], imports=[], error=str(exc))
    json.dump(result, sys.stdout)
