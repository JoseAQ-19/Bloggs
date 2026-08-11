#!/usr/bin/env python3
"""
audit_v2.py — Root wrapper delegante hacia scripts/audit_v2.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from audit_v2 import run

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', '--section', dest='section', type=str, default=None)
    parser.add_argument('--lang', type=str, choices=['es', 'en'], default=None)
    args = parser.parse_args()
    run(args.section, args.lang)
