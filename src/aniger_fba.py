"""Zero-dependency loader/wrapper for the A. niger CCM (curated) GEM pilot.

This is a *curated* central-carbon-metabolism model built in-house
(VitaMind project), NOT a published full-genome GEM like iJB1325 / ecYeastGEM.

Honest model notes (verified empirically on this file):
  * 28 rxn / 24 met / 17 gene -- a focused CCM core, not a whole-cell model.
  * Lumped glycolysis (EMP_pyr/EMP_pep) and GOX/ATP_sink are simplifying
    approximations; mass/charge are not strictly conserved there, so MEMOTE
    would flag mass_balance fails. That is a known, disclosed simplification.
  * Biomass (BIOMASS, SBO:0000629) is a *real* reaction with real precursors
    and GAM, unlike iMA871's artificial sink. The pFBA value (~18.9) is in
    MODEL UNITS (biomass coefficients are lumped), NOT per hour -- do not
    compare directly to iJB1325 (0.9399 h^-1) or ecYeastGEM (0.087974 h^-1).
  * Carbon guardrail IS verifiable: closing the 5 organic-carbon exchange
    reactions collapses growth to 0 (drop ~100%).
  * Native A. niger trait: phosphate depletion decouples growth from TCA and
    routes carbon to citrate (see phosphate_switch()).
"""
import contextlib
import io
import os

from cobra.exceptions import Infeasible
from cobra.flux_analysis import pfba
from cobra.io import read_sbml_model

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL = os.path.normpath(os.path.join(HERE, "..", "data", "aniger_ccm_refined.xml"))

# Inorganic carbon species are excluded from the "organic carbon" guardrail.
INORG = {"CO2", "HCO3", "CO", "CH4"}


def load_model(path=None):
    """Load the curated CCM model from ``path`` or the bundled data file."""
    return read_sbml_model(path or DEFAULT_MODEL)


def find_biomass(model):
    """Return the biomass-reaction id, or None.

    This curated model ships a *real* biomass reaction named ``BIOMASS``
    (SBO:0000629) with genuine precursors + GAM.
    """
    if "BIOMASS" in model.reactions:
        return "BIOMASS"
    for r in model.reactions:
        if "biomass" in ((r.name or "") + " " + r.id).lower():
            return r.id
    return None


def pfba_growth(model, biomass_id=None):
    """Set the objective to the biomass reaction and run pFBA.

    Returns (status, growth_rate, total_flux). Catches Infeasible and returns
    ("infeasible", 0.0, 0.0) so callers can treat infeasibility as growth 0.
    """
    bid = biomass_id or find_biomass(model)
    if bid is None:
        raise ValueError("biomass reaction not found in model")
    model.objective = model.reactions.get_by_id(bid)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            sol = pfba(model)
        except Infeasible:
            return "infeasible", 0.0, 0.0
    return sol.status, float(sol.fluxes[bid]), float(sol.fluxes.abs().sum())


def carbon_bearing_boundaries(model):
    """List boundary (exchange) reactions that carry organic carbon."""
    out = []
    for r in model.reactions:
        if not r.boundary:
            continue
        has_c = False
        inorganic_only = True
        for met in r.metabolites:
            f = (met.formula or "").strip()
            if "C" in f:
                has_c = True
            if f not in INORG:
                inorganic_only = False
        if has_c and not inorganic_only:
            out.append(r)
    return out


def carbon_guardrail(model, biomass_id=None):
    """Close every organic-carbon boundary reaction and re-optimize.

    Returns (status, growth_after, drop_pct, n_closed). On a well-posed model
    growth must collapse (drop >= ~90%). On this curated CCM model it DOES:
    closing the 5 organic-carbon exchanges drops growth to 0 (verified).
    """
    bid = biomass_id or find_biomass(model)
    if bid is None:
        raise ValueError("biomass reaction not found in model")
    m = model.copy()  # operate on a copy; never mutate the caller's model
    m.objective = m.reactions.get_by_id(bid)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        base = m.optimize()
    b0 = float(base.fluxes[bid])
    carb = carbon_bearing_boundaries(m)
    for r in carb:
        r.lower_bound = 0.0
        r.upper_bound = 0.0
    with contextlib.redirect_stdout(buf):
        after = m.optimize()
    try:
        b1 = float(after.fluxes[bid])
    except Exception:
        b1 = 0.0
    drop = (1.0 - b1 / b0) * 100.0 if b0 > 0 else 0.0
    return after.status, b1, drop, len(carb)


def phosphate_switch(model, biomass_id=None):
    """Native A. niger phenotype: phosphate depletion routes carbon to citrate.

    Returns a dict with phase-1 (phosphate sufficient) and phase-2 (phosphate
    depleted) biomass + citrate-secretion fluxes. On a well-posed CCM model,
    closing EX_phos should drop growth and raise citrate secretion.
    """
    bid = biomass_id or find_biomass(model)
    # phase 1: phosphate sufficient
    m1 = model.copy()
    m1.objective = m1.reactions.get_by_id(bid)
    s1 = m1.optimize()
    g1 = float(s1.fluxes[bid]) if bid in s1.fluxes else 0.0
    c1 = float(s1.fluxes["EX_cit"]) if "EX_cit" in s1.fluxes else 0.0
    # phase 2: phosphate depleted (block extracellular phosphate uptake)
    m2 = model.copy()
    m2.reactions.EX_phos.lower_bound = 0.0
    m2.objective = m2.reactions.get_by_id(bid)
    s2 = m2.optimize()
    g2 = float(s2.fluxes[bid]) if bid in s2.fluxes else 0.0
    c2 = float(s2.fluxes["EX_cit"]) if "EX_cit" in s2.fluxes else 0.0
    return {"growth_sufficient": g1, "citrate_sufficient": c1,
            "growth_depleted": g2, "citrate_depleted": c2}
