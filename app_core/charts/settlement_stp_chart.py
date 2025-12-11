import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- Same 7 product groups ---
group_map = {
    "Cash Equity": ["Cash Equity"],
    "Fixed Income": ["Bonds", "NCD", "Secured Notes"],
    "Repos": ["Repo", "ReverseRepo"],
    "Equity Derivatives": ["EqFutures", "EqOptions", "EqSwaps", "IndFutures", "IndOptions"],
    "Forex Spot & Derivatives": ["Forex-Spot", "FxForwards", "FxFutures", "FxOptions", "FxSwaps"],
    "Int Rate Derivatives": ["IntRateFRA", "IntRateOptions", "IntRateSwaps"],
    "Credit Derivatives": ["CDS", "TRS"],
}

def plot_settlement_stp(subproduct_metrics: dict):

    if not subproduct_metrics:
        # Return an empty figure rather than crashing
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        ax.axis("off")
        return fig

    group_names = list(group_map.keys())

    # --- Get ordered weeks from deals_4w ---
    week_periods = sorted(deals_4w["week"].unique())
    num_weeks = len(week_periods)
    week_labels = [str(w) for w in week_periods]
    num_groups = len(group_names)

    # --- Matrix: Settlement STP % per group & week ---
    settle_stp_pct = np.full((num_groups, num_weeks), np.nan)

    for gi, gname in enumerate(group_names):
        subps = group_map[gname]

        for wi, w in enumerate(week_periods):
            # filter deals for this group & week
            df_gw = deals_4w[
                (deals_4w["week"] == w) &
                (deals_4w["Product_subtype"].isin(subps))
            ]

            if df_gw.empty:
                continue

            # consider only real settlements (Cash or Physical)
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
                settle_stp_pct[gi, wi] = stp_yes / total * 100.0

      # ΔSettlement STP in percentage points vs previous week
    settle_wow_pp = np.full((num_groups, num_weeks), np.nan)

    for gi in range(num_groups):
        for wi in range(1, num_weeks):
            prev = settle_stp_pct[gi, wi - 1]
            curr = settle_stp_pct[gi, wi]
            if np.isnan(prev) or np.isnan(curr):
                continue
            settle_wow_pp[gi, wi] = curr - prev  # e.g. +1.2pp


    x = np.arange(num_groups)
    bar_width = 0.18

    fig, ax = plt.subplots(figsize=(18, 7))

    # 4 bars per group: one per week
    for wi in range(num_weeks):
        offset = (wi - (num_weeks - 1) / 2) * bar_width
        ax.bar(
            x + offset,
            settle_stp_pct[:, wi],
            bar_width,
            label=week_labels[wi]
        )

    ax.set_xlabel("Product Group")
    ax.set_ylabel("Settlement STP %")
    ax.set_title("Settlement STP % by Product Group (Last 4 Weeks)")
    ax.set_xticks(x, group_names, rotation=15)
    ax.legend(title="Week")
    ax.grid(True, axis="y")
    ax.ylim(70, 105)
    fig.tight_layout()
    return fig
