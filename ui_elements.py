from shiny import ui
from faicons import icon_svg

from matplotlib.colors import LinearSegmentedColormap

from conjoint_model import (
    make_id, 
    grid_df, 
    filters_df,
    BASECASE_DF, 
    PRICE_ATTR,
    PRICE_ATTRS,
    MAX_PRICE, 
    MIN_PRICE, 
    ATTRIBUTES, 
    LEVELS,
    FILTER_COLS
)


#### UI COLOURS
CANVAS_BG = "#F8F9FA"
TEXT_COLOUR = "#212529"
SIDEBAR_BG = "#FFFFFF"
CARD_BG = "#FFFFFF"
CARD_SHADOW = "0 4px 12px rgba(0,0,0,0.1)"
ACCENT_BLUE = "#0D6EFD"
NONE_GREY = "#E9ECEF"

# template theme colours
WHITE = "#FFFFFF"
BLACK = "#000000"
TEMPLATE_ORANGE = "#FF3C00"
TEMPLATE_BROWN = "#3C0F03"
TEMPLATE_GOLD = "#FFAA00"
TEMPLATE_PURPLE = "#5800BD"
TEMPLATE_CREAM = "#ECE7DA"
TEMPLATE_TEAL = "#63A07D"
TEMPLATE_GREEN = "#224329"
TEMPLATE_LILAC = "#DEBDED"

TEMPLATE_COLOURS = [TEMPLATE_ORANGE, TEMPLATE_BROWN, TEMPLATE_GOLD, TEMPLATE_PURPLE, TEMPLATE_CREAM, TEMPLATE_TEAL, TEMPLATE_LILAC, TEMPLATE_GREEN]
cmap = LinearSegmentedColormap.from_list("TEMPLATE_cmap", TEMPLATE_COLOURS)



#### SIMULATOR
def _numeric_price_value(value, currency_symbol=""):
    """Convert an Excel price value to a number."""
    clean_value = str(value)

    if currency_symbol:
        clean_value = clean_value.replace(
            currency_symbol, ""
        ).strip()

    return float(clean_value.replace(",", "").strip())


def _price_slider_step(attr):
    """Use sensible slider increments while allowing interpolated prices."""
    values = [
        _numeric_price_value(value)
        for value in grid_df[attr].dropna()
        if str(value).strip() != ""
    ]

    # Whole-number prices move in units of 1; decimal prices in units of 0.01.
    if all(value.is_integer() for value in values):
        return 1

    return 0.01

print("ATTRIBUTES:", ATTRIBUTES)
print("PRICE_ATTRS:", PRICE_ATTRS)

def create_product_card(product_no):

    card = ui.card(

        ui.card_header(
            ui.div(
                ui.row(
                    ui.column(
                        6,
                        ui.div(
                            f"Product {product_no}",
                            style="""
                                font-weight: 900;
                                font-size: 1.15rem;
                                white-space: nowrap;
                                text-align: left;
                            """
                        )
                    ),

                    ui.column(
                        6,
                        ui.input_checkbox(
                            f"product_{product_no}_include",
                            ui.HTML(
                                "<span style='color: white; font-weight: 600;'>Include</span>"
                            ),
                            value=True
                        ),
                        class_="text-end"
                    ),

                    class_="w-100 m-0 align-items-center"
                ),

                ui.row(
                    ui.column(
                        12,
                        ui.div(
                            ui.output_ui(
                                f"card_share_{product_no}",
                                inline=True
                            ),
                            style="""
                                text-align: center;
                                margin-top: 8px;
                                padding-top: 8px;
                                border-top: 1px solid rgba(255, 255, 255, 0.2);
                            """
                        )
                    ),
                    class_="w-100 m-0"
                ),

                style="""
                    display: flex;
                    flex-direction: column;
                    width: 100%;
                """
            ),

            style="""
                background-color: #3C0F03;
                color: white;
                padding: 12px 16px;
                border-bottom: none;
            """
        ),

        ui.card_body(
            *[
                ui.input_slider(
                    f"product_{product_no}_{make_id(attr)}",
                    attr,
                    min=min(
                        _numeric_price_value(value)
                        for value in grid_df[attr].dropna()
                        if str(value).strip() != ""
                    ),
                    max=max(
                        _numeric_price_value(value)
                        for value in grid_df[attr].dropna()
                        if str(value).strip() != ""
                    ),
                    value=_numeric_price_value(
                        BASECASE_DF.loc[product_no - 1, attr]
                    ),
                    step=_price_slider_step(attr)
                )
                if attr in PRICE_ATTRS
                else
                ui.input_selectize(
                    f"product_{product_no}_{make_id(attr)}",
                    attr,
                    choices=[
                        str(level).strip()
                        for level in grid_df[attr].dropna()
                        if str(level).strip() != ""
                        and str(level).strip().lower() != "nan"
                    ],
                    selected=str(BASECASE_DF.loc[product_no - 1, attr])
                )
                for attr in ATTRIBUTES
            ],
        ),

        full_screen=True,
    )

    return card




