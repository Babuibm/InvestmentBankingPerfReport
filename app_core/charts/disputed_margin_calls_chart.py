import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------
# 1. Basic preparation
# ---------------------------

def pct_change_matrix(mat: pd.DataFrame) -> pd.DataFrame:
    # mat: index = margin types, columns = weeks in order
    res = mat.replace(0, np.nan).pct_change(axis=1) * 100.0
    res = res.replace([np.inf, -np.inf], np.nan)
    return res

def plot_disputed_margin_calls(df_margincalls: pd.DataFrame, last_n_weeks: int = 4):

    # ---------------------------
    # 0. Basic validation
    # ---------------------------
    if df_margincalls is None or df_margincalls.empty:
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        ax1.text(0.5, 0.5, "No margin call data", ha="center", va="center")
        ax1.axis("off")

        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.text(0.5, 0.5, "No margin call data", ha="center", va="center")
        ax2.axis("off")

        return fig1, fig2

    df = df_margincalls.copy()

    # Convert date string to datetime
    df["Call_date_dt"] = pd.to_datetime(df["Call_date"], format="%d-%b-%Y")

    # Define "disputed" calls - adjust list if needed
    disputed_states = ["Disputed"]  # e.g. ["Disputed", "Challenged"]
    df_dispute = df[df["Call_result"].isin(disputed_states)].copy()

    if df_dispute.empty:
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        ax1.text(0.5, 0.5, "No disputed margin calls", ha="center", va="center")
        ax1.axis("off")

        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.text(0.5, 0.5, "No disputed margin calls", ha="center", va="center")
        ax2.axis("off")

        return fig1, fig2

    # Create week period (week ending Sunday; change to W-MON if needed)
    df_dispute["week"] = df_dispute["Call_date_dt"].dt.to_period("W-SUN")

    # Keep last 4 weeks that actually have disputes
    weeks_all = sorted(df_dispute["week"].unique())

    if not weeks_all:
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        ax1.text(0.5, 0.5, "No disputed weeks", ha="center", va="center")
        ax1.axis("off")

        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.text(0.5, 0.5, "No disputed weeks", ha="center", va="center")
        ax2.axis("off")

        return fig1, fig2

    last_weeks = weeks_all[-4:]
    df_dispute = df_dispute[df_dispute["week"].isin(last_weeks)].copy()

    if df_dispute.empty:
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        ax1.text(0.5, 0.5, "No disputed calls in last weeks", ha="center", va="center")
        ax1.axis("off")

        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.text(0.5, 0.5, "No disputed calls in last weeks", ha="center", va="center")
        ax2.axis("off")

        return fig1, fig2

    week_labels = [str(w) for w in last_weeks]

    # ---------------------------
    # 2. Aggregations: counts and amounts by Margin_type x week
    # ---------------------------

    # Counts
    counts = (
        df_dispute
        .groupby(["Margin_type", "week"])
        .size()
        .unstack("week", fill_value=0)
        .reindex(columns=last_weeks, fill_value=0)
    )

    # Amounts
    amounts = (
        df_dispute
        .groupby(["Margin_type", "week"])["Call_amount"]
        .sum()
        .unstack("week", fill_value=0.0)
        .reindex(columns=last_weeks, fill_value=0.0)
    )
    amounts_mn = amounts / 1_000_000
    margin_types = list(counts.index)
    num_types = len(margin_types)
    num_weeks = len(last_weeks)

    # ---------------------------
    # 3. Helper: compute WoW % change per row (axis=1)
    # ---------------------------



    counts_pct = pct_change_matrix(counts)
    amounts_pct = pct_change_matrix(amounts)

    # ---------------------------
    # 4. Plot 1 - # disputes per week by margin type
    # ---------------------------

    x = np.arange(num_types)
    bar_width = 0.18

    fig_counts, ax_counts = plt.subplots(figsize=(14, 10))

    for j, week in enumerate(last_weeks):
        offset = (j - (num_weeks - 1) / 2) * bar_width
        ax_counts.bar(
            x + offset,
            counts.iloc[:, j].values,
            bar_width,
            label=week_labels[j]
        )

    # Annotate WoW % above weeks 2–4 (index 1..3)
    for i, mt in enumerate(margin_types):
        for j in range(1, num_weeks):
            pct = counts_pct.iloc[i, j]
            if pd.isna(pct):
                continue
            offset = (j - (num_weeks - 1) / 2) * bar_width
            bar_x = x[i] + offset
            bar_y = counts.iloc[i, j]
            ax_counts.text(
                bar_x,
                bar_y,
                f"{pct:.1f}%",
                ha="center",
                va="bottom",
                fontsize=8
            )

    ax_counts.set_xlabel("Margin type")
    ax_counts.set_ylabel("Number of disputed calls")
    ax_counts.set_title("Weekly # of Disputed Margin Calls by Margin Type (Last Weeks)")
    ax_counts.set_xticks(x)
    ax_counts.set_xticklabels(margin_types, rotation=15)
    ax_counts.legend(title="Week")
    ax_counts.grid(True, axis="y")
    fig_counts.tight_layout()

    # Second plot - by amount
    fig_amounts, ax_amounts = plt.subplots(figsize=(14, 10))

    for j, week in enumerate(last_weeks):
        offset = (j - (num_weeks - 1) / 2) * bar_width
        ax_amounts.bar(
            x + offset,
            amounts_mn.iloc[:, j].values,   # ✅ USD Mn values
            bar_width,
            label=week_labels[j]
        )

    # Annotate WoW % above weeks 2–4
    for i, mt in enumerate(margin_types):
        for j in range(1, num_weeks):
            pct = amounts_pct.iloc[i, j]
            if pd.isna(pct):
                continue
            offset = (j - (num_weeks - 1) / 2) * bar_width
            bar_x = x[i] + offset
            bar_y = amounts_mn.iloc[i, j]
            ax_amounts.text(
                bar_x,
                bar_y,
                f"{pct:.1f}%",
                ha="center",
                va="bottom",
                fontsize=8
            )

    ax_amounts.set_xlabel("Margin type")
    ax_amounts.set_ylabel("Disputed amount (USD Mn)")
    ax_amounts.set_title("Weekly Disputed Amount by Margin Type (Last Weeks)")
    ax_amounts.set_xticks(x)
    ax_amounts.set_xticklabels(margin_types, rotation=15)
    ax_amounts.legend(title="Week")
    ax_amounts.grid(True, axis="y")
    ax_amounts.ticklabel_format(style="plain", axis="y")  # no ×1e8
    fig_amounts.tight_layout()
    return fig_counts, fig_amounts
