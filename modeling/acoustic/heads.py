#!/usr/bin/env python3
"""BAM classification heads: the honest, data-gated registry of what the
acoustic model is allowed to claim, plus a multiclass held-out eval that never
emits a metric without a documented split.

The slice already ships binary SRKW-call PRESENCE (eval_report.json). This
follow-on adds heads only where an openly-licensed, window-level annotated
corpus actually supports them. Each head carries:
  - the labelling scheme (windows.py) it trains on,
  - the corpus that supplies its labels and that corpus's license verdict (BSW-R02),
  - whether held-out eval can support a shipped claim,
  - its known confounds.

Anti-overclaim is enforced in code: a head with eval_supported=False (e.g.
single-vs-multiple, which BSW-R02 finds NO corpus provides true source-count
labels for) can be measured for diagnosis but is refused as a shipped claim by
`assert_shippable`. The HUD claim must never exceed what a supported head's
held-out eval measures.

numpy + scipy + scikit-learn only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.metrics import (
    precision_recall_fscore_support, confusion_matrix,
    average_precision_score, accuracy_score,
)
from sklearn.preprocessing import label_binarize

# License verdicts restated from BSW-R02 so a head cannot be wired to a
# STOP-to-O0 corpus by accident. Only OPEN may back a shipped claim without an
# explicit O0 NC authorization recorded in PROVENANCE.md.
LICENSE_OPEN = "OPEN"                  # CC-BY-4.0, ship freely with attribution
LICENSE_NC_AUTHORIZED = "NC-AUTHORIZED"  # CC-BY-NC-SA, O0/owner sign-off recorded
LICENSE_STOP = "STOP-to-O0"            # NC/ND/unclear, blocked until O0 clears


@dataclass
class Head:
    name: str
    scheme: str                        # windows.py labelling scheme
    classes: list[str]                 # closed label set the head reports
    label_corpus: list[str]            # corpora that can supply the labels
    license_status: str                # LICENSE_* of the backing corpus
    eval_supported: bool               # can a held-out eval honestly back a claim?
    hud_claimable: bool                # may this reach the served HUD wording?
    confounds: list[str] = field(default_factory=list)
    blocked_reason: str | None = None  # why eval_supported is False, if so
    notes: str | None = None


# The registry. presence already shipped; the rest are gated until BAM-DATA
# lands a license-cleared, window-level corpus and BAM-TRAIN measures them.
HEADS: dict[str, Head] = {
    "presence": Head(
        name="presence",
        scheme="presence",
        classes=["background", "present"],
        label_corpus=["orcasound_lab_bout (shipped v0)"],
        license_status=LICENSE_NC_AUTHORIZED,
        eval_supported=True,
        hud_claimable=True,
        confounds=[
            "v0 labels are bout-level weak labels on a single session; window-level "
            "corpus labels are the follow-on that removes this confound",
        ],
        notes="Already shipped as bam-srkw-presence-v0. Window-level corpus "
              "re-trains this head on true per-window labels.",
    ),
    "ecotype": Head(
        name="ecotype",
        scheme="ecotype",
        classes=["background", "SRKW", "NRKW", "TKW", "OKW", "SAR"],
        label_corpus=["DCLDE-2027 collated Annotations.csv"],
        license_status=LICENSE_OPEN,
        eval_supported=True,
        hud_claimable=True,
        confounds=[
            "collated CSV is ecotype-level, not pod (J/K/L) or individual ID",
            "class imbalance: SRKW vs other ecotypes varies by provider/location",
            "cross-station generalization must be measured by a station-grouped split",
        ],
        notes="DCLDE Ecotype field (SRKW / NRKW / TKW / OKW / SAR). Honest 'who' "
              "is coarse ecotype, never pod or individual.",
    ),
    "call_type": Head(
        name="call_type",
        # Coarse, acoustically-honest signal classes only. The fine S1-S40
        # catalog is NEVER a class here (charter forbids claiming it).
        scheme="call_type",
        classes=["pulsed_call", "whistle"],
        label_corpus=["DCLDE-2027 originals: VFPA Boundary Pass, SMRU Lime Kiln, SIMRES Tekteksen"],
        license_status=LICENSE_NC_AUTHORIZED,  # CC-BY-SA-4.0, ShareAlike carried
        eval_supported=False,
        hud_claimable=False,
        confounds=[
            "the populated call_type labels in the fetched originals ARE the SRKW "
            "S1-S40 stereotyped-call catalog (S01/S04/S44/...), which the charter "
            "forbids claiming; coarse signal_type labels (W/CK/BZ + 'whistle') are "
            "extremely sparse",
            "click/buzz coarse labels exist at ONE station (Lime Kiln) only, so a "
            "click class cannot be evaluated cross-station",
            "whistle coarse labels (~78) span only 2 stations; the 129-dim log-mel "
            "silhouette is a presence-oriented feature, weak for fine call morphology",
        ],
        blocked_reason=(
            "No honest, shippable call_type head for v1: the only well-populated "
            "labels are the S1-S40 catalog (forbidden to claim per charter), and "
            "the coarse signal classes are too sparse / single-station for an "
            "honest cross-station eval. Trained only as a marked DIAGNOSTIC "
            "(pulsed_call vs whistle); not wired to the HUD. to_strengthen: a "
            "scoped relabel budget or O0-costed torch embedding."
        ),
        notes="Diagnostic only. Coarse pulsed_call vs whistle; never an S1-S40 claim.",
    ),
    "single_vs_multiple": Head(
        name="single_vs_multiple",
        scheme="single_vs_multiple",
        classes=["background", "single", "multiple"],
        label_corpus=[],
        license_status=LICENSE_STOP,
        eval_supported=False,
        hud_claimable=False,
        confounds=[
            "BSW-R02: NO candidate corpus supplies verified source-count labels; "
            "all are call/segment detections or presence, not caller enumeration",
            "concurrent-annotation count is a proxy for label density, not a "
            "measured number of vocalizing animals",
        ],
        blocked_reason=(
            "No license-clear corpus provides true single-vs-multiple caller "
            "ground truth (BSW-R02). This head can be measured as a diagnostic "
            "but must not be shipped as a claim. Source-count is an O0 decision."
        ),
        notes="Kept in the registry so the gap is explicit, not silently dropped. "
              "Shipping it requires an O0-approved counting corpus or method.",
    ),
}


def assert_shippable(head_name: str) -> Head:
    """Guard the served contract: refuse to wire a head into classification.json
    unless it is eval-supported and HUD-claimable. Raises on overclaim."""
    head = HEADS[head_name]
    if not head.eval_supported or not head.hud_claimable:
        raise ValueError(
            f"head {head_name!r} is not shippable: {head.blocked_reason or 'not eval-supported'}"
        )
    if head.license_status == LICENSE_STOP:
        raise ValueError(
            f"head {head_name!r} is backed by a STOP-to-O0 corpus; clear license with O0 first"
        )
    return head


def multiclass_eval(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    proba: np.ndarray | None,
    classes: list[str],
    split_desc: str,
    groups_train: list[str] | None = None,
    groups_test: list[str] | None = None,
) -> dict:
    """Honest per-class + macro metrics with the split recorded inline. Refuses
    to produce numbers without a non-empty split description (enforces 'no metric
    without a split'). AUPRC is one-vs-rest macro when probabilities are given.

    groups_train / groups_test record which station-days were held out, so the
    report shows the cross-station / cross-day generalization the slice lacked.
    """
    if not split_desc or not split_desc.strip():
        raise ValueError("multiclass_eval requires a non-empty split_desc; no metric without a split")
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    p, r, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=classes, average=None, zero_division=0)
    per_class = {
        c: {"precision": round(float(p[i]), 4), "recall": round(float(r[i]), 4),
            "f1": round(float(f1[i]), 4), "support": int(support[i])}
        for i, c in enumerate(classes)
    }
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=classes, average="macro", zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=classes)

    auprc_macro = None
    if proba is not None and len(classes) > 1:
        present = [c for c in classes if c in set(y_true)]
        if len(present) >= 2:
            yb = label_binarize(y_true, classes=classes)
            if yb.shape[1] == 1:  # binary: label_binarize emits one column
                yb = np.hstack([1 - yb, yb])
            aps = []
            for i, c in enumerate(classes):
                if yb[:, i].sum() == 0:
                    continue
                aps.append(average_precision_score(yb[:, i], proba[:, i]))
            if aps:
                auprc_macro = round(float(np.mean(aps)), 4)

    return {
        "classes": classes,
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_precision": round(float(macro_p), 4),
        "macro_recall": round(float(macro_r), 4),
        "macro_f1": round(float(macro_f1), 4),
        "auprc_macro_ovr": auprc_macro,
        "per_class": per_class,
        "confusion": {"labels": classes, "matrix": cm.astype(int).tolist()},
        "split": {
            "description": split_desc,
            "train_groups": sorted(set(groups_train)) if groups_train else None,
            "test_groups": sorted(set(groups_test)) if groups_test else None,
            "n_train": len(groups_train) if groups_train else None,
            "n_test": len(groups_test) if groups_test else None,
        },
        "n_test_windows": int(len(y_true)),
    }


def _selftest() -> int:
    # Guard logic: presence + ecotype ship; call_type and single_vs_multiple are
    # refused as shipped claims (call_type only has S1-S40 / too-sparse coarse
    # labels; single_vs_multiple has no source-count labels).
    for name in ("presence", "ecotype"):
        h = assert_shippable(name)
        assert h.eval_supported and h.hud_claimable
    for name in ("call_type", "single_vs_multiple"):
        refused = False
        try:
            assert_shippable(name)
        except ValueError:
            refused = True
        assert refused, f"{name} must be refused as a shipped claim"

    # Eval requires a split description.
    yt = np.array(["background", "SRKW", "SRKW", "TKW"])
    yp = np.array(["background", "SRKW", "TKW", "TKW"])
    needs_split = False
    try:
        multiclass_eval(yt, yp, None, ["background", "SRKW", "TKW"], split_desc="")
    except ValueError:
        needs_split = True
    assert needs_split, "multiclass_eval must refuse an empty split_desc"

    rep = multiclass_eval(yt, yp, None, ["background", "SRKW", "TKW"],
                          split_desc="leave-station-out (synthetic)",
                          groups_train=["A", "A"], groups_test=["B", "B"])
    assert rep["macro_f1"] >= 0.0 and rep["n_test_windows"] == 4
    print("  shippable guard OK; single_vs_multiple refused; split enforced")
    print(f"  synthetic macro_f1={rep['macro_f1']} per_class_keys={list(rep['per_class'])}")
    print("heads.py self-test OK (synthetic, nothing written)")
    return 0


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    for n, h in HEADS.items():
        flag = "SHIP" if (h.eval_supported and h.hud_claimable) else "BLOCKED"
        print(f"{n:20s} [{flag:7s}] license={h.license_status:13s} classes={h.classes}")
