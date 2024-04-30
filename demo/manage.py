#!/usr/bin/env python

import os
import sys

from pathlib import Path

from django.core.management import execute_from_command_line


def main():
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    os.environ["DJANGO_SETTINGS_MODULE"] = "demo.settings"
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