filters_ui = ui.card(
    ui.card_header("Filters"),
    ui.card_body(
        ui.input_switch("all_filters", "Deselect all", value=True),
        # Filters in accordion panels
        ui.accordion(
            *[ui.accordion_panel(
                # f"filter_panel_{make_id(c)}",
                c,
                ui.input_checkbox_group(
                    f"filter_{make_id(c)}",
                    "",
                    choices=sorted(filters_df[c].dropna().astype(str).unique()),
                    selected=sorted(filters_df[c].dropna().astype(str).unique())
                    )
                )
                for c in FILTER_COLS],
            open=False
            )
        ),
    )



#### SENSITIVITIES

#### SENSITIVITIES

# ==========================================================
# UI CARDS
# ==========================================================


# ----------------------------------------------------------
# ATTRIBUTE IMPORTANCES
# ----------------------------------------------------------

card_importances = ui.card(

    ui.card_header(

        ui.div(

            ui.span(
                "Attribute Importances",
                class_="importances-title"
            ),

            ui.div(

                ui.tags.button(
                    "Copy data to clipboard",
                    id="copy_importances",
                    class_="btn btn-sm btn-outline-secondary"
                ),

                ui.div(
                    ui.output_text(
                        "attribute_importances_clipboard_data"
                    ),
                    id="attribute_importances_clipboard_data",
                    style="""
                        position: absolute;
                        left: -9999px;
                        width: 1px;
                        height: 1px;
                        overflow: hidden;
                    """
                ),

                class_="importances-actions"
            ),

            class_="importances-header",
        )
    ),

    ui.card_body(

        # --------------------------------------------------
        # PRICE TOGGLE
        # --------------------------------------------------

        ui.div(

            ui.input_switch(
                "toggle_price",
                "Exclude 'Price'?",
                value=False
            ),

            style="""
                margin-bottom: 0;
                padding-bottom: 0;
            """
        ),

        # --------------------------------------------------
        # ATTRIBUTE IMPORTANCES EXPLAINER
        # --------------------------------------------------

        ui.div(

            ui.strong(
                "How to interpret attribute importance"
            ),

            ui.p(

                "Attribute importance shows the relative influence each attribute "
                "has on respondents' choices. Higher importance means that changes "
                "in that attribute have a greater impact on predicted preference. "
                "Importances are relative, so they should be interpreted by "
                "comparing attributes with one another rather than as absolute scores.",

                style="""
                    margin-top: 0;
                    margin-bottom: 0;
                """
            ),

            style="""
                padding: 15px 15px;
                margin-bottom: 10px;
                background-color: #f8f9fa;
                border-radius: 6px;
                font-size: 1.05rem;
            """
        ),

        # --------------------------------------------------
        # ATTRIBUTE IMPORTANCES CHART
        # --------------------------------------------------

        ui.output_plot(
            "attribute_importances_plot",
            height="400px"
        ),

        # --------------------------------------------------
        # ATTRIBUTE IMPORTANCES SUMMARY
        # --------------------------------------------------

        ui.output_ui(
            "attribute_importance_summary"
        ),


    ),

    full_screen=True,
)


