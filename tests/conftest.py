import sys
import os

# Ensure root, core, and scripts directories are in sys.path during pytest execution
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CORE_DIR = os.path.join(ROOT_DIR, "core")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")

for d in [ROOT_DIR, CORE_DIR, SCRIPTS_DIR]:
    if d not in sys.path:
        sys.path.insert(0, d)
