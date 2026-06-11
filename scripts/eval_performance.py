"""Golden-case eval for the performance / ROI engine (tools.performance).

Validates the analytical functions against the live auction DB and against
synthetic inputs. Run: `python -m scripts.eval_performance`
Exits non-zero if any case fails (use as a regression guard).

These assert on *ranges* and *invariants*, not exact figures, so they stay green
as the underlying data grows — while still catching methodology regressions
(e.g. the index breaking, confidence guardrails misfiring, or CAGR math drifting).
"""

from __future__ import annotations

import sys

from tools.performance import (
    build_price_index, compute_performance, segment_proxy_for_artist,
)

CASES: list[tuple[str, callable, str]] = []


def case(name: str):
    def deco(fn):
        CASES.append((name, fn, fn.__doc__ or ""))
        return fn
    return deco


# ── Synthetic: pure CAGR math ─────────────────────────────────────────
@case("cagr_math_doubling")
def _cagr_math():
    """A value doubling over 4 years => CAGR ~18.9%, total return ~100%."""
    idx = [{"year": 2020 + i, "n": 50, "median": m, "mean": m, "q1": int(m * 0.8), "q3": int(m * 1.2)}
           for i, m in enumerate([1000, 1189, 1414, 1682, 2000])]
    p = compute_performance(idx)
    assert p["ok"], p
    assert 18.0 <= p["cagr"] <= 20.0, f"cagr {p['cagr']}"
    assert 95 <= p["total_return"] <= 105, f"total {p['total_return']}"
    assert p["confidence"] == "high", p["confidence"]
    return f"CAGR={p['cagr']}% total={p['total_return']}% conf={p['confidence']}"


@case("thin_index_low_confidence")
def _thin():
    """An index with one lot/year must NOT earn high confidence."""
    idx = [{"year": y, "n": 1, "median": m, "mean": m, "q1": m, "q3": m}
           for y, m in [(2021, 100000), (2023, 400000), (2026, 31000)]]
    p = compute_performance(idx)
    assert p["confidence"] in ("low", "none"), p["confidence"]
    return f"conf={p['confidence']}"


# ── Live DB: segment index is robust ──────────────────────────────────
@case("estonian_oil_segment")
def _ee_oil():
    """Estonian oil paintings: smooth high-confidence index, sane CAGR."""
    idx = build_price_index(country="EE", medium="oil")
    assert len(idx) >= 10, f"only {len(idx)} years"
    p = compute_performance(idx)
    assert p["ok"] and p["confidence"] == "high", p
    assert -5 <= p["cagr"] <= 20, f"implausible cagr {p['cagr']}"
    assert p["n_total"] >= 1000, f"n_total {p['n_total']}"
    return f"years={len(idx)} cagr={p['cagr']}% n={p['n_total']} conf={p['confidence']}"


@case("estonian_classical_oil")
def _ee_classical():
    """Estonian classical (<=1945) oils: still enough data for confidence."""
    idx = build_price_index(country="EE", medium="oil", period="classical")
    p = compute_performance(idx)
    assert p["ok"], p
    assert p["confidence"] in ("high", "medium"), p["confidence"]
    assert p["n_total"] >= 100, p["n_total"]
    return f"cagr={p['cagr']}% n={p['n_total']} conf={p['confidence']}"


# ── Live DB: thin artist falls back to a reliable segment proxy ────────
@case("magi_artist_thin_with_proxy")
def _magi():
    """Konrad Mägi: artist index is thin (not high confidence); proxy is reliable."""
    idx = build_price_index(author="Mägi")
    ap = compute_performance(idx)
    assert ap["confidence"] != "high", f"artist unexpectedly high conf: {ap}"
    proxy = segment_proxy_for_artist("Konrad Mägi")
    assert proxy is not None, "no proxy returned"
    pp = proxy["performance"]
    assert pp.get("ok"), f"proxy not ok: {pp}"
    assert pp["confidence"] in ("high", "medium"), pp["confidence"]
    return f"artist_conf={ap['confidence']} proxy='{proxy['label']}' proxy_conf={pp['confidence']}"


def main() -> int:
    print(f"{'CASE':<34} {'RESULT':<8} DETAIL")
    print("-" * 90)
    failures = 0
    for name, fn, _doc in CASES:
        try:
            detail = fn()
            print(f"{name:<34} {'PASS':<8} {detail}")
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"{name:<34} {'FAIL':<8} {type(e).__name__}: {e}")
    print("-" * 90)
    total = len(CASES)
    print(f"{total - failures}/{total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