# ----------------------------------------------------------
# LEVEL UTILITIES
# ----------------------------------------------------------

card_utilities = ui.card(

    ui.card_header(

        ui.div(

            ui.span(
                "Level Utilities",
                class_="utilities-title"
            ),

            ui.div(

                ui.tags.button(
                    "Copy data to clipboard",
                    id="copy_level_utilities",
                    class_="btn btn-sm btn-outline-secondary"
                ),

                ui.div(
                    ui.output_text(
                        "level_utilities_clipboard_data"
                    ),
                    id="level_utilities_clipboard_data",
                    style="""
                        position: absolute;
                        left: -9999px;
                        width: 1px;
                        height: 1px;
                        overflow: hidden;
                    """
                ),

                class_="utilities-actions"
            ),

            class_="utilities-header",
        )
    ),

    ui.card_body(

        # --------------------------------------------------
        # LEVEL UTILITIES EXPLAINER
        # --------------------------------------------------

        ui.div(

            ui.strong(
                "How to interpret level utilities"
            ),

            ui.p(

                "Level utilities show the relative preference associated "
                "with each level within an attribute. Higher utilities "
                "indicate greater preference, while lower utilities indicate "
                "lower preference. Utilities are best interpreted by "
                "comparing levels within the same attribute, rather than "
                "across different attributes.",

                style="""
                    margin-bottom: 0;
                """
            ),

            style="""
                padding: 12px 15px;
                margin-bottom: 15px;
                background-color: #f8f9fa;
                border-radius: 6px;
                font-size: 1rem;
            """
        ),

        # --------------------------------------------------
        # ATTRIBUTE DROPDOWN
        # --------------------------------------------------

        ui.output_ui(
            "level_utilities_attribute_selector"
        ),

        # --------------------------------------------------
        # LEVEL UTILITIES CHART
        # --------------------------------------------------

        ui.output_plot(
            "level_utilities_plot",
            height="400px"
        ),

        # --------------------------------------------------
        # LEVEL UTILITIES SUMMARY
        # --------------------------------------------------

        ui.output_ui(
            "level_utilities_summary"
        ),

    ),

    full_screen=True,
)

ui.card_body(

        # --------------------------------------------------
        # LEVEL UTILITIES EXPLAINER
        # --------------------------------------------------

        ui.div(
            ui.strong("How to interpret level utilities"),

            ui.p(
                "Level utilities show the relative preference associated "
                "with each level within an attribute. Higher utilities "
                "indicate greater preference, while lower utilities indicate "
                "lower preference. Utilities are best interpreted by "
                "comparing levels within the same attribute, rather than "
                "across different attributes.",
                style="margin-bottom: 0;"
            ),

            style="""
                padding: 12px 15px;
                margin-bottom: 15px;
                background-color: #f8f9fa;
                border-radius: 6px;
                font-size: 1rem;
            """
        ),

        # --------------------------------------------------
        # ATTRIBUTE DROPDOWN
        # --------------------------------------------------

        ui.output_ui(
            "level_utilities_attribute_selector"
        ),

        # --------------------------------------------------
        # LEVEL UTILITIES CHART
        # --------------------------------------------------

        ui.output_plot(
            "level_utilities_plot",
            height="400px"
        ),

        # --------------------------------------------------
        # LEVEL UTILITIES SUMMARY
        # --------------------------------------------------

        ui.output_ui(
            "level_utilities_summary"
        ),

    ),



#### PRICING

