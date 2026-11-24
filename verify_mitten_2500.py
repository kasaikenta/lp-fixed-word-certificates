"""Reconstruct the added example and check ranks, logicals, and audit coverage.

The lower-bound execution audit is an input, not rerun by this script.
All matrix arithmetic is over GF(2); no remote computation is launched.
"""
from pathlib import Path
import collections
import hashlib
import itertools
import json
from generate_construction_table import MITTEN, evaluate
from verify_selected import basis, matrices, remainder, supports, transpose

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'evidence/mitten_2500_distance30'


def apply(rows, vector):
    return sum(((row & vector).bit_count() % 2) << i for i, row in enumerate(rows))


def inverse(rows):
    n = len(rows)
    augmented = [row | (1 << (n+i)) for i, row in enumerate(rows)]
    for c in range(n):
        pivot = next(i for i in range(c, n) if (augmented[i] >> c) & 1)
        augmented[c], augmented[pivot] = augmented[pivot], augmented[c]
        for i in range(n):
            if i != c and (augmented[i] >> c) & 1:
                augmented[i] ^= augmented[c]
    assert [r & ((1 << n)-1) for r in augmented] == [1 << i for i in range(n)]
    result = [r >> n for r in augmented]
    assert all(apply(rows, v) == 1 << i for i, v in enumerate(transpose(result, n)))
    return result


def main():
    doc = json.loads((DATA / 'code.json').read_text())
    spec = evaluate(MITTEN, (25, 20, 4), 'ij')
    n, hx, hz = matrices(spec)
    assert n == 2500 == doc['n']
    assert [list(supports(v)) for v in hx] == doc['hx']
    assert [list(supports(v)) for v in hz] == doc['hz']
    assert all((x & z).bit_count() % 2 == 0 for x in hx for z in hz)
    bx, bz = basis(hx), basis(hz)
    assert len(bx) == len(bz) == 1000 and n - len(bx) - len(bz) == 500
    q = 500
    a0 = [v & ((1 << q)-1) for v in hx[:q]]
    a1 = [(v >> (2*q)) & ((1 << q)-1) for v in hx[:q]]
    b0 = [v & ((1 << q)-1) for v in hz[:q]]
    b1 = [(v >> q) & ((1 << q)-1) for v in hz[:q]]
    ranks = [len(basis(rows)) for rows in [a0, a1, b0, b1]]
    assert ranks == [460, 500, 500, 500]
    ia, ib = inverse(a1), inverse(b1)
    xs = [(1 << g) | (apply(ib, v) << q) for g, v in enumerate(transpose(b0, q))]
    zs = [(1 << g) | (apply(ia, v) << (2*q)) for g, v in enumerate(transpose(a0, q))]
    assert all(apply(hz, x) == 0 and remainder(x, bx) for x in xs)
    assert all(apply(hx, z) == 0 and remainder(z, bz) for z in zs)
    assert all((x & z).bit_count() % 2 == (i == j)
               for i, x in enumerate(xs) for j, z in enumerate(zs))
    assert {v.bit_count() for v in xs} == {256}
    assert {v.bit_count() for v in zs} == {262}
    for side, words in [('X', xs), ('Z', zs)]:
        for g in range(q):
            a, b = divmod(g, 20)
            translated = 0
            for pos in supports(words[0]):
                block, local = divmod(pos, q)
                i, j = divmod(local, 20)
                u, v = ((a + pow(4, b, 25)*i) % 25, (b+j) % 20) if side == 'X' else ((i + pow(4, j, 25)*a) % 25, (j+b) % 20)
                translated ^= 1 << (block*q + u*20+v)
            assert translated == words[g]
    girths = []
    for rows in [hx, hz]:
        assert {v.bit_count() for v in rows} == {9}
        assert {v.bit_count() for v in transpose(rows, n)} == {3, 6}
        pairs = collections.Counter(pair for row in rows for pair in itertools.combinations(supports(row), 2))
        assert any(count > 1 for count in pairs.values())
        girths.append(4)
    digest = hashlib.sha256((json.dumps(doc, sort_keys=True, indent=2) + '\n').encode()).hexdigest()
    audit = json.loads((DATA / 'audit.json').read_text())
    witness = json.loads((DATA / 'witness.json').read_text())
    assert audit['code_sha256'] == witness['code_sha256'] == digest
    assert audit['complete'] and audit['cutoff'] == 29
    assert set(audit['coverage']) == {'X-anchor', 'X-stripe', 'Z-anchor', 'Z-stripe'}
    assert all(c['complete'] and c['missing'] == 0 and c['frontier'][0] == c['frontier_owned'] for c in audit['coverage'].values())
    assert witness['side'] == 'Z' and len(set(witness['support'])) == len(witness['support']) == witness['weight'] == 30
    v = sum(1 << i for i in witness['support'])
    assert apply(hx, v) == 0 and remainder(v, bz)
    upper_x = json.loads((DATA / 'extra_witness_X.json').read_text())
    assert upper_x['code_sha256'] == digest and upper_x['side'] == 'X'
    assert len(set(upper_x['support'])) == len(upper_x['support']) == upper_x['weight'] == 122
    v = sum(1 << i for i in upper_x['support'])
    assert apply(hz, v) == 0 and remainder(v, bx)
    result = dict(n=n, k=500, distance=30, code_sha256=digest,
                  matrix_match=True, component_ranks=ranks,
                  canonical_pairs_verified=500, canonical_seed_weights={'X': 256, 'Z': 262},
                  group_orbits_verified=True, girths=girths,
                  lower_bound_from_completed_audit=30, physical_Z_witness_weight=30,
                  physical_X_witness_weight=122,
                  lower_bound_search_rerun=False)
    (DATA / 'manuscript_checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
