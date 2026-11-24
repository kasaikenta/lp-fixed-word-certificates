# Paper, version 1

Paper DOI: https://doi.org/10.5281/zenodo.24505843

**Increasing Lifted-Product Code Distance by Reusing Fixed Constituent Expressions**  
Kenta Kasai, Institute of Science Tokyo

Manuscript date: November 24, 2026. GitHub paper release: November 25, 2026 (`paper-v1`).

- [Read the paper (PDF)](compact_lp_extensions.pdf)
- [English LaTeX source](source/)
- [Versioned release](https://github.com/kasaikenta/lp-fixed-word-certificates/releases/tag/paper-v1)
- [Project page](https://kasai.ict.eng.isct.ac.jp/lp-extensions-en.html)

The 11-page PDF contains the same text as the verified arXiv compilation, without the submission-preview stamp. This is a publicly released preprint. The GitHub release does not imply arXiv submission or journal acceptance.

## Rebuild

From `paper/source/`, run:

```sh
pdflatex -interaction=nonstopmode -halt-on-error compact_lp_extensions.tex
pdflatex -interaction=nonstopmode -halt-on-error compact_lp_extensions.tex
pdflatex -interaction=nonstopmode -halt-on-error compact_lp_extensions.tex
```

The release PDF was built with pdfLaTeX, TeX Live 2025. References are included in `references.tex`; no BibTeX run is required.

The accompanying code data and verification records remain those of the [v1.0.0 data release](https://github.com/kasaikenta/lp-fixed-word-certificates/releases/tag/v1.0.0). The paper cites that data release separately.

## License

The paper PDF and LaTeX sources are licensed under [CC BY 4.0](LICENSE.md).
