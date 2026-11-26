#!/usr/bin/env python3
"""Session reminder only. No transcript reads, no forced agent loop, no LLM calls."""
import sys
import json

def main():
    try:
        event = json.load(sys.stdin).get("hook_event_name")
    except (ValueError, AttributeError):
        return
    if event == "SessionStart":
        print("For tracked Yontology tasks, resume from the current task checkpoint and relevant wiki references. Save incremental checkpoints at meaningful milestones; never wait for quota exhaustion.")
    # PreCompact and Stop are not portable context-injection points.
    # Keep these non-blocking; semantic checkpoint updates belong to the skill.

if __name__ == "__main__":
    main()
