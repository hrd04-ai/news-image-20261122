"""main.py — entrypoint for the news-image-20261122 entry.

Draws the 22 November 2026 front page and writes it to entry.png in the
output directory. Run locally with:

    MAKEFUN_OUTPUT_DIR=out python3 main.py

The grader runs it with no network, stdlib only, and compares two runs
byte for byte, so the drawing is fully deterministic.
"""

import os
import sys

# The grader runs `python3 -P -s /bot/main.py`: -P (safe_path) does NOT
# prepend the script's directory to sys.path, so a plain
# `import make_image` fails with ModuleNotFoundError. Point sys.path at
# this file's own directory first.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import make_image


def output_dir():
    """Where entry.png goes: the harness dir, /output, or local out/."""
    env_dir = os.environ.get('MAKEFUN_OUTPUT_DIR')
    if env_dir:
        return env_dir
    if os.path.isdir('/output'):
        return '/output'
    return 'out'


def main():
    out_dir = output_dir()
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'entry.png')
    make_image.render(path)
    print('wrote ' + path)


if __name__ == '__main__':
    main()
