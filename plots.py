"""
Plotting module for Conjoint Simulator.
Handles visualization of analysis outputs.
"""

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib
matplotlib.use("Agg")
import pandas as pd
import numpy as np
from matplotlib.patches import Patch
import matplotlib.ticker as mticker
import textwrap

from shiny import ui
from ui_elements import (NONE_GREY, ACCENT_BLUE, TEMPLATE_ORANGE, TEMPLATE_BROWN,
                         TEMPLATE_GOLD, TEMPLATE_PURPLE, TEMPLATE_CREAM,
                         TEMPLATE_TEAL, TEMPLATE_LILAC, TEMPLATE_GREEN,
                         TEMPLATE_COLOURS, cmap)
from conjoint_model import (ATTRIBUTES, LEVELS, MIN_PRICE, MAX_PRICE, N_PRODUCTS)


def plot_level_utilities(
    level_utilities_df,
    figsize=(10, 5)
):
    """
    Create a horizontal bar chart of level utilities
    for a single selected attribute.

    Levels are shown in their original Excel order.
    """

    # ------------------------------------------------------------
    # Handle empty data
    # ------------------------------------------------------------

    if level_utilities_df.empty:
        fig, ax = plt.subplots(figsize=figsize)

        ax.text(
            0.5,
            0.5,
            "No utility data available",
            ha="center",
            va="center",
            fontsize=12,
        )

        ax.axis("off")

        return fig

    # ------------------------------------------------------------
    # Prepare data
    # ------------------------------------------------------------

    df = level_utilities_df.copy()

    df["Utility"] = pd.to_numeric(
        df["Utility"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["Utility"]
    ).reset_index(drop=True)

    if df.empty:
        fig, ax = plt.subplots(figsize=figsize)

        ax.text(
            0.5,
            0.5,
            "No utility data available",
            ha="center",
            va="center",
            fontsize=12,
        )

        ax.axis("off")

        return fig

    # ------------------------------------------------------------
    # Get selected attribute
    # ------------------------------------------------------------

    attribute = str(
        df["Attribute"].iloc[0]
    )

    # ------------------------------------------------------------
    # Dynamic figure height
    # ------------------------------------------------------------

    n_levels = len(df)

    chart_height = max(
        3.5,
        min(7, 1.0 + n_levels * 0.65)
    )

    fig, ax = plt.subplots(
        figsize=(figsize[0], chart_height),
        facecolor="white"
    )

    # ------------------------------------------------------------
    # Y positions
    # ------------------------------------------------------------

    y_pos = np.arange(n_levels)

    # ------------------------------------------------------------
    # Draw bars
    # ------------------------------------------------------------

    bars = ax.barh(
        y_pos,
        df["Utility"],
        color=TEMPLATE_ORANGE,
        alpha=0.9,
        edgecolor="black",
        linewidth=0.5,
        height=0.55,
    )

    # ------------------------------------------------------------
    # Zero reference line
    # ------------------------------------------------------------

    ax.axvline(
        0,
        color="#666666",
        linewidth=0.8,
        zorder=0,
    )

    # ------------------------------------------------------------
    # Level labels
    # ------------------------------------------------------------

    ax.set_yticks(y_pos)

    ax.set_yticklabels(
        df["Level"].astype(str),
        fontsize=9,
    )

    ax.tick_params(
        axis="y",
        length=0,
        pad=8,
    )

    # ------------------------------------------------------------
    # Calculate sensible x-axis limits
    # ------------------------------------------------------------

    utility_min = df["Utility"].min()
    utility_max = df["Utility"].max()

    max_abs_utility = max(
        abs(utility_min),
        abs(utility_max),
    )

    # Give both sides of zero some breathing room
    if max_abs_utility == 0:
        x_limit = 1
    else:
        x_limit = max_abs_utility * 1.20

    ax.set_xlim(
        -x_limit,
        x_limit,
    )

    # ------------------------------------------------------------
    # Add utility labels
    # ------------------------------------------------------------

    label_offset = x_limit * 0.025

    for bar, utility in zip(
        bars,
        df["Utility"]
    ):

        y = (
            bar.get_y()
            + bar.get_height() / 2
        )

        if utility >= 0:

            x = utility + label_offset
            ha = "left"

        else:

            x = utility - label_offset
            ha = "right"

        ax.text(
            x,
            y,
            f"{utility:.2f}",
            ha=ha,
            va="center",
            fontsize=9,
            fontweight="bold",
        )

    # ------------------------------------------------------------
    # Axis labels
    # ------------------------------------------------------------

    ax.set_xlabel(
        "Utility",
        fontsize=9,
    )

    ax.set_title(
        attribute,
        fontsize=11,
        fontweight="bold",
        loc="left",
        pad=12,
    )

    ax.tick_params(
        axis="x",
        labelsize=8,
    )

    # ------------------------------------------------------------
    # Remove unnecessary spines
    # ------------------------------------------------------------

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.spines["bottom"].set_color(
        "#BBBBBB"
    )

    # ------------------------------------------------------------
    # Keep first Excel level at the top
    # ------------------------------------------------------------

    ax.invert_yaxis()

    # ------------------------------------------------------------
    # Final spacing
    # ------------------------------------------------------------

    fig.subplots_adjust(
        left=0.28,
        right=0.96,
        top=0.84,
        bottom=0.14,
    )

    return fig


def plot_attribute_importances(
    attribute_importances_df,
    figsize=(10, 5)
):
    """
    Create a compact horizontal bar chart of attribute importances.

    Attributes are sorted from highest to lowest importance.
    """

    # ------------------------------------------------------------
    # Handle empty data
    # ------------------------------------------------------------

    if attribute_importances_df.empty:
        fig, ax = plt.subplots(figsize=figsize)

        ax.text(
            0.5,
            0.5,
            "No attribute importance data available",
            ha="center",
            va="center",
            fontsize=12,
        )

        ax.axis("off")

        return fig

    # ------------------------------------------------------------
    # Prepare data
    # ------------------------------------------------------------

    df = attribute_importances_df.copy()

    # Make sure the expected columns are numeric
    df["Importance"] = pd.to_numeric(
        df["Importance"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["Importance"]
    )

    # Highest importance first
    df = df.sort_values(
        "Importance",
        ascending=True
    ).reset_index(drop=True)

    # ------------------------------------------------------------
    # Create figure
    # ------------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=figsize,
        facecolor="white"
    )

    # ------------------------------------------------------------
    # Draw bars
    # ------------------------------------------------------------

    bars = ax.barh(
        df["Attribute"],
        df["Importance"],
        color=TEMPLATE_ORANGE,
        alpha=0.9,
        edgecolor="black",
        linewidth=0.5,
        height=0.65,
    )

    # ------------------------------------------------------------
    # Add percentage labels
    # ------------------------------------------------------------

    max_importance = df["Importance"].max()

    for bar, importance in zip(
        bars,
        df["Importance"]
    ):

        ax.text(
            importance + max_importance * 0.015,
            bar.get_y() + bar.get_height() / 2,
            f"{importance:.1f}%",
            ha="left",
            va="center",
            fontsize=9,
            fontweight="bold",
        )

    # ------------------------------------------------------------
    # Format axes
    # ------------------------------------------------------------

    ax.set_xlabel(
        "Attribute importance (%)",
        fontsize=9
    )

    ax.tick_params(
        axis="y",
        labelsize=9,
        length=0,
    )

    ax.tick_params(
        axis="x",
        labelsize=8,
    )

    # Give labels some room
    ax.set_xlim(
        0,
        max_importance * 1.15
    )

    # ------------------------------------------------------------
    # Remove unnecessary spines
    # ------------------------------------------------------------

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.spines["bottom"].set_color(
        "#BBBBBB"
    )

    # ------------------------------------------------------------
    # Final layout
    # ------------------------------------------------------------

    fig.subplots_adjust(
        left=0.20,
        right=0.97,
        top=0.96,
        bottom=0.12,
    )

    return fig


def plot_product_preference_shares(selected_shares, base_shares, figsize=(5, 8)):
    """
    Create a horizontal bar chart comparing selected product preference shares to base shares.
    """
    fig = plt.figure(figsize=figsize)
    ax = fig.subplots()

    all_product_ids = base_shares["ProductID"].values
    products = [f"Product {i}" if i != "NONE" else "NONE" for i in all_product_ids]

    base_shares_by_id = base_shares.set_index("ProductID")["PrefShare"].astype(float)
    selected_shares_by_id = selected_shares.set_index("ProductID")["PrefShare"].astype(float)

    selected_shares_aligned = selected_shares_by_id.reindex(
        all_product_ids,
        fill_value=0.0
    )
    base_shares_aligned = base_shares_by_id.reindex(
        all_product_ids,
        fill_value=0.0
    )

    bar_width = 0.08
    y_pos = np.arange(len(products)) * 0.2

    ax.barh(
        y_pos - bar_width / 3,
        selected_shares_aligned.values,
        bar_width,
        label="Selected Scenario",
        color=TEMPLATE_ORANGE,
        alpha=0.8,
        zorder=2
    )

    ax.barh(
        y_pos + bar_width / 4,
        base_shares_aligned.values,
        bar_width,
        label="Base Scenario",
        color=NONE_GREY,
        alpha=0.9,
        zorder=1
    )

    ax.set_yticks(y_pos, products)
    ax.set_xlabel("Preference Share (%)")
    fig.gca().invert_yaxis()

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.05),
        ncol=2,
        frameon=False
    )

    fig.tight_layout()

    for container in ax.containers:
        values = container.datavalues
        multiplier = 100 if max(values) <= 1.05 else 1
        labels = [
            f"{v * multiplier:.1f}%" if v > 0.001 else ""
            for v in values
        ]

        for container in ax.containers:
            values = container.datavalues
            multiplier = 100 if max(values) <= 1.05 else 1

            labels = [
                f"{v * multiplier:.1f}%" if v > 0.001 else ""
                for v in values
            ]

            ax.bar_label(
                container,
                labels=labels,
                label_type="edge",
                padding=-35,
                fontweight="bold",
                color="#333333",
                fontsize=9
            )

    return fig

