#!/usr/bin/env python3
"""
SessionStart hook: reads .hody/profile.yaml and injects project context
into the system message so all agents know the current tech stack.
"""
import json
import sys
import os


def main():
    try:
        input_data = json.load(sys.stdin)
        cwd = input_data.get("cwd", os.getcwd())

        profile_path = os.path.join(cwd, ".hody", "profile.yaml")
        if not os.path.isfile(profile_path):
            print("{}")
            sys.exit(0)

        with open(profile_path, "r") as f:
            profile_content = f.read()

        # Extract key info for a concise summary
        lines = profile_content.strip().splitlines()
        summary_parts = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("name:"):
                summary_parts.append(stripped)
            elif stripped.startswith("framework:"):
                summary_parts.append(stripped)
            elif stripped.startswith("language:"):
                summary_parts.append(stripped)
            elif stripped.startswith("database:"):
                summary_parts.append(stripped)
            elif stripped.startswith("ci:"):
                summary_parts.append(stripped)

        summary = " | ".join(summary_parts) if summary_parts else "profile loaded"

        output = {
            "systemMessage": f"[Hody Workflow] Project: {summary}. Full profile at .hody/profile.yaml"
        }
        print(json.dumps(output))
        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block session on hook error


if __name__ == "__main__":
    main()
