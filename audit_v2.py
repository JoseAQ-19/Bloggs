#!/usr/bin/env python3
"""
audit_v2.py — Root wrapper delegante hacia scripts/audit_v2.py
"""

import sys
import os
import importlib.util

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
scripts_audit_path = os.path.join(ROOT_DIR, 'scripts', 'audit_v2.py')

spec = importlib.util.spec_from_file_location("scripts_audit_v2", scripts_audit_path)
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)
run = audit_module.run

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', '--section', dest='section', type=str, default=None)
    parser.add_argument('--lang', type=str, choices=['es', 'en'], default=None)
    args = parser.parse_args()
    run(args.section, args.lang)
