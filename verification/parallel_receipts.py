"""Bounded parallel orchestration of the unchanged saved-record scanner.

Each chunk is independently passed through nested_audit.scan_archives. The parent
rejects duplicate exclusions and any cutoff-29 witness before the unchanged
nested partition coverage audit. No native distance search is launched.
"""
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from pathlib import Path
import tempfile
import nested_audit
_SERIAL_SCAN = nested_audit.scan_archives
_CAMPAIGNS = _CODE = None

def _init(campaigns, code):
    global _CAMPAIGNS, _CODE
    _CAMPAIGNS, _CODE = campaigns, code

def _scan_one(name):
    path = Path(name)
    with tempfile.TemporaryDirectory(prefix='lp-receipt-chunk-') as td:
        root = Path(td)
        worker = root / 'workers' / 'one'
        worker.mkdir(parents=True)
        (worker / path.name).symlink_to(path)
        if path.name.endswith('.gz'):
            metadata = path.with_suffix(path.suffix + '.json')
            (worker / metadata.name).symlink_to(metadata)
        scratch = root / 'scratch'
        scratch.mkdir()
        return _SERIAL_SCAN(root, _CAMPAIGNS, _CODE, scratch)

def scan_archives(snapshot, campaigns, code, scratch, workers=8):
    assert all(c['config']['cutoff'] == 29 for c, _ in campaigns.values())
    paths = sorted(str(p.resolve()) for p in (snapshot / 'workers').glob('*/evidence*.sqlite*')
                   if p.name == 'evidence.sqlite' or p.name.endswith('.sqlite.gz'))
    assert paths and 1 <= workers <= 16
    chosen, attempts = {}, 0
    with ProcessPoolExecutor(max_workers=workers,
            mp_context=multiprocessing.get_context('fork'),
            initializer=_init, initargs=(campaigns, code)) as pool:
        for i, (exclusions, witnesses, count) in enumerate(pool.map(_scan_one, paths), 1):
            assert not witnesses, 'A logical witness contradicts cutoff-29 exclusion'
            assert chosen.keys().isdisjoint(exclusions), 'Duplicate completed leaf across chunks'
            chosen.update(exclusions)
            attempts += count
            if i % 25 == 0 or i == len(paths):
                print(f'Audited {i}/{len(paths)} chunks; {attempts} attempts', flush=True)
    return chosen, {}, attempts