def plot_pricing_results(pricing_results_df, selected_product, show_competitors=False, products_df=None, price_attr=None, currency_symbol="", currency_decimals=2, figsize=(16, 8), *args):
    """
    Create a dual-axis line plot showing Market Share and Relative Revenue.
    """
    # Safe fallback to standard layout to avoid Shiny warnings
    fig, ax1 = plt.subplots(figsize=figsize)

    fig.subplots_adjust(
        left=0.07,
        right=0.93,
        top=0.95,
        bottom=0.30
    )

    ax1.set_position([
        0.07,   # left
        0.35,   # bottom
        0.86,   # width
        0.60    # height
    ])
    
    # Create a second Y-axis for Revenue
    ax2 = ax1.twinx()
    
    p_col = str(selected_product)
    share_cols = [
    c for c in pricing_results_df.columns
    if c not in ["Price point", "Revenue"]
]

    # Current price of the selected product
    current_price = products_df.loc[
        products_df["ProductID"] == selected_product,
        price_attr
    ].iloc[0]
    
    # Calculate Revenue (Share * Price) for the target product
    pricing_results_df["Revenue"] = pricing_results_df[p_col] * pricing_results_df["Price point"]
    
    # Find the Revenue-Maximizing Price
    max_rev_idx = pricing_results_df["Revenue"].idxmax()
    optimal_price = pricing_results_df.loc[max_rev_idx, "Price point"]
    optimal_rev = pricing_results_df.loc[max_rev_idx, "Revenue"]
    

    # --------------------------------------------------
    # Plot competitors when requested
    # --------------------------------------------------

    if show_competitors:

        # Colours for competitor products
        competitor_colors = [
            "#6C757D",
            "#9C27B0",
            "#FF9800",
            "#009688",
            "#795548",
        ]

        competitor_index = 0

        for c in share_cols:

            if c != p_col and c != "NONE":

                competitor_color = competitor_colors[
                    competitor_index % len(competitor_colors)
                ]

                ax1.plot(
                    pricing_results_df["Price point"],
                    pricing_results_df[c],
                    color=competitor_color,
                    alpha=0.75,
                    linewidth=2.5,
                    linestyle="-",
                    label=f"Product {c} - Preference Share"
                )

                competitor_index += 1
            
    # 2. Plot Target Product Share (Bold Blue)
    line1 = ax1.plot(pricing_results_df["Price point"], pricing_results_df[p_col], 
                     color="#3C0F03", linewidth=4, 
                     label=f"Product {selected_product} – Preference Share")
             
    # 3. Plot Target Product Revenue (Bold Green Dotted)
    line2 = ax2.plot(pricing_results_df["Price point"], pricing_results_df["Revenue"], 
                     color = TEMPLATE_ORANGE, linewidth=4, linestyle=":", label="Revenue")
    # --------------------------------------------------
    # Highlight current selected-product price
    # --------------------------------------------------


    
    current_share = np.interp(
        current_price,
        pricing_results_df["Price point"],
        pricing_results_df[p_col]
    )

    ax1.scatter(
        [current_price],
        [current_share],
        color="#6C757D",
        marker="s",
        s=70,
        zorder=5,
        label="Current price"
    )
   
             
    # 4. Highlight Optimal Price Point
    ax2.axvline(optimal_price, color=TEMPLATE_ORANGE, linestyle="--", alpha=0.4)
    ax2.scatter([optimal_price], [optimal_rev], color= TEMPLATE_ORANGE, s=150, zorder=5)
    
    

    bbox_props = dict(
        boxstyle="round,pad=0.6",
        fc="#EEC881",
        ec="none",
        alpha=0.15
    )

    ax2.annotate(
        f"Revenue Maximising Price:\n"
        f"{currency_symbol}{optimal_price:,.{currency_decimals}f}",
        xy=(optimal_price, optimal_rev), 
        xytext=(0, 25), 
        textcoords="offset points", 
        ha="center", 
        fontweight="bold",
        fontsize=11,
        color=TEMPLATE_ORANGE,
        bbox=bbox_props
    )
    
    # Clean up formatting
    ax1.set_xlabel(
    price_attr,
    fontweight="bold",
    fontsize=12,
    labelpad=10
    )

    ax1.xaxis.set_major_formatter(
        mticker.StrMethodFormatter("{x:,.2f}")
    )
    ax1.set_ylabel("Preference Share", color="#3C0F03", fontweight="bold", fontsize=12)
    ax2.set_ylabel("Revenue Trajectory", color=TEMPLATE_ORANGE, fontweight="bold", fontsize=12)
    
    # Format Y axes (PercentFormatter with 1.0 means it turns 0.205 into 20.5%)
    ax1.yaxis.set_major_formatter(mticker.PercentFormatter(1.0)) 

    # Determine the maximum share across all visible products
    # Determine the maximum share across all products
    visible_share_cols = [
        c for c in share_cols
        if c != "NONE"
    ]

    max_share = pricing_results_df[
        visible_share_cols
    ].max().max()

    share_upper = min(
        1.0,
        np.ceil(max_share * 1.1 / 0.1) * 0.1
    )

    share_upper = max(share_upper, 0.2)

    ax1.set_ylim(0, share_upper)

    share_upper = min(
        1.0,
        np.ceil(max_share * 1.1 / 0.1) * 0.1
    )

    # Ensure there's enough room for the chart
    share_upper = max(share_upper, 0.2)

    ax1.set_ylim(0, share_upper)
    
    # Color coordinate the ticks so it's obvious which axis is which
    ax1.tick_params(axis='y', colors="#3C0F03")
    ax2.tick_params(axis='y', colors=TEMPLATE_ORANGE)
    
    # Remove messy borders and color the spines
    ax1.spines['top'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_color("#3C0F03")
    ax1.spines['left'].set_linewidth(2)
    ax2.spines['right'].set_color(TEMPLATE_ORANGE)
    ax2.spines['right'].set_linewidth(2)
    
    ax1.grid(axis="y", alpha=0.15, linestyle="--")

    # --------------------------------------------------
    # Build legend in Product ID order
    # --------------------------------------------------

    share_handles, share_labels = ax1.get_legend_handles_labels()
    revenue_handles, revenue_labels = ax2.get_legend_handles_labels()

    # Separate Product entries from Current price
    product_legend = [
        (handle, label)
        for handle, label in zip(share_handles, share_labels)
        if label.startswith("Product ")
    ]

    current_price_legend = [
        (handle, label)
        for handle, label in zip(share_handles, share_labels)
        if label == "Current price"
    ]

    # Sort products numerically
    product_legend = sorted(
        product_legend,
        key=lambda x: int(
            x[1].replace("Product ", "").split(" ")[0]
        )
    )

    # Combine handles and labels
    legend_handles = (
        [item[0] for item in product_legend]
        + [item[0] for item in current_price_legend]
        + revenue_handles
    )

    legend_labels = (
        [item[1] for item in product_legend]
        + [item[1] for item in current_price_legend]
        + revenue_labels
    )

    legend = ax1.legend(
        legend_handles,
        legend_labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.45),
        ncol=3,
        frameon=True,
        fontsize=10,
        title="Legend",
        title_fontsize=10
    )

    legend.get_frame().set_facecolor("#F8F9FA")
    legend.get_frame().set_edgecolor("#DEE2E6")
    legend.get_frame().set_linewidth(1)
    legend.get_frame().set_alpha(1)


    return fig