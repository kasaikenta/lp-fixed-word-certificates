# Increasing Lifted-Product Code Distance by Reusing Fixed Constituent Expressions

Paper DOI: https://doi.org/10.5281/zenodo.24505843

**Kenta Kasai · Institute of Science Tokyo**

[Read the paper (PDF)](https://github.com/kasaikenta/lp-fixed-word-certificates/releases/download/paper-v1/compact_lp_extensions.pdf) · [Paper release: paper-v1](https://github.com/kasaikenta/lp-fixed-word-certificates/releases/tag/paper-v1) · [LaTeX sources](paper/source/) · [Project page](https://kasai.ict.eng.isct.ac.jp/lp-extensions-en.html)

This paper reuses fixed constituent expressions of lifted-product codes while changing the finite evaluation group. It extends the [[975,195,24]] Mitten code to [[1650,330,30]] and [[2500,500,30]], at the same rate 1/5 and check-row weight nine. Both distances are certified exactly. The 2500-qubit example also retains the structure needed to generate a complete canonical logical basis using group actions.

The paper is released here as a preprint, with explicit code data and complete distance-verification records. [Paper details and build instructions](paper/README.md).

## Fixed-word lifted-product code distance certificates

This repository accompanies *Increasing Lifted-Product Code Distance by Reusing Fixed Constituent Expressions*. It specifies the codes as binary check matrices, ordered group words, parameters and physical logical witnesses, together with the software and execution records needed to audit the reported distances.

| Evaluation | n | k | d | Row weight | Column weights | Mitten defining invertibility |
|---|---:|---:|---:|---:|---|---|
| G(13,15,9), original | 975 | 195 | 24 | 9 | 3, 6 | retained |
| G(22,15,3) | 1650 | 330 | 30 | 9 | 3, 6 | fails (ranks 320/330) |
| G(25,20,4) | 2500 | 500 | 30 | 9 | 3, 6 | retained (ranks 500/500) |

The 1650-qubit code is an LP reevaluation of the Mitten constituent expressions, rather than a Mitten code satisfying the original invertibility definition. The 2500-qubit code retains that condition and has 500 complete canonical logical pairs generated from X/Z seeds of weights 256/262. Basis weights are not minimum distances.

## Lightweight reconstruction and logical verification

Python 3.10 or later, standard library only:

```sh
python3 generate_construction_table.py
python3 verify_selected.py
python3 verify_mitten_2500.py
```

These commands regenerate all three matrices, test CSS orthogonality, ranks, weights and physical logical witnesses, and check all canonical pairs of the 2500-qubit evaluation. They do not independently certify a distance lower bound from a summary JSON. For that, audit the complete records described in [AUDIT.md](AUDIT.md).

## Code data

- `evidence/selected/`: binary matrices, evaluated constituent data and group parameters for all three codes. Matrix JSON uses zero-based physical-qubit indices in each row of `hx` and `hz`.
- `evidence/mitten_1650_distance30/`: compact result, audited-status summary and physical witnesses.
- `evidence/mitten_2500_distance30/`: compact result, audit summary and physical witnesses.
- `generate_construction_table.py`: exact ordered expressions and reconstruction convention.
- `verification/` and `vendor/QEDist/`: source-bound receipt and partition-coverage auditors, with native source identity checks and retained license notices.

The complete lower-bound receipt archives are versioned [release assets](https://github.com/kasaikenta/lp-fixed-word-certificates/releases/tag/v1.0.0), to keep large binary evidence out of Git history. Asset identities and hashes are listed in `data/receipt_archives.json`.

## Scientific scope

The same formal words, every integer exponent and multiplication order are retained while the finite group changes. This is extra input beyond the parent binary matrices; equivalent words in the parent group can give different target evaluations. Both extensions have exact global distance 30: the 1650-qubit code has dX=30 and 30<=dZ<=38; the 2500-qubit code has dZ=30 and 30<=dX<=122. Global exactness requires both sector lower bounds and one matching physical witness.

The parent distance 24 is sourced from the QEDist catalogue, not newly proved by this repository. The extension results increase absolute distance with larger blocklength, while preserving rate 1/5 and check-row weight nine. They do not establish improved relative distance, decoding performance or circuit-level performance.

## References and provenance

- Bhardwaj et al., *High-rate qLDPC processors*, arXiv:2607.28795v2, Definition 4, Theorem 1, Appendix K/Table 13.
- Lee, *QEDist: Practical Exact Distance Certification for Stabilizer Codes*, arXiv:2611.21709v1, Section 3.6.
- The original and 1650-qubit matrices and earlier evidence were released in [lp-fixed-data-extensions v1.2.0](https://github.com/kasaikenta/lp-fixed-data-extensions/releases/tag/v1.2.0).

See [CONSTRUCTION.md](CONSTRUCTION.md), [AUDIT.md](AUDIT.md), and [NOTICE.md](NOTICE.md). Cite the v1.0.0 release to identify this fixed data version.

## Licenses

The [paper PDF and LaTeX sources](paper/) are licensed under [CC BY 4.0](paper/LICENSE.md). Original software and verification documentation retain the [MIT license](LICENSE); third-party notices remain in force.
