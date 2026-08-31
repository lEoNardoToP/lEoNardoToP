#!/usr/bin/env python3
"""Infrastructure-only wrapper for the frozen InterCode holdout.

This wrapper fixes two GitHub-hosted Docker filesystem issues discovered before
any model action was executed: (1) mkdtemp staging directories were not
traversable by the Docker daemon, and (2) `cp -a` attempted to preserve host
ownership inside a cap-drop=ALL sandbox. It changes only staging/copy mechanics.
Task selection, prompts, action budget, model, scoring, expected flags, tool
allowlist, network isolation, and sandbox security capabilities are unchanged.
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


def _ownership_safe_start_sandbox(image, staged, tag):
    name = f'il-ctf-{tag}-{os.getpid()}'
    p = holdout.docker([
        'run','-d','--name',name,
        '--network','none',
        '--cap-drop','ALL',
        '--security-opt','no-new-privileges',
        '--pids-limit','96',
        '--memory','1024m',
        '--cpus','2',
        '--read-only',
        '-v',f'{staged.resolve()}:/challenge:ro',
        '--tmpfs','/work:rw,nosuid,nodev,size=256m',
        '--workdir','/work',
        image,'sleep','3600'
    ], 60)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-1000:])
    # Same challenge bytes and modes, but deliberately do not preserve host uid/gid.
    init = holdout.docker([
        'exec',name,'bash','-lc',
        'cp -r --no-preserve=ownership /challenge/. /work/ && ls -la'
    ], 30)
    if init.returncode != 0:
        holdout.docker(['rm','-f',name],20)
        raise RuntimeError(init.stderr[-1000:])
    return name, holdout.clean_text(init.stdout,3000)


holdout.sanitize_challenge = _docker_readable_sanitize
holdout.start_sandbox = _ownership_safe_start_sandbox

if __name__ == '__main__':
    holdout.main()
