import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# same group mapping
group_map = {
    "Cash Equity": ["Cash Equity"],
    "Fixed Income": ["Bonds", "NCD", "Secured Notes"],
    "Repos": ["Repo", "ReverseRepo"],
    "Equity Derivatives": ["EqFutures", "EqOptions", "EqSwaps", "IndFutures", "IndOptions"],
    "Forex Spot & Derivatives": ["Forex-Spot", "FxForwards", "FxFutures", "FxOptions", "FxSwaps"],
    "Int Rate Derivatives": ["IntRateFRA", "IntRateOptions", "IntRateSwaps"],
    "Credit Derivatives": ["CDS", "TRS"],
}

def parse_count(x):
    if x is None:
        return 0.0
    s = str(x).strip().upper()
    if s == "" or s == "NA":
        return 0.0
    s = s.replace(",", "")
    return float(s)

def parse_pct_value(x):
    if x is None:
        return np.nan
    s = str(x).strip()
    if s == "" or s.upper() == "NA":
        return np.nan
    return float(s.replace("%", "").replace(",", ""))

def plot_trade_cap_stp(subproduct_metrics: dict):
    
    if not subproduct_metrics:
        # Return an empty figure rather than crashing
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        ax.axis("off")
        return fig

    sample_df = next(iter(subproduct_metrics.values()))
    week_cols = list(sample_df.columns)   # 4 weeks
    num_weeks = len(week_cols)

    group_names = list(group_map.keys())
    num_groups = len(group_names)

    # stp_pct_group[gi, wi] = Trade capture STP % for group gi, week wi
    stp_pct_group = np.full((num_groups, num_weeks), np.nan)

    for gi, gname in enumerate(group_names):
        for wi, week in enumerate(week_cols):
            num = 0.0   # numerator: sum(pct_sub * deals_sub)
            den = 0.0   # denominator: sum(deals_sub)
            for sp in group_map[gname]:
                if sp not in subproduct_metrics:
                    continue
                df_sp = subproduct_metrics[sp]
                deals = parse_count(df_sp.loc["Number of deals", week])
                pct   = parse_pct_value(df_sp.loc["Trade capture STP %", week])
                if deals <= 0 or np.isnan(pct):
                    continue
                num += pct * deals
                den += deals
            if den > 0:
                stp_pct_group[gi, wi] = num / den   # weighted avg 0..100

    x = np.arange(num_groups)
    bar_width = 0.18

    fig, ax = plt.subplots(figsize=(18, 7))

    # 4 bars per group: one per week
    for wi in range(num_weeks):
        offset = (wi - (num_weeks - 1) / 2) * bar_width
        ax.bar(
            x + offset,
            stp_pct_group[:, wi],
            bar_width,
            label=week_cols[wi]
        )

    ax.set_xlabel("Product Group")
    ax.set_ylabel("Trade Capture STP %")
    ax.set_title("Trade Capture STP % by Product Group (Last 4 Weeks)")
    ax.set_xticks(x, group_names, rotation=15)
    ax.legend(title="Week")
    ax.grid(True, axis="y")
    ax.ylim(70, 105)  # keep within 0–100%
    fig.tight_layout()
    return fig
