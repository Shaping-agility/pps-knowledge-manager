#!/usr/bin/env python3
"""
Radon complexity checker with utils directory excluded by default.
"""

import subprocess
import sys
import os


def run_radon_check(min_complexity="B", exclude_utils=True):
    """Run radon with default exclusions."""
    cmd = ["radon", "cc", "src/pps_knowledge_manager/", "--min", min_complexity]

    if exclude_utils:
        cmd.extend(["--exclude", "src/pps_knowledge_manager/utils/*"])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Radon check failed: {e}")
        print(e.stdout)
        print(e.stderr)
        return False


if __name__ == "__main__":
    # Parse command line arguments
    min_complexity = "B"
    exclude_utils = True

    for arg in sys.argv[1:]:
        if arg in ["A", "B", "C", "D", "E", "F"]:
            min_complexity = arg
        elif arg == "--include-utils":
            exclude_utils = False

    success = run_radon_check(min_complexity, exclude_utils)
    sys.exit(0 if success else 1)
