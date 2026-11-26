#!/usr/bin/env python3
"""UserPromptSubmit: constant lightweight instruction, no LLM or data collection."""
import sys

def main():
    # Consume the hook payload without reading/logging the user's prompt.
    sys.stdin.read()
    print("Deep Inside: silently identify expert gap, primary evidence, concrete methods/tools and independent validation; internally refine the task in English, answer in Korean unless requested otherwise. Scale to the task; increase depth and reliability, not breadth. Preserve authorization and constraints; do not expose private reasoning or delegate merely for this check.")

if __name__ == "__main__":
    main()
