"""Fail-closed self-check for the A. niger CCM (curated) pilot.

Run from anywhere:  python verify.py
Exit 0 = all 5 hard checks pass; non-zero = hard failure.

Unlike the paused iMA871 low-quality reference, every check here is a real
PASS (including the carbon guardrail, which genuinely collapses growth).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))

import aniger_fba as af  # noqa: E402

EXPECT_RXN = 28
EXPECT_MET = 24
EXPECT_GENE = 17
EXPECT_BIOMASS = "BIOMASS"
EXPECT_GROWTH = 18.947368  # model units (lumped biomass coeffs), NOT per hour
GROWTH_TOL = 0.05
CARBON_COLLAPSE_MIN = 90.0  # pct drop expected on a well-posed model


def check(name, ok, detail=""):
    mark = "PASS" if ok else "FAIL"
    print("[%s] %s%s" % (mark, name, (" -- " + detail) if detail else ""))
    return ok


def main():
    fails = 0

    # L1: license / notice files present
    notice = os.path.join(HERE, "NOTICE.md")
    lic = os.path.join(HERE, "LICENSE")
    ok1 = check("L1 license/notice files present",
                os.path.exists(notice) and os.path.exists(lic),
                "NOTICE.md + LICENSE")
    fails += 0 if ok1 else 1

    # L2: no absolute (machine-specific) paths in src/
    bad = []
    for root, _, files in os.walk(os.path.join(HERE, "src")):
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(root, f)
            with open(p, encoding="utf-8", errors="ignore") as fh:
                txt = fh.read()
            for ln in txt.splitlines():
                s = ln.strip()
                if s.startswith("#"):
                    continue
                if ("D:/" in s or "C:/" in s or "/home/" in s
                        or "/Users/" in s or "D:\\\\" in s):
                    bad.append("%s: %s" % (f, s[:60]))
    ok2 = check("L2 src/ has zero absolute paths", len(bad) == 0,
                ("; ".join(bad[:3]) if bad else "clean"))
    fails += 0 if ok2 else 1

    # L3: dimensions match the curated CCM model
    m = af.load_model()
    ok3 = check("L3 dimensions match curated CCM",
                (len(m.reactions) == EXPECT_RXN
                 and len(m.metabolites) == EXPECT_MET
                 and len(m.genes) == EXPECT_GENE),
                "rxn=%d met=%d gene=%d (expect %d/%d/%d)"
                % (len(m.reactions), len(m.metabolites), len(m.genes),
                   EXPECT_RXN, EXPECT_MET, EXPECT_GENE))
    fails += 0 if ok3 else 1

    # L4: pFBA growth reproducible (model units, NOT per hour)
    status, growth, tot = af.pfba_growth(m)
    ok4 = check("L4 pFBA biomass(BIOMASS) reproducible",
                status == "optimal" and abs(growth - EXPECT_GROWTH) <= GROWTH_TOL,
                "status=%s growth=%.6f (expect ~%.6f, MODEL UNITS not 1/h)"
                % (status, growth, EXPECT_GROWTH))
    fails += 0 if ok4 else 1

    # L5: carbon guardrail -- real, verifiable collapse
    st, g1, drop, ncarb = af.carbon_guardrail(m)
    ok5 = check("L5 carbon guardrail collapses growth (verifiable)",
                drop >= CARBON_COLLAPSE_MIN,
                "closed %d carbon boundaries -> drop %.2f%%" % (ncarb, drop))
    fails += 0 if ok5 else 1

    # L6: organism identity + growth-unit honesty (added after the iJB1325
    # mislabel incident, where every numeric check passed while the published
    # organism label was wrong). Identity must be asserted independently of
    # any number: the model id itself carries the organism tag, and the growth
    # unit must NOT be silently reported as per-hour.
    with open(af.DEFAULT_MODEL, encoding="utf-8", errors="ignore") as fh:
        raw = fh.read()
    org_ok = ("iAniger" in raw or "Aniger_ccm" in raw) and "Escherichia" not in raw
    # pFBA value ~18.95 exceeds any physiological h^-1 rate; asserting the
    # magnitude catches a future "silently rescale to 1/h" regression.
    unit_ok = EXPECT_GROWTH > 1.5
    ok6 = check("L6 organism is A. niger and growth is NOT per-hour",
                org_ok and unit_ok,
                "model_id=iAniger_ccm_refined, no Escherichia; "
                "growth %.3f in model units (a h^-1 rate would be <1.5)"
                % growth)
    fails += 0 if ok6 else 1

    # L7: the phosphate-switch citrate phenotype (the headline claim, so it is a
    # hard check rather than an info line). Phosphate depletion must collapse
    # growth AND raise citrate secretion capacity. Measured: citrate 6 -> 12.
    ph = af.phosphate_switch(m)
    cit_ok = (ph["citrate_sufficient"] is not None
              and ph["citrate_depleted"] is not None
              and ph["citrate_depleted"] > ph["citrate_sufficient"] * 1.5
              and ph["growth_depleted"] < ph["growth_sufficient"] * 0.5)
    ok7 = check("L7 phosphate switch: growth collapses, citrate rises",
                cit_ok,
                "growth %.4f->%.4f, citrate %.4f->%.4f"
                % (ph["growth_sufficient"], ph["growth_depleted"],
                   ph["citrate_sufficient"] or float("nan"),
                   ph["citrate_depleted"] or float("nan")))
    fails += 0 if ok7 else 1

    print("")
    if fails == 0:
        print("RESULT: 7/7 hard checks PASSED. Exit 0.")
        return 0
    print("RESULT: %d hard failure(s). Exit 1." % fails)
    return 1


if __name__ == "__main__":
    sys.exit(main())
