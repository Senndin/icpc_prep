#!/usr/bin/env python
"""Утиліта командного рядка Django для адміністрування проєкту."""
import os
import sys


def main():
    """Запускає команду адміністрування Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
