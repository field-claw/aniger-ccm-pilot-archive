# aniger-ccm-refined-pilot — *Aspergillus niger* (black Aspergillus) virtual microbe

Minimal, license-clean slice of the VitaMind virtual-microbe project. This is
the **official *A. niger* entry** in the series (after `ijb1325-ecoli-pilot`
and `ecYeastGEM-yeast-pilot`). One **curated** central-carbon-metabolism (CCM)
model built in-house, plus a zero-dependency Python wrapper and a fail-closed
`verify.py`.

> **This replaces the paused `iMA871-aniger-pilot`.** iMA871 (BioModels) is a
> low-quality reference (gene=0, artificial biomass sink, carbon guardrail not
> verifiable). This curated CCM model is the honest, working *A. niger* pilot.

## What's in this repo

| Path | What |
|---|---|
| `data/aniger_ccm_refined.xml` | Curated *A. niger* CCM model (28 rxn / 24 met / **17 gene**), built in-house |
| `src/aniger_fba.py` | Zero-dependency loader: load / biomass-locate / pFBA / carbon guardrail / phosphate switch |
| `verify.py` | Fail-closed self-check (**5/5 hard checks PASS**) |
| `LICENSE` | MIT — covers `src/` **and** the model |
| `NOTICE.md` | Model provenance + known limitations (disclosed) |
| `requirements.txt` | `cobra>=0.31`, `numpy>=1.24` |

## Reproduce

```bash
pip install -r requirements.txt
python verify.py        # exit 0 = all 5 checks passed
```

Expected output (5 PASS):

```
[PASS] L1 license/notice files present
[PASS] L2 src/ has zero absolute paths
[PASS] L3 dimensions match curated CCM   (rxn=28 met=24 gene=17)
[PASS] L4 pFBA biomass(BIOMASS) reproducible  (growth=18.947368)
[PASS] L5 carbon guardrail collapses growth (verifiable)  (drop 100.00%)
   [info] phosphate switch: growth 18.94..->.., citrate ..->..
RESULT: 5/5 hard checks PASSED. Exit 0.
```

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
| 1 | *E. coli* | iJB1325 (BiGG) | 0.9399 h⁻¹ | `field-claw/ijb1325-ecoli-pilot` |
| 2 | *S. cerevisiae* | ecYeastGEM (BiGG, GECKO) | 0.087974 h⁻¹ | `field-claw/ecYeastGEM-yeast-pilot` |
| 3 | *A. niger* | aniger_ccm_refined (curated, in-house) | 18.95 (model units, **not** h⁻¹) | this repo |

Series hub: `field-claw/vitamind-virtual-microbe`.
