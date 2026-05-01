from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.memory import MemoryCore


def main() -> None:
    memory = MemoryCore('./data/selfcheck.db')
    memory.record_event('wf-test', 'selfcheck', 'STARTED', {'ok': True})
    memory.record_failure('wf-test', 'selfcheck', 'synthetic_error', fingerprint='SELFTEST')
    snap = memory.reconstruct_workflow('wf-test')
    assert len(snap['events']) >= 1
    assert len(snap['failures']) >= 1
    print('selfcheck_ok')


if __name__ == '__main__':
    main()
