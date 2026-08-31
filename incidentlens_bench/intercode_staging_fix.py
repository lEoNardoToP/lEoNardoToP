#!/usr/bin/env python3
"""Infrastructure-only wrapper for the frozen InterCode holdout.

The GitHub hosted Docker daemon cannot traverse tempfile.mkdtemp() directories
created as 0700 by the runner uid. This wrapper changes only the staged copy's
filesystem permissions before the read-only bind mount. It does not change task
selection, prompts, action budget, model, scoring, expected flags, or sandbox
capabilities.
"""
import os
from pathlib import Path
import intercode_local_holdout as holdout

_original_sanitize = holdout.sanitize_challenge


def _docker_readable_sanitize(challenge_dir, files):
    staged = _original_sanitize(challenge_dir, files)
    for root, dirs, names in os.walk(staged):
        os.chmod(root, 0o755)
        for d in dirs:
            os.chmod(Path(root) / d, 0o755)
        for name in names:
            p = Path(root) / name
            try:
                original_mode = p.stat().st_mode
                os.chmod(p, 0o555 if (original_mode & 0o111) else 0o444)
            except FileNotFoundError:
                pass
    return staged


holdout.sanitize_challenge = _docker_readable_sanitize

if __name__ == '__main__':
    holdout.main()
