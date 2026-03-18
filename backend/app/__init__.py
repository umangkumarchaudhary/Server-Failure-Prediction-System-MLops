"""PredictrAI Backend."""

from pathlib import Path
import sys


# Make the repo-level ``ml`` package importable when the backend starts from ``backend/``.
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))
