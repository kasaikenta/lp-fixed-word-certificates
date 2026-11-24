# Auditing exact global distance 30

The lower bound excludes every nontrivial logical operator of weight at most 29 in both CSS sectors. A separate physical logical operator of weight 30 supplies the matching upper bound. Checking matrices and a witness alone does not establish the lower bound.

## Reproduce the saved-record audit

```sh
python3 verification/download_receipts.py --id p25_m20_r4
python3 verification/audit_distance.py --id p25_m20_r4
python3 verification/download_receipts.py --id Mitten-975_p22_r3_v0
python3 verification/audit_distance.py --id Mitten-975_p22_r3_v0
```

Use Python 3.10 or later on macOS or Linux (the saved-record auditors use POSIX file locks). The archived Linux engine binaries are hashed, not executed, by these commands. The downloads are hash pinned in `data/receipt_archives.json`. Extracted records stay under `receipts/`; generated reports go to `verification_results/`. Allow sufficient memory, disk space and time for SQLite decompression and receipt verification.

The auditors reconstruct the physical code and sector partitions, verify the configuration and native engine source identities, inspect saved execution receipts, and check exhaustive nested partition coverage for X-anchor, X-stripe, Z-anchor and Z-stripe. The anchor case treats a nonzero distinguished component; the stripe case covers its zero-component kernel quotient. Every terminal frontier must be accounted for. An unfinished task is not a lower-bound certificate.

This procedure audits the saved executions. It does not rerun the original exhaustive native distance search. Its conclusion is conditional on the audited native algorithm, its execution receipts and the documented computational model; it is not a proof-assistant checked theorem.

## Archive contents and derivation

The 1650-qubit asset is byte-identical to the previously released cutoff-29 archive. Its legacy auditor is retained separately because its record format differs.

The 2500-qubit asset is a cutoff-29 projection of the original campaign. It contains the binary check matrices, campaign configurations, the relevant task states, and all original attempt rows at that cutoff. SQLite containers are repacked and compressed, but the selected row values, including execution receipt blobs, are preserved exactly. Records for other cutoffs are omitted. `curation.json` and per-chunk metadata record the derivation and original chunk hashes; `SHA256.json` fixes the derived files. Complete source chunks remain in the research archive.

Expected counts are 281626 attempt rows for the 1650-qubit code and 272824 for the 2500-qubit code. These are computational execution records, not counts of distinct low-weight logical operators. The cutoff-30 campaign is not used to assert either lower bound.

## Upper bounds and sector statements

Both supports have weight 30, zero syndrome and a nontrivial logical class. The saved lower-bound audits and these physical witnesses establish global distance 30. The sector statements are dX=30 and 30<=dZ<=38 for the 1650-qubit code, and dZ=30 and 30<=dX<=122 for the 2500-qubit code. Canonical basis weights are separate invariants of the selected basis and are not substituted for distance.

`verification/curate_cutoff29.py` documents the lossless cutoff projection used to prepare the 2500-qubit archive. It accepts an original campaign export and a new derivation workspace; it is not needed for a public saved-record audit and launches no distance search.

For a bounded parallel replay of the 2500-qubit archive on macOS or Linux, use `python3 verification/audit_distance.py --id p25_m20_r4 --workers 8`. This passes each chunk through the same serial saved-record scanner, rejects duplicate exclusions and cutoff-29 witnesses across chunks, and then runs the same complete partition-coverage audit. The worker pool closes and joins when the replay finishes or raises an error. The legacy 1650-qubit archive uses the serial path.
