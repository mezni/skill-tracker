import os
import tempfile

os.environ.setdefault(
    "SKILL_TRACKER_DB",
    os.path.join(tempfile.mkdtemp(prefix="skill-tracker-import-"), "startup.db"),
)
