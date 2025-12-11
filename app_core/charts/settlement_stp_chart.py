import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, Dict, Any

# --- group_map unchanged ---
group_map = {
    "Cash Equity": ["Cash Equity"],
    "Fixed Income": ["Bonds", "NCD", "Secured Notes"],
    "Repos": ["Repo", "ReverseRepo"],
    "Equity Derivatives": ["EqFutures", "EqOptions", "EqSwaps", "IndFutures", "IndOptions"],
    "Forex Spot & Derivatives": ["Forex-Spot", "FxForwards", "FxFutures", "FxOptions", "FxSwaps"],
    "Int Rate Derivatives": ["IntRateFRA", "IntRateOptions", "IntRateSwaps"],
    "Credit Derivatives": ["CDS", "TRS"],
}

def plot_settlement_stp(subproduct_metrics: Dict[str, pd.DataFrame], deals_4w: Optional[pd.DataFrame] = None):
    """
    Robust wrapper for settlement STP chart.

    Parameters
    ----------
    subproduct_metrics : dict
        dict returned by run_analytics()['subproduct_metrics']
    deals_4w : pandas.DataFrame
        DataFrame returned by run_analytics()['deals_4w'] (expected). If None, the function
        will raise an informative error.

    Returns
    -------
    matplotlib.figure.Figure
    """

    # ---------- validate inputs early for clear logs ----------
    if not isinstance(subproduct_metrics, dict):
        raise TypeError(f"plot_settlement_stp: expected subproduct_metrics as dict, got {type(subproduct_metrics)!r}")

    if deals_4w is None:
        raise TypeError("plot_settlement_stp: deals_4w is required. Pass results['deals_4w'] from run_analytics().")

    if not isinstance(deals_4w, pd.DataFrame):
        raise TypeError(f"plot_settlement_stp: expected deals_4w as pandas.DataFrame, got {type(deals_4w)!r}")

    # ---------- same flow as before, using deals_4w ----------
    if not subproduct_metrics:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        ax.axis("off")
        return fig

    group_names = list(group_map.keys())

    # get ordered weeks from deals_4w
    if "week" not in deals_4w.columns:
        raise KeyError("plot_settlement_stp: 'week' column not found in deals_4w")

    week_periods = sorted(deals_4w["week"].dropna().unique())
    if len(week_periods) == 0:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No weeks available in deals_4w", ha="center", va="center")
        ax.axis("off")
        return fig

    num_weeks = len(week_periods)
    week_labels = [str(w) for w in week_periods]
    num_groups = len(group_names)

    # Matrix: Settlement STP % per group & week (float)
    settle_stp_pct = np.full((num_groups, num_weeks), np.nan, dtype=float)

    for gi, gname in enumerate(group_names):
        subps = group_map[gname]

        for wi, w in enumerate(week_periods):
            df_gw = deals_4w[
                (deals_4w["week"] == w) &
                (deals_4w["Product_subtype"].isin(subps))
            ]

            if df_gw.empty:
                continue

            df_valid = df_gw[
                df_gw["Settlement_type"].astype(str).str.strip().isin(["Cash", "Physical"])
            ]
            if df_valid.empty:
                continue

            total = len(df_valid)
            stp_yes = (
                df_valid["Settlement_stp"]
                .astype(str).str.strip().str.upper()
                .eq("Y")
                .sum()
            )

            if total > 0:
                settle_stp_pct[gi, wi] = (stp_yes / total) * 100.0

    # compute week-over-week percentage point changes (safe)
    settle_wow_pp = np.full((num_groups, num_weeks), np.nan, dtype=float)
    for gi in range(num_groups):
        for wi in range(1, num_weeks):
            prev = settle_stp_pct[gi, wi - 1]
            curr = settle_stp_pct[gi, wi]
            if np.isnan(prev) or np.isnan(curr):
                continue
            settle_wow_pp[gi, wi] = curr - prev

    # Plot
    x = np.arange(num_groups)
    bar_width = 0.18
    fig, ax = plt.subplots(figsize=(18, 7))

    for wi in range(num_weeks):
        offset = (wi - (num_weeks - 1) / 2) * bar_width
        # replace nan with 0 for plotting (so matplotlib doesn't error)
        vals = np.where(np.isnan(settle_stp_pct[:, wi]), 0.0, settle_stp_pct[:, wi])
        ax.bar(x + offset, vals, bar_width, label=week_labels[wi])

    ax.set_xlabel("Product Group")
    ax.set_ylabel("Settlement STP %")
    ax.set_title("Settlement STP % by Product Group (Last Weeks)")
    ax.set_xticks(x)
    ax.set_xticklabels(group_names, rotation=15)
    ax.legend(title="Week")
    ax.grid(True, axis="y")

    # safe y-limits: choose [0, max(105, observed_max*1.05)]
    observed_max = np.nanmax(settle_stp_pct)
    upper = 105 if np.isnan(observed_max) else max(105, observed_max * 1.05)
    ax.set_ylim(0, upper)

    fig.tight_layout()
    return fig

