# aniger-ccm-refined-pilot — *Aspergillus niger* (black Aspergillus) virtual microbe

Minimal, license-clean slice of the VitaMind virtual-microbe project. This is
the **official *A. niger* entry** in the series (see the series index at the
bottom for the current repo names). One **curated** central-carbon-metabolism
(CCM) model built in-house, plus a zero-dependency Python wrapper and a
fail-closed `verify.py`.

> **This replaces the paused `iMA871-aniger-pilot`.** iMA871 (BioModels) is a
> low-quality reference (gene=0, artificial biomass sink, carbon guardrail not
> verifiable). This curated CCM model is the honest, working *A. niger* pilot.

## What's in this repo

| Path | What |
|---|---|
| `data/aniger_ccm_refined.xml` | Curated *A. niger* CCM model (28 rxn / 24 met / **17 gene**), built in-house |
| `src/aniger_fba.py` | Zero-dependency loader: load / biomass-locate / pFBA / carbon guardrail / phosphate switch |
| `verify.py` | Fail-closed self-check (**7/7 hard checks PASS**) |
| `LICENSE` | MIT — covers `src/` **and** the model |
| `NOTICE.md` | Model provenance + known limitations (disclosed) |
| `requirements.txt` | `cobra>=0.31`, `numpy>=1.24` |

## Reproduce

```bash
pip install -r requirements.txt
python verify.py        # exit 0 = all 7 checks passed
```

Expected output (7 PASS):

```
[PASS] L1 license/notice files present
[PASS] L2 src/ has zero absolute paths
[PASS] L3 dimensions match curated CCM   (rxn=28 met=24 gene=17)
[PASS] L4 pFBA biomass(BIOMASS) reproducible  (growth=18.947368)
[PASS] L5 carbon guardrail collapses growth (verifiable)  (drop 100.00%)
[PASS] L6 organism is A. niger and growth is NOT per-hour
[PASS] L7 phosphate switch: growth collapses, citrate rises  (citrate 6.0000->12.0000)
RESULT: 7/7 hard checks PASSED. Exit 0.
```

## The phosphate-switch phenotype (L7)

Closing `EX_phos` is what an industrial citric-acid strain actually experiences
in phase 2, and this curated model reproduces the qualitative switch:

| Phase | Growth | Citrate secretion capacity |
|---|---|---|
| phosphate sufficient | 18.95 | 6.00 |
| phosphate depleted (`EX_phos` closed) | 0.00 | **12.00** (2x) |

**One measured trap worth knowing.** You cannot read citrate overflow off a
biomass-maximising FBA solution: with biomass as the sole objective the LP
returns a carbon-minimal knife-edge solution and `EX_cit` is exactly `0.0000`
in *both* phases — a false negative that hides the phenotype completely. Citrate
overflow is an *alternative* objective, so each phase is solved as "keep growth
>= 50% of the phase-1 maximum, then maximise `EX_cit`". An earlier version of
`src/aniger_fba.py` got this wrong and reported citrate 0.0 -> 0.0.

## Why L6 exists

L6 asserts the organism identity and the growth unit **independently of any
numeric check**. It was added after the `iJB1325` release: every dimension and
growth number matched published values exactly, and the carbon guardrail
passed — while the published organism label was wrong. Green metrics hid a
wrong identity. Identity assertions must never ride on the metric checks.

## Honest interpretation — what this model is and isn't

| Property | iMA871 (paused) | this curated CCM |
|---|---|---|
| Gene layer | **0** (none) | **17** (real GPR) |
| Biomass reaction | artificial `added_biomass_sink` | real `BIOMASS` (SBO:0000629, precursors+GAM) |
| Carbon guardrail | **NOT verifiable** (drop ~0%) | **verifiable** (drop 100%) |
| Scope | 1400 rxn (empty shell) | 28 rxn (focused, validated core) |
| Growth value | 27.79 (model units) | 18.95 (model units) |

**Known limitations (disclosed, see `NOTICE.md`):**
1. Curated CCM core, not a whole-cell model.
2. Lumped glycolysis / GOX / ATP_sink are simplifying approximations
   (mass/charge not strictly conserved → MEMOTE `mass_balance` would flag).
3. pFBA growth ~18.95 is in **model units**, not per hour — not comparable to
   the h⁻¹ rates of iJB1325 / ecYeastGEM.
4. **Solid parts:** real biomass, verifiable carbon guardrail, genuine GPR,
   and the native *A. niger* phosphate-switch citrate phenotype.

## License

MIT — covers both `src/` and `data/aniger_ccm_refined.xml` (in-house model,
no third-party GEM license). See `LICENSE` + `NOTICE.md`.

## Series index

| Pilot | Organism | Model | Growth (if comparable) | Repo |
|---|---|---|---|---|
| 1 | *Aspergillus niger* | iJB1325 / ATCC 1015 (BiGG) | 0.9399 h⁻¹ | `field-claw/ijb1325-aniger-pilot` |
| 2 | *S. cerevisiae* | ecYeastGEM (BiGG, GECKO) | 0.087974 h⁻¹ | `field-claw/ecYeastGEM-yeast-pilot` |
| 3 | *A. niger* | aniger_ccm_refined (curated, in-house) | 18.95 (model units, **not** h⁻¹) | this repo |

> Note: entry 1 was originally published as `ijb1325-ecoli-pilot`. Verifying the
> model's own annotations (A. niger x606 vs Escherichia x4) proved iJB1325 is the
> *A. niger* ATCC 1015 genome-scale model, so the repo was renamed. Same class of
> error L6 now guards against.

Series hub: `field-claw/vitamind-virtual-microbe`.
