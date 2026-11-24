"""Audit compact archives and a complete nested residue-partition cover.

Native source recognition, physical matrices, receipts and witnesses are checked
against upstream QEDist. This adds the mixed-partition union check needed after
refinement; it does not alter the native search or upstream receipt checker.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'vendor/QEDist'))
from cssdist.audit import check_receipt, configuration
from cssdist.code import CSSCode, digest
from cssdist.engine import audited_source_hashes, uses_dynamic_storage
from cssdist.lp_blocks import search_problems


def read(p):
    return json.loads(p.read_text())


def header(path, code):
    c = read(path / 'campaign.json')
    assert c['schema'] == 'cssdist.campaign.v1'
    assert c['code_sha256'] == code.fingerprint
    assert read(path / 'code.json') == code.document
    cfg = c['config']
    sources = audited_source_hashes(path / 'engine', cfg['native_profile'],
                                   allow_cyclic_01=not cfg.get('generator_symmetry'),
                                   proposed_additions=cfg.get('proposed_additions', False))
    assert sources == c['engine']['source_sha256']
    assert cfg == configuration(code, cfg['cutoff'], cfg['shards'], cfg['split_weight'],
                                cfg['use_symmetry'], cfg['coset_pruning'],
                                cfg['native_profile'], cfg.get('proposed_additions', False),
                                cfg.get('large_capacity'))
    assert cfg.get('large_capacity') == uses_dynamic_storage(sources)
    bb = (path / 'engine/build.json').read_bytes()
    assert digest(bb) == c['engine']['build_sha256']
    build = json.loads(bb)
    assert build['identity']['source_sha256'] == sources
    assert digest((path / 'engine/exact').read_bytes()) == build['executable_sha256'] == c['engine']['executable_sha256']
    problems = search_problems(code, cfg)
    assert set(problems) == set(c['input_sha256'])
    for side, problem in problems.items():
        data = (path / f'inputs/{side}.mat').read_bytes()
        assert data == problem.text().encode()
        assert digest(data) == c['input_sha256'][side]
    if cfg.get('generator_symmetry'):
        assert set(c['symmetry_sha256']) == set(problems)
        for side, problem in problems.items():
            data = (path / f'inputs/{side}.symmetry').read_bytes()
            assert data == problem.symmetry_text().encode()
            assert digest(data) == c['symmetry_sha256'][side]
    return c, problems


def scan_archives(snapshot, campaigns, code, scratch):
    chosen = {}
    witness_keys = set()
    witness_best = {}
    attempts = 0
    for p in sorted((snapshot / 'workers').glob('*/evidence.sqlite')):
        db = sqlite3.connect(f'file:{p.resolve()}?mode=ro', uri=True)
        assert db.execute('PRAGMA quick_check').fetchone()[0] == 'ok', p
        placeholders=','.join('?' for _ in campaigns)
        for aid, w, side, shard, rb, stdout, stderr, _ in db.execute(f'SELECT * FROM attempts WHERE w IN ({placeholders}) ORDER BY id',tuple(campaigns)):
            if w not in campaigns:
                continue
            campaign, problems = campaigns[w]
            for name, data in [('receipt.json', rb), ('stdout.jsonl', stdout), ('stderr.txt', stderr)]:
                (scratch / name).write_bytes(data)
            checked = check_receipt(scratch / 'receipt.json', scratch, campaign, code,
                                    side, shard, problems[side])
            attempts += 1
            key = (w, side, shard)
            for word in checked['witnesses']:
                witness_keys.add(key)
                assert key not in chosen, f'Witness contradicts exclusion: {key}'
                assert code.is_logical(word, problems[side].sector)
                sector = problems[side].sector
                if sector not in witness_best or word.bit_count() < witness_best[sector].bit_count():
                    witness_best[sector] = word
            if checked['status'] == 'excluded':
                assert key not in witness_keys, f'Exclusion contradicts witness: {key}'
                assert key not in chosen, f'Duplicate completed leaf: {key}'
                chosen[key] = (checked['terminal'], digest(rb))
        db.close()
        print(f'Audited {attempts} attempts; {len(chosen)} completed exclusions', file=sys.stderr, flush=True)

    return chosen, witness_best, attempts


def coverage(tasks, configs, exclusions, inherited):
    """Each node is either a certified leaf or exactly all its residue children."""
    counts = {w: c['config']['shards'] for w, c in configs.items()}
    weights = sorted({c['config']['cutoff'] for c in configs.values()})
    all_keys = set(tasks)
    parentless = set(all_keys)
    for key, status in tasks.items():
        w, side, i = key
        if status != 'split':
            continue
        assert w + 1 in counts and counts[w + 1] % counts[w] == 0
        a, b = configs[w]['config'], configs[w + 1]['config']
        assert {k: v for k, v in a.items() if k != 'shards'} == {k: v for k, v in b.items() if k != 'shards'}
        children = {(w + 1, side, i + k * counts[w])
                    for k in range(counts[w + 1] // counts[w])}
        assert children <= all_keys, f'Missing children of {key}'
        parentless -= children
    expected_roots = set()
    for weight in weights:
        first = min(w for w in counts if configs[w]['config']['cutoff'] == weight)
        expected_roots |= {(first, s, i) for s in configs[first]['input_sha256'] for i in range(counts[first])}
    assert parentless == expected_roots, 'Uncovered/overlapping partition tree roots'
    for key in all_keys - expected_roots:
        w, side, i = key
        assert (w - 1, side, i % counts[w - 1]) in tasks
        assert tasks[(w - 1, side, i % counts[w - 1])] == 'split'
    result = {}
    for weight in weights:
        result[weight] = {}
        for side in configs[min(counts)]['input_sha256']:
            complete = True
            owned = 0
            frontier = None
            leaves = missing = 0
            for key, status in tasks.items():
                w, s, _ = key
                if s != side or configs[w]['config']['cutoff'] != weight or status == 'split':
                    continue
                leaves += 1
                record = inherited.get(key) if status == 'inherited_excluded' else exclusions.get(key)
                if status in ('excluded', 'inherited_excluded'):
                    assert record is not None, f'Queue exclusion without evidence: {key}'
                if record is None:
                    complete = False
                    missing += 1
                    continue
                terminal = record[0]
                common = tuple(terminal[k] for k in ('frontier_seen', 'frontier_digest', 'common_nodes'))
                if frontier is None:
                    frontier = common
                assert common == frontier, 'Mixed partitions traversed different frontiers'
                owned += terminal['frontier_owned']
            if complete:
                assert frontier is not None and owned == frontier[0], 'Incomplete frontier union'
            result[weight][side] = dict(complete=complete, leaves=leaves, missing=missing,
                                       frontier=frontier, frontier_owned=owned)
    return result


def audit_stage(snapshot, weight, output=None):
    started = time.time()
    code = CSSCode.load(snapshot / 'code.json')
    paths=sorted(p for p in (snapshot/'campaigns').glob('w*') if p.is_dir() and p.name[1:].isdigit() and int(p.name[1:])//100==weight)
    campaigns={int(p.name[1:]):header(p,code) for p in paths}
    assert campaigns, 'Missing campaign configurations'
    with tempfile.TemporaryDirectory(prefix='mitten-stage-audit-') as td:
        excluded, witnesses, attempts = scan_archives(snapshot, campaigns, code, Path(td))
    with (snapshot / 'queue.lock').open('a') as lock:
        import fcntl
        fcntl.flock(lock, fcntl.LOCK_EX)
        db = sqlite3.connect(snapshot / 'queue.sqlite')
        tasks = {(w,s,i): st for w,s,i,st in db.execute(
            'SELECT w,side,shard,status FROM tasks WHERE w>=? AND w<?', (weight*100,(weight+1)*100))}
        db.close()
    cover = coverage(tasks, {w:c for w,(c,_) in campaigns.items()}, excluded, {})[weight]
    bounds = {}
    for sector in ('X','Z'):
        complete = all(v['complete'] for part,v in cover.items() if part.startswith(sector+'-'))
        words = [code.upper_witnesses()[sector]] + ([witnesses[sector]] if sector in witnesses else [])
        word = min(words, key=int.bit_count)
        assert code.is_logical(word, sector)
        bounds[sector] = dict(lower=weight+1 if complete else 1, upper=word.bit_count(),
                              complete=complete, support=[i for i in range(code.n) if word>>i&1])
    result = dict(code_sha256=code.fingerprint, cutoff=weight, complete=all(v['complete'] for v in cover.values()),
                  coverage=cover, sector_bounds=bounds, attempts=attempts,
                  queue_scope_sha256=digest(json.dumps([[*k,v] for k,v in sorted(tasks.items())]).encode()),
                  nodes=sum(t[0]['nodes'] for t in excluded.values()),
                  method='Unmodified upstream source/receipt audit plus physical symmetry inputs, nested residue coverage and complete frontier union',
                  evidence_kind='Source-bound exhaustive execution records, not a formal per-node proof',
                  finished=time.time(), wall_seconds=time.time()-started)
    if output:
        from cssdist.campaign import write_json
        write_json(output,result)
    return result

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,default=ROOT);p.add_argument('--weight',type=int,required=True);p.add_argument('--output',type=Path)
    a=p.parse_args();print(json.dumps(audit_stage(a.snapshot,a.weight,a.output)),flush=True)
