#!/usr/bin/env python3
"""Portable CLI launcher; also finds the Codex desktop bundled Node runtime."""
import os
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parent
node = shutil.which('node')
if not node:
    bundled = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
    if bundled.is_file():
        node = str(bundled)
if not node:
    sys.exit('Node.js 20+ is required. Install Node.js and retry.')
if not (root / 'node_modules/typescript').exists():
    sys.exit('Dependencies are missing. Run pnpm install --frozen-lockfile in ' + str(root))
os.execv(node, [node, str(root / 'cli/main.mjs'), *sys.argv[1:]])
