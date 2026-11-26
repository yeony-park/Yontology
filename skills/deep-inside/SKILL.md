---
name: deep-inside
description: Apply a proportional expert-quality preflight to every request; explicitly invoke with /deep-inside for complex work.
---

# Deep Inside

Before proposing or implementing a solution, apply the Deep Inside method:

1. Expert gap: identify what a top practitioner would do that the requester has not explicitly specified.
2. Raw sources: identify and inspect the most primary evidence available.
3. Methods and tools: choose concrete methods, algorithms, tools, data structures and operational controls.
4. Independent validation: define how to establish correctness independently of the implementation.
5. Deep prompt rewrite: internally reformulate the task in English, preserving intent, constraints and acceptance criteria. Respond in Korean unless the user asks otherwise.

Increase depth and reliability, not breadth. For a simple request, apply this silently in one pass. For complex work, surface only useful assumptions, evidence and validation results, not private reasoning. Do not invent sources, tests or permissions. Never launch extra agents merely to apply this skill. A hook can inject the compact preflight without a second model call. Explicit invocation may use this full skill. This version reconstructs the established method; it is not a verbatim copy of an unavailable original prompt.