pricing_sidebar_ui = ui.sidebar(
    ui.card(
        ui.card_header("Configuration"),

        ui.card_body(
            ui.input_select(
                "pricing_attribute",
                "Select price attribute",
                choices=PRICE_ATTRS,
                selected=PRICE_ATTRS[0] if PRICE_ATTRS else None,
            ),

    ui.output_ui("pricing_product_selector"),

            ui.div(
                ui.output_ui("selected_product_pricing"),
                style="margin-top: 15px; margin-bottom: 15px;"
            ),

            ui.input_checkbox(
                "show_competitors",
                "Show competitors",
                value=False
            ),
        ),

        style="margin-top: 0 !important;"
    ),

    ui.hr(),

    ui.input_action_button(
        "run_pricing",
        "Run Pricing Analysis",
        class_="btn-pricing",
        icon=icon_svg("chart-line"),
        width="100%"
    ),

    position="right",
    width="clamp(220px, 21vw, 300px)",
    open="desktop",
    fillable=True,
    bg=SIDEBAR_BG,
    id="pricing_sidebar"
)

card_pricing = ui.card_body(

    ui.div(
        ui.strong("What pricing analysis shows"),
        ui.p(
            "Pricing analysis shows how changes in price affect predicted preference "
            "share and revenue. Use the analysis to identify the revenue-maximising "
            "price and understand the trade-off between charging more and maintaining "
            "demand. You can also show competitor preference shares to assess how "
            "demand shifts between products as price changes.",
            style="margin-bottom: 0;"
        ),
        style="""
            padding: 12px 15px;
            margin: 10px 15px 15px 15px;
            background-color: #f8f9fa;
            border-radius: 6px;
            font-size: 1.05rem;
        """
    ),

    # ----------------------------------------------
    # Copy Pricing results
    # ----------------------------------------------
    ui.div(

        ui.tags.button(
            "Copy data to clipboard",
            id="copy_pricing",
            class_="btn btn-sm btn-outline-secondary"
        ),

        ui.div(
            ui.output_text(
                "pricing_clipboard_data"
            ),
            id="pricing_clipboard_data",
            style="""
                position: absolute;
                left: -9999px;
                width: 1px;
                height: 1px;
                overflow: hidden;
            """
        ),

        style="text-align: right; margin-bottom: 10px;"
    ),

    ui.layout_columns(

    # --------------------------------------------------
    # Pricing chart
    # --------------------------------------------------
    ui.div(
        ui.output_plot(
            "pricing_plot",
            height="500px"
        ),
        style="width: 100%;"
    ),

    # --------------------------------------------------
    # Key insight
    # --------------------------------------------------
    ui.div(

        
        ui.output_ui(
            "pricing_summary"
        ),

        style="""
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 6px;
            border: 1px solid #dee2e6;
            height: 100%;
            font-size: 0.95rem;
        """
    ),
    col_widths=[9, 3],
    gap="1rem",
    style="""
        align-items: stretch;
        margin-top: -25px;
    """
    ),

    class_="p-0",
    style="min-height: 0; width: 100%; height: auto;"
),

pricing_clipboard_script = ui.tags.script("""
    document.addEventListener("click", function(event) {

        if (event.target && event.target.closest("#copy_pricing")) {

            const button = event.target.closest("#copy_pricing");

            // TEST: change button immediately
            button.innerText = "Copied!";

            setTimeout(function() {
                button.innerText = "Copy data to clipboard";
            }, 1500);

            const output = document.getElementById(
                "pricing_clipboard_data"
            );

            if (!output) {
                console.error("Pricing output not found.");
                return;
            }

            const text = output.innerText || output.textContent || "";

            console.log("Pricing text:", text);

            if (!text.trim()) {
                console.error("Pricing data is empty.");
                return;
            }

            navigator.clipboard.writeText(text)
                .then(function() {
                    console.log("Pricing data copied.");
                })
                .catch(function(error) {
                    console.error("Clipboard failed:", error);
                });
        }

    });
""")