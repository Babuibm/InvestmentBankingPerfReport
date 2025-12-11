import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.size": 14,
    "axes.titlesize": 16,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12
})

# 1. Define grouping: group name -> list of sub_product keys (must match subproduct_metrics keys)
group_map = {
    "Cash Equity": ["Cash Equity"],
    "Fixed Income": ["Bonds", "NCD", "Secured Notes"],
    "Repos": ["Repo", "ReverseRepo"],
    "Equity Derivatives": ["EqFutures", "EqOptions", "EqSwaps", "IndFutures", "IndOptions"],
    "Forex Spot & Derivatives": ["Forex-Spot", "FxForwards", "FxFutures", "FxOptions", "FxSwaps"],
    "Int Rate Derivatives": ["IntRateFRA", "IntRateOptions", "IntRateSwaps"],
    "Credit Derivatives": ["CDS", "TRS"],
}

# 2. Helper to parse "Number of deals" row values (handles numeric or formatted strings)
def parse_count(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return 0.0
    s = str(x).strip()
    if s == "" or s.upper() == "NA":
        return 0.0
    s = s.replace(",", "")  # in case of "1,234"
    return float(s)
def plot_deals_unconfirmed(subproduct_metrics: dict):

    if not subproduct_metrics:
        # Return an empty figure rather than crashing
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        ax.axis("off")
        return fig

    # 3. Get week columns from any sub-product dataframe
    sample_df = next(iter(subproduct_metrics.values()))
    week_cols = list(sample_df.columns)      # 4 weeks
    num_weeks = len(week_cols)

    group_names = list(group_map.keys())
    num_groups = len(group_names)

    # 4. Build matrix of counts: shape (num_groups, num_weeks)
    counts = np.zeros((num_groups, num_weeks))

    for gi, gname in enumerate(group_names):
        for sp in group_map[gname]:
            if sp not in subproduct_metrics:
                continue  # in case a sub-product has no data
            df_sp = subproduct_metrics[sp]
            row = df_sp.loc["Number of unconfirmed deals", week_cols]
            vals = row.apply(parse_count).values
            counts[gi, :] += vals

    # 5. Compute WoW % change for each group (based on aggregated counts)
    wow_pct = np.full((num_groups, num_weeks), np.nan)
    for gi in range(num_groups):
        for wi in range(1, num_weeks):  # weeks 1,2,3 vs previous
            prev = counts[gi, wi - 1]
            curr = counts[gi, wi]
            if prev > 0:
                wow_pct[gi, wi] = (curr - prev) / prev * 100.0
            else:
                wow_pct[gi, wi] = np.nan  # undefined if previous week was 0

    # 6. Plot grouped bar chart (4 bars per group)
    x = np.arange(num_groups)  # group positions
    bar_width = 0.18

    fig, ax = plt.subplots(figsize=(18, 14))

    for wi in range(num_weeks):
        # shift each week's bars around group center
        offset = (wi - (num_weeks - 1) / 2) * bar_width
        ax.bar(
            x + offset,
            counts[:, wi],
            bar_width,
            label=week_cols[wi]
        )

    # 7. Annotate WoW % above bars for weeks 2–4 (index 1..3)
    for gi in range(num_groups):
        for wi in range(1, num_weeks):
            pct = wow_pct[gi, wi]
            if np.isnan(pct):
                continue
            offset = (wi - (num_weeks - 1) / 2) * bar_width
            bar_x = x[gi] + offset
            bar_y = counts[gi, wi]
            ax.text(
                bar_x,
                bar_y,
                f"{pct:.1f}%",
                ha="center",
                va="bottom",
                fontsize=8
            )

    ax.set_xlabel("Product Group")
    ax.set_ylabel("Number of Unconfirmed Deals")
    ax.set_title("Weekly volume of unconfirmed deals by Product Group (Last 4 Weeks)")
    ax.set_xticks(x, group_names, rotation=15)
    ax.legend(title="Week")
    ax.grid(True, axis="y")

    fig.tight_layout()
    return fig
