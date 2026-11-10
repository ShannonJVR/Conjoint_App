import pandas as pd
import numpy as np
import matplotlib
from shiny.types import SilentException
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import math
import conjoint_model  
import traceback
from pathlib import Path
from plots import (
    plot_level_utilities,
    plot_attribute_importances,
    plot_product_preference_shares,
    plot_pricing_results
)
from ui_elements import *
from shiny import App, ui, reactive, render
from faicons import icon_svg
from conjoint_model import (
    make_id, clean_attr, apply_restrictions,
    grid_df, utils_df, attributes_df, filters_df,
    settings_df, default_df, restrictions_df,
    ATTRIBUTES, LEVELS, PRICE_ATTR, PRICE_ATTRS, FILTER_COLS,
    N_PRODUCTS, BASECASE_DF,
    run_pricing_analysis
)
from pathlib import Path

# --- AI SETUP (COMMENTED OUT FOR NOW) ---
# import os
# import certifi
# from openai import AsyncOpenAI
# os.environ["SSL_CERT_FILE"] = certifi.where()
# api_key = os.environ.get("OPENAI_API_KEY", "missing-key-prevent-crash")
# aclient = AsyncOpenAI(api_key=api_key)
# ----------------------------------------


# ======================================================
# APP UI
# ======================================================
custom_css = Path(__file__).parent / "shared" / "www" / "styles.css"

app_ui = ui.page_navbar(
    ui.head_content(
        ui.include_css(custom_css),
        pricing_clipboard_script,
        # 🌟 NEW: This safely forces the "Include" text to be white and bold!
        ui.tags.style("""
            .card-header .form-check-label {
                color: white !important;
                font-weight: bold !important;
            }
            
            

             /* ==============================================
                Profile Analysis - Balanced Column Spacing
                ============================================== */

                .profile-table-wrapper {
                    width: 100%;
                    overflow-x: auto;
                }

                .profile-analysis-table {
                    width: 100% !important;
                    min-width: 1100px;
                    table-layout: auto;
                }

                .profile-header {
                    display: flex;
                    align-items: center;
                    width: 100%;
                }

                .profile-actions {
                    margin-left: auto;
                }

                .profile-analysis-table th,
                .profile-analysis-table td {
                    padding: 9px 16px !important;
                    vertical-align: middle;
                }

                /* Profile and Group get enough room for longer labels */
                .profile-analysis-table th:first-child,
                .profile-analysis-table td:first-child {
                    min-width: 130px;
                }

                .profile-analysis-table th:nth-child(2),
                .profile-analysis-table td:nth-child(2) {
                    min-width: 180px;
                }

                /* Keep numerical columns consistent */
                .profile-analysis-table th:nth-child(n+3),
                .profile-analysis-table td:nth-child(n+3) {
                    min-width: 100px;
                    text-align: center;
                }
        """),

           

            ui.tags.style(f"""
                /* Icons */
                svg {{
                    color: {TEMPLATE_ORANGE} !important;
                }}

                .fa,
                .fas,
                .far,
                .fab,
                .fa-solid,
                .fa-regular,
                .fa-brands {{
                    color: {TEMPLATE_BROWN} !important;
                }}


                /* Purple wand icon override */
                .purple-wand-icon,
                .purple-wand-icon svg,
                .purple-wand-icon .fa,
                .purple-wand-icon .fa-solid {{
                    color: {TEMPLATE_PURPLE}  !important;
                }}

                /* Shiny checkboxes */
                .shiny-input-container input[type="checkbox"]:checked {{
                    background-color: {TEMPLATE_ORANGE} !important;
                    border-color: {TEMPLATE_ORANGE} !important;
                }}

                .shiny-input-container .form-check-input:checked {{
                    background-color: {TEMPLATE_BROWN} !important;
                    border-color: {TEMPLATE_BROWN} !important;
                }}

                                /* Top navigation bar */
                nav.navbar {{
                    background-color: {TEMPLATE_BROWN} !important;
                }}

                nav.navbar .navbar-brand,
                nav.navbar .navbar-brand *,
                nav.navbar .nav-link,
                nav.navbar .nav-link * {{
                    color: {WHITE} !important;
                }}

                nav.navbar .nav-link.active {{
                    color: {WHITE} !important;
                    border-bottom-color: {WHITE} !important;
                }}

                /* Navigation / page titles */
                nav.navbar .nav-link {{
                    font-family: Georgia, serif !important;
                }}

                /* Fonts */
                body {{
                    font-family: "Aptos", sans-serif !important;
                }}

                h1,
                h2,
                h3,
                h4,
                h5,
                h6 {{
                    font-family: Georgia, serif !important;
                }}

                /* Main page title */
                .navbar-brand {{
                    font-family: Georgia, serif !important;
                }}

                /* Card headers */
                .card-header {{
                    font-family: Georgia, serif !important;
                }}

                /* Sliders */
                .irs-bar,
                .irs-bar-edge,
                .irs-single,
                .irs-handle > i:first-child {{
                    background-color: {TEMPLATE_ORANGE} !important;
                }}

                .irs-single {{
                    color: {WHITE} !important;
                }}

                /* Sliders */
                .irs-bar,
                .irs-bar-edge,
                .irs-single {{
                    background-color: {TEMPLATE_ORANGE} !important;
                }}

                .irs-single {{
                    color: {WHITE} !important;
                }}

                /* Price slider circle */
                .irs-handle,
                .irs-handle i {{
                    background-color: {TEMPLATE_ORANGE} !important;
                    border-color: {TEMPLATE_ORANGE} !important;
                }}

                /* Progress bars */
                .progress-bar {{
                    background-color: {TEMPLATE_ORANGE} !important;
                }}

                /* Card headers */
                .card-header {{
                    background-color: {TEMPLATE_BROWN} !important;
                    color: {WHITE} !important;
                }}

                .card-header * {{
                    color: {WHITE} !important;
                }}

                

            """),

            ui.tags.style(
                f"""
                :root {{
                    --template-orange: {TEMPLATE_ORANGE};
                    --template-orange-faded: color-mix(
                        in srgb,
                        {TEMPLATE_ORANGE} 25%,
                        white
                    );
                }}
                """
            ),

            ui.tags.style("""
                #optimisation_sidebar .card {
                    margin-top: -16px;
                }
            """),

            

            ui.tags.style("""
                .optimisation-constraints-accordion {
                    margin-top: 5px;
                }

                .optimisation-constraints-accordion .accordion-button {
                    padding: 8px 10px;
                    font-size: 0.9rem;
                    font-weight: 600;
                }

                .optimisation-constraints-accordion .accordion-body {
                    padding: 10px;
                }

                .optimisation-constraints-accordion .form-check {
                    margin-bottom: 4px;
                }

                

                /* Optimised configuration header */

                .optimised-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 12px;
                    width: 100%;
                }



                /* --------------------------------------------------
                Optimised comparison table
                -------------------------------------------------- */

                .optimised-table-container {
                    width: 100%;
                    overflow-x: auto;
                }

                .optimised-comparison-table {
                    width: 100%;
                    table-layout: fixed;
                    border-collapse: separate;
                    border-spacing: 0;
                    font-size: 13px;
                    word-wrap: break-word;
                    overflow-wrap: anywhere;
                }

                .optimised-comparison-table th,
                .optimised-comparison-table td {
                    white-space: normal !important;
                    overflow-wrap: anywhere;
                    word-break: normal;
                    vertical-align: middle;
                    padding: 14px 12px;
                    line-height: 1.75;
                }


                .optimised-comparison-table thead th {
                    background-color: #F8F9FA;
                    color: #3C0F03;
                    font-weight: 700;
                    border-bottom: 2px solid #E9ECEF;
                }

                /* Column widths */

                .optimised-comparison-table th:nth-child(1),
                .optimised-comparison-table td:nth-child(1) {
                    width: 14%;
                }

                .optimised-comparison-table th:nth-child(2),
                .optimised-comparison-table td:nth-child(2) {
                    width: 22%;
                }

                .optimised-comparison-table th:nth-child(3),
                .optimised-comparison-table td:nth-child(3) {
                    width: 32%;
                }

                .optimised-comparison-table th:nth-child(4),
                .optimised-comparison-table td:nth-child(4) {
                    width: 32%;
                }

                .optimised-comparison-table
                .optimised-changed-row td {
                    background-color: var(--template-orange-faded) !important;
                }

                .optimised-comparison-table
                .optimised-changed-value {
                    color: #000000 !important;
                    font-weight: 600;
                }

                /* Shared brown card headers */

                .optim-box .card-header,
                .optimised-box .card-header {
                    background-color: #3C0F03 !important;
                    color: #FFFFFF !important;
                    padding: 12px 16px;
                }

                .optimised-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    width: 100%;
                }

                .optimised-header h5 {
                    color: #FFFFFF !important;
                    font-weight: 700;
                }

                /* Optimisation sidebar spacing */

                #optimisation_tab .sidebar .form-group,
                #optimisation_tab .sidebar .shiny-input-container {
                    margin-bottom: 14px;
                }

                #optimisation_tab .sidebar label {
                    font-weight: 600;
                    color: #495057;
                }

                #optimisation_tab .sidebar .form-check {
                    margin-bottom: 5px;
                }

                #optimisation_tab .sidebar hr {
                    opacity: 0.7;
                }

            """),

            ui.tags.style("""
                /* Pricing tab fills the available page height */
                #pricing_tab {
                    height: calc(100vh - 90px);
                }

                #pricing_tab .bslib-sidebar-layout {
                    height: 100%;
                }

                #pricing_tab .main {
                    height: 100%;
                    min-height: 0;
                }

                /* Allow pricing cards to use their natural height */
                #pricing_tab .card {
                    height: auto;
                }

                #pricing_tab .card-body {
                    height: auto;
                }


                /* Give the pricing plot room to expand */
                #pricing_tab .shiny-plot-output {
                    width: 100% !important;
                    min-height: 600px;
                }

                /* ==================================================
                ALIGN PRICING SIDEBAR CONTENT TO TOP
                ================================================== */

                #pricing_sidebar .sidebar-content {
                    padding-top: 0 !important;
                    align-items: flex-start !important;
                }

                /* Configuration card starts at the top */
                #pricing_sidebar > .card {
                    margin-top: 0 !important;
                    width: 100% !important;
                    height: auto !important;
                    flex: 0 0 auto !important;
                }

                /* Prevent the card body from stretching */
                #pricing_sidebar > .card .card-body {
                    height: auto !important;
                    flex: 0 0 auto !important;
                }

                /* ==================================================
                PRICING CONFIGURATION SIDEBAR HEADER
                ================================================== */

                /* Align Pricing sidebar content to the top */
                #pricing_sidebar {
                    padding-top: 0 !important;
                }

                #pricing_sidebar .card {
                    margin-top: 0 !important;
                    height: auto !important;
                }

                #pricing_sidebar .card-body {
                    height: auto !important;
                }

                /* Align Pricing configuration card with Filters card */
                #pricing_sidebar .card {
                    margin-top: 0 !important;
                }

                /* ==========================================================
                CENTRE + ENLARGE OPTIMISATION PROGRESS DIALOGUE
                ========================================================== */

                .modal-dialog {
                    max-width: 600px !important;
                    margin: 0 auto !important;
                }

                .modal-content {
                    min-height: 220px !important;
                }

                .modal-body {
                    padding: 40px !important;
                }

                .modal-body .progress {
                    height: 25px !important;
                    margin-top: 25px !important;
                    margin-bottom: 20px !important;
                }

                .modal-body .progress-bar {
                    font-size: 14px !important;
                    font-weight: 600 !important;
                }


                /* ==========================================================
                SHINY PROGRESS - CENTRE + ENLARGE
                ========================================================== */

                .shiny-progress {
                    position: fixed !important;
                    top: 50% !important;
                    left: 50% !important;
                    right: auto !important;
                    bottom: auto !important;
                    transform: translate(-50%, -50%) !important;

                    width: 650px !important;
                    max-width: 80vw !important;

                    z-index: 99999 !important;
                }

                .shiny-progress .progress-dialog {
                    width: 100% !important;
                    max-width: none !important;
                }

                .shiny-progress .progress {
                    height: 28px !important;
                }

                .shiny-progress .progress-bar {
                    font-size: 14px !important;
                    font-weight: 600 !important;
                }

                .purple-wand-icon,
                .purple-wand-icon svg {
                    color: #5800BD !important;
                }

            """),


            
            ui.tags.script("""
                document.addEventListener("click", function(event) {

                    const button = event.target;

                    const outputMap = {
                        "copy_simulator": "simulator_clipboard_data",
                        "copy_sensitivities": "sensitivities_clipboard_data",
                        "copy_importances": "attribute_importances_clipboard_data",
                        "copy_level_utilities": "level_utilities_clipboard_data",
                        "copy_profiles": "profiles_clipboard_data",
                        "copy_optimisation": "optimisation_clipboard_data",
                        "copy_pricing": "pricing_clipboard_data"
                    };

                    if (!outputMap[button.id]) {
                        return;
                    }

                    const output = document.getElementById(
                        outputMap[button.id]
                    );

                    if (!output) {
                        console.error("Clipboard output not found.");
                        return;
                    }

                    const text = output.textContent.trim();

                    if (!text) {
                        console.error("Clipboard data is empty.");
                        return;
                    }

                    navigator.clipboard.writeText(text).then(function() {

                        const originalText = button.innerText;

                        button.innerText = "Copied!";

                        setTimeout(function() {
                            button.innerText = originalText;
                        }, 1500);

                    }).catch(function(error) {

                        console.error("Clipboard failed:", error);

                    });
                });
            """),  
    ),

    # Simulator
    ui.nav_panel(
        "Simulator",
        ui.layout_sidebar(
           ui.sidebar(
                ui.output_plot("pref_shares_plot", fill=True, width="100%", height="700px"),
                id="share_sidebar",
                title=ui.tags.span(
                    "Product Preference Shares",
                    style="font-size: 20px; font-weight: bold;"
                ),
                position="right",
                open="always", 
                width=500,
            ),
            ui.layout_columns(
                ui.value_box(
                    "Weighted base size",
                    ui.output_text("base_n"),
                    showcase=ui.span(
                        icon_svg("weight-hanging"),
                        style=f"color: {TEMPLATE_BROWN};"
                    )
                ),
                ui.value_box(
                    "Total respondents",
                    ui.output_text("n_respondents"),
                    showcase=ui.span(
                        icon_svg("hashtag"),
                        style=f"color: {TEMPLATE_BROWN};"
                    )
                ),
                ui.value_box(
                    "Number of attributes",
                    ui.output_text("n_attributes"),
                    showcase=ui.span(
                        icon_svg("chart-simple"),
                        style=f"color: {TEMPLATE_BROWN};"
                    )
                ),
                id="data_summary"
            ),
            # ----------------------------------------------
            # Copy Simulator results
            # ----------------------------------------------
            ui.div(
                ui.tags.button(
                    "Copy data to clipboard",
                    id="copy_simulator",
                    class_="btn btn-sm btn-outline-secondary"
                ),

                ui.div(
                    ui.output_text_verbatim(
                        "simulator_clipboard_data"
                    ),
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

            ui.output_ui("product_cards"),

            bg=CANVAS_BG
        ),
        icon=icon_svg("calculator"),
        value="simulator_tab"
    ),

   # ----------------------------------------------------------
    # Attribute Importances
    # ----------------------------------------------------------

    ui.nav_panel(
        "Attribute Importances",

        card_importances,

        icon=icon_svg("chart-column"),
        value="sensitivities_tab"
    ),

       

    # ----------------------------------------------------------
    # Level Importances
    # ----------------------------------------------------------

    ui.nav_panel(
        "Level Importances",

        card_utilities,

        icon=icon_svg("chart-bar"),
        value="level_importances_tab"
    ),

# Profile analysis
    ui.nav_panel(
        "Profiles",


    # ==================================================
    # Detailed profile analysis
    # ==================================================
    ui.card(

        ui.card_header(

            ui.div(

                ui.span(
                    "Detailed profile analysis",
                    class_="profile-section-title"
                ),

                ui.div(

                    ui.tags.button(
                        "Copy data to clipboard",
                        id="copy_profiles",
                        class_="btn btn-sm btn-outline-secondary"
                    ),

                    ui.div(
                        ui.output_text_verbatim(
                            "profiles_clipboard_data"
                        ),
                        id="profiles_clipboard_data",
                        style="""
                            position: absolute;
                            left: -9999px;
                            width: 1px;
                            height: 1px;
                            overflow: hidden;
                        """
                    ),

                    class_="profile-actions"
                ),

                class_="profile-header",
            )
        ),

        ui.div(

            ui.tags.p(
                "Preference shares across respondent subgroups. "
                "The Total row provides the overall benchmark. "
                "Profiles with fewer than 100 respondents are "
                "shown in red italic text.",
                class_="profile-section-description",
                style="font-size: 16px;"
            ),

            class_="profile-description-row"
        ),

        ui.div(
            ui.output_ui(
                "profile_analysis_table"
            ),
            class_="profile-table-wrapper"
        ),

        class_="profile-analysis-card"
    ),

        # ==================================================
        # Preference share by profile
        # ==================================================
        ui.card(

            ui.card_header(
                ui.tags.div(
                    "Preference share by profile",
                    class_="profile-section-title"
                )
            ),

            ui.output_plot(
                "profile_share_chart",
                width="100%",
                height="300px"
            ),

            ui.output_ui(
                "profile_preference_summary"
            ),

            class_="profile-analysis-card profile-chart-card"
        ),

        icon=icon_svg("table-list"),
        value="profile_tab"
    ),




    # Optimizer
    # ======================================================
    # OPTIMISATION
    # ======================================================
    ui.nav_panel(
        "Optimisation",

        ui.div(

            ui.layout_sidebar(

                
                ui.sidebar(

                    ui.card(

                        # ==================================================
                        # BROWN TEMPLATE HEADER
                        # ==================================================

                        ui.card_header("Optimisation"),

                        ui.card_body(

                            # ==================================================
                            # RUN / RESET BUTTONS
                            # ==================================================

                            ui.layout_columns(

                                ui.input_action_button(
                                    "run_optim",
                                    "Run",
                                    class_="btn-optim",
                                    width="100%"
                                ),

                                ui.input_action_button(
                                    "reset_optim",
                                    "Reset",
                                    class_="btn-optim",
                                    width="100%"
                                ),

                                col_widths=[6, 6],
                                gap="0.5rem"
                            ),

                            # ==================================================
                            # OBJECTIVE
                            # ==================================================

                            ui.input_select(
                                "optim_objective",
                                "Objective",
                                choices={
                                    "Share": "Share",
                                    "Revenue": "Revenue"
                                },
                                selected="Share",
                                width="100%"
                            ),

                        

                            # ==================================================
                            # TARGET PRODUCT
                            # ==================================================

                            ui.output_ui(
                                "optim_product_selector"
                            ),

                            # ==================================================
                            # CONSTRAINTS + PRICING ASSUMPTIONS DROPDOWNS
                            # ==================================================

                            ui.hr(),

                             ui.accordion(
                                ui.accordion_panel(
                                    "Constraints",
                                    ui.output_ui("optimisation_constraints"),
                                ),
                                ui.accordion_panel(
                                    "Pricing assumptions",
                                    ui.input_numeric(
                                        "units_sold",
                                        "Expected units sold",
                                        value=500,
                                        min=1,
                                        step=1,
                                        width="100%",
                                    ),
                                    ui.output_ui("pricing_assumptions_controls"),
                                ),
                                id="optimisation_assumptions",
                                open=False,
                                multiple=True,
                            ),

                        ),  # Close ui.card_body

                        fill=False,
                        fillable=False,

                    ),  # Close ui.card

                    position="right",
                    id="optimisation_sidebar",
                    width=300,
                    open="always",
                    fillable=True,
                    bg=SIDEBAR_BG,

                ),  # Close ui.sidebar


                # ==================================================
                # MAIN OPTIMISATION AREA
                # ==================================================

                ui.div(
                    ui.strong("What optimisation shows"),
                    ui.p(
                        "Optimisation identifies the product configuration predicted to maximise "
                        "either preference share or revenue, based on the selected objective and "
                        "constraints. Use the controls to explore how changing price or locking "
                        "features affects the recommended configuration and expected performance.",
                        style="margin-bottom: 0;"
                    ),
                    style="""
                        padding: 12px 15px;
                        margin-bottom: 15px;
                        background-color: #f8f9fa;
                        border-radius: 6px;
                        font-size: 1.05rem;
                    """
                ),

                # ==================================================
                # OPTIMISED CONFIGURATION
                # Full-width card
                # ==================================================

                ui.card(

                    ui.card_header(
                        ui.div(
                            ui.h5(
                                "Optimised configuration",
                                class_="mb-0"
                            ),

                            ui.output_ui(
                                "copy_optimisation_button"
                            ),

                            class_="optimised-header"
                        )
                    ),

                    ui.card_body(

                        ui.tags.style("""
                            /* ==================================================
                            Compact Optimised Configuration card
                            ================================================== */

                            .optimised-box .card-header {
                                padding: 8px 12px !important;
                            }

                            .optimised-box .card-body {
                                padding: 0 !important;
                            }

                            .optimised-box .card-footer {
                                padding: 8px 12px !important;
                            }

                            /* ==================================================
                            Comparison table
                            ================================================== */

                            #best_product_table {
                                width: 100%;
                            }

                            #best_product_table table {
                                width: 100%;
                                table-layout: fixed;
                                margin-bottom: 0;
                            }

                            #best_product_table th,
                            #best_product_table td {
                                font-size: 13px !important;
                                padding: 8px 10px !important;
                                line-height: 1.35 !important;
                                vertical-align: middle !important;
                                text-align: center !important;
                                white-space: normal !important;
                                overflow-wrap: anywhere !important;
                                word-break: normal !important;
                                overflow: visible !important;
                                text-overflow: clip !important;
                            }

                            /* ==================================================
                            Column widths
                            ================================================== */

                            #best_product_table th:nth-child(1),
                            #best_product_table td:nth-child(1) {
                                width: 14%;
                            }

                            #best_product_table th:nth-child(2),
                            #best_product_table td:nth-child(2) {
                                width: 22%;
                            }

                            #best_product_table th:nth-child(3),
                            #best_product_table td:nth-child(3) {
                                width: 32%;
                            }

                            #best_product_table th:nth-child(4),
                            #best_product_table td:nth-child(4) {
                                width: 32%;
                            }

                            /* ==================================================
                            Dropdown labels
                            ================================================== */

                            .selectize-control.single .selectize-input {
                                height: 60px !important;
                                min-height: 60px !important;
                                white-space: normal !important;
                                display: flex !important;
                                align-items: center !important;
                                justify-content: center !important;
                                text-align: center !important;
                                padding: 8px 35px 8px 12px !important;
                            }

                            .selectize-control.single .selectize-input > div {
                                font-size: 12px !important;
                                white-space: normal !important;
                                overflow-wrap: break-word !important;
                                line-height: 1.35 !important;
                                text-align: center !important;
                                width: 100% !important;
                            }

                            /* ==================================================
                            Attribute labels
                            ================================================== */

                            .shiny-input-container > label {
                                font-weight: 600 !important;
                                text-align: center !important;
                                width: 100% !important;
                            }

                            /* ==================================================
                            Dropdown menu
                            ================================================== */

                            .selectize-dropdown {
                                background-color: #FFFFFF !important;
                                border: 1px solid #999999 !important;
                                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.18) !important;
                                border-radius: 4px !important;
                                z-index: 1000 !important;
                            }

                            .selectize-dropdown .option {
                                font-size: 14px !important;
                                text-align: center !important;
                                white-space: normal !important;
                                line-height: 1.35 !important;
                                padding: 8px 10px !important;
                            }
                        """),

                        # ==================================================
                        # Hidden clipboard output
                        # ==================================================

                        ui.div(
                            ui.output_text_verbatim(
                                "optimisation_clipboard_data"
                            ),
                            style="""
                                position: absolute;
                                left: -9999px;
                                width: 1px;
                                height: 1px;
                                overflow: hidden;
                            """
                        ),

                        # ==================================================
                        # Optimised product table
                        # ==================================================

                        ui.div(
                            ui.output_ui(
                                "best_product_table"
                            ),
                            class_="optimised-table-container"
                        ),

                        class_="p-0 overflow-hidden",
                        style="min-height: 0;"
                    ),

                    # ==================================================
                    # Configuration summary
                    # ==================================================

                    ui.card_footer(
                        ui.output_ui(
                            "optim_config_summary_text"
                        ),
                        style=(
                            "font-size: 0.95rem; "
                            "background-color: #f8f9fa; "
                            "border-top: 1px solid #dee2e6; "
                            "padding: 8px 12px;"
                        )
                    ),

                    class_="optimised-box",
                    fill=False,
                    fillable=False
                ),


                # ==================================================
                # IMPACT + SUMMARY ROW
                # ==================================================

                ui.layout_columns(

                    # ==================================================
                    # IMPACT CARD
                    # ==================================================

                    ui.card(

                        ui.card_header(
                            ui.div(
                                ui.h5(
                                    "Impact",
                                    class_="mb-0"
                                ),

                                class_="optimised-header"
                            )
                        ),

                        ui.card_body(

                            ui.output_plot(
                                "optim_plot",
                                height="350px"
                            ),

                            class_="p-0 overflow-hidden",
                            style="min-height: 0;"
                        ),

                        class_="optim-box",
                        fill=False,
                        fillable=False
                    ),


                    # ==================================================
                    # SUMMARY CARD
                    # ==================================================

                    ui.card(

                        ui.card_header(
                            ui.div(
                                ui.h5(
                                    "Summary",
                                    class_="mb-0"
                                ),

                                class_="optimised-header"
                            )
                        ),

                        ui.card_body(

                            ui.output_ui(
                                "optim_summary_text"
                            ),

                            style=(
                                "font-size: 0.95rem; "
                                "padding: 15px; "
                                "min-height: 350px;"
                            )
                        ),

                        class_="optim-box",
                        fill=False,
                        fillable=False
                    ),

                    col_widths=[6, 6],
                    fill=False,
                    fillable=False
                ),
                
            ),

            class_="d-flex flex-column",
            style="min-height: 0; height: auto;"
        ),

        icon=icon_svg(
            "screwdriver-wrench"
        ),

        value="optimisation_tab"
    ),

     # Pricing Analysis
    ui.nav_panel(
        "Pricing",
        ui.layout_sidebar(
            pricing_sidebar_ui,
            card_pricing,
        ),
        icon=icon_svg("money-bill-trend-up"),
        value="pricing_tab"
    ),

        ui.nav_spacer(),

        ui.nav_control(
            ui.tags.img(
                src="logo.png",
                style="height: 40px; width: auto; margin-right: 20px;"
            )
        ),

    sidebar=ui.sidebar(
        filters_ui,

        ui.hr(),

        # ==================================================
        # INCLUDE NONE OPTION
        # Hidden on Attribute Importances and Level Importances
        # ==================================================
        ui.panel_conditional(
            """
            input.main_page != 'sensitivities_tab' &&
            input.main_page != 'level_importances_tab'
            """,

            ui.input_checkbox(
                "show_none",
                "Include 'NONE' in shares?",
                value=True
            )
        ),

        ui.input_action_button(
            "reset",
            "Reset to base scenario",
            width="100%",
            icon=icon_svg("arrow-rotate-left")
        ),

        id="filters_sidebar",
        width=300,
        open="always",
        fillable=True,
        bg=SIDEBAR_BG
    ),

    title=ui.h1("Conjoint Simulator"),
    id="main_page"
)

# ======================================================
# SERVER
# ======================================================
def server(input, output, session):
    # -------------------------
    # Dynamic filtering
    # -------------------------
    @reactive.Effect
    @reactive.event(input.all_filters)
    def toggle_filters():
        all_selected = input.all_filters()
        for c in FILTER_COLS:
            cid = make_id(f"filter_{c}")
            choices = sorted(filters_df[c].dropna().astype(str).unique())
            ui.update_checkbox_group(cid, selected=choices if all_selected else [])
        ui.update_switch("all_filters", label="Deselect all" if not all_selected else "Select all")

    # -------------------------
    # Product cards layout 
    # -------------------------
    @render.ui
    def product_cards():
        sidebar_open = input.share_sidebar()
        width = 1/3 if sidebar_open else 1/4
        
        return ui.layout_column_wrap(
            *[create_product_card(i) for i in range(1, N_PRODUCTS+1)],
            width=width
        )


    # -------------------------
    # In-Card Share Renderers
    # -------------------------
    def _generate_card_share(p_id):
        try:
            shares_df = selected_shares()
            row = shares_df[shares_df["ProductID"].astype(str) == str(p_id)]
            share_val = row["PrefShare"].iloc[0] * 100 if not row.empty else 0.0
        except Exception:
            # Fallback to 0.0 if the math isn't ready yet during boot-up
            share_val = 0.0
            
        # 🌟 Outputs pure white, bold text to seamlessly blend into the unified header!
        html_text = f"<span style='color: white; font-weight: bold; font-size: 1.05rem;'>Share: {share_val:.1f}%</span>"
        
        return ui.HTML(html_text)

    @render.text
    def simulator_clipboard_data():

        shares_df = selected_shares().copy()

        # --------------------------------------------------
        # Keep only actual products
        # --------------------------------------------------
        shares_df = shares_df[
            shares_df["ProductID"].astype(str) != "NONE"
        ].copy()

        # --------------------------------------------------
        # Get current product configuration
        # --------------------------------------------------
        current_products = products_df().copy()

        if current_products.empty:
            current_products = BASECASE_DF.copy()

        # --------------------------------------------------
        # Merge product configuration with shares
        # --------------------------------------------------
        export_df = current_products.merge(
            shares_df,
            on="ProductID",
            how="left"
        )

        # --------------------------------------------------
        # Format preference share as a percentage
        # --------------------------------------------------
        export_df["Preference Share"] = (
            export_df["PrefShare"] * 100
        ).round(1)

        export_df.drop(
            columns=["PrefShare"],
            inplace=True,
            errors="ignore"
        )

        # --------------------------------------------------
        # Convert to tab-separated text
        # --------------------------------------------------
        return export_df.to_csv(
            sep="\t",
            index=False
        )


    @render.text
    def level_utilities_clipboard_data():

        df = level_utilities_df().copy()

        return df.to_csv(
            sep="\t",
            index=False
        )

    

    @render.text
    def attribute_importances_clipboard_data():

        df = attribute_importances_df().copy()

        return df.to_csv(
            sep="\t",
            index=False
        )

    @render.text
    def pricing_clipboard_data():

        # --------------------------------------------------
        # Get the currently selected product
        # --------------------------------------------------

        selected_product = int(
            str(input.pricing_product()).replace(
                "Product ", ""
            )
        )

        # --------------------------------------------------
        # Get the same pricing results used by the chart
        # --------------------------------------------------

        pricing_df = _pricing_results().copy()

        p_col = str(selected_product)

        # --------------------------------------------------
        # Calculate revenue exactly as the chart does
        # --------------------------------------------------

        pricing_df["Revenue"] = (
            pricing_df[p_col]
            * pricing_df["Price point"]
        )

        # --------------------------------------------------
        # Create export dataframe
        # --------------------------------------------------

        export_df = pricing_df[
            ["Price point", p_col, "Revenue"]
        ].copy()

        export_df.rename(
            columns={
                "Price point": "Price",
                p_col: "Preference Share"
            },
            inplace=True
        )

        # --------------------------------------------------
        # Format preference share as percentage
        # --------------------------------------------------

        export_df["Preference Share"] = (
            export_df["Preference Share"] * 100
        ).round(1)

        # --------------------------------------------------
        # Format revenue
        # --------------------------------------------------

        export_df["Revenue"] = (
            export_df["Revenue"]
            .round(2)
        )

        # --------------------------------------------------
        # Convert to tab-separated text
        # --------------------------------------------------

        return export_df.to_csv(
            sep="\t",
            index=False
        )

    @render.ui
    def card_share_1(): return _generate_card_share(1)
    @render.ui
    def card_share_2(): return _generate_card_share(2)
    @render.ui
    def card_share_3(): return _generate_card_share(3)
    @render.ui
    def card_share_4(): return _generate_card_share(4)
    @render.ui
    def card_share_5(): return _generate_card_share(5)
    @render.ui
    def card_share_6(): return _generate_card_share(6)
    @render.ui
    def card_share_7(): return _generate_card_share(7)
    @render.ui
    def card_share_8(): return _generate_card_share(8)
    @render.ui
    def card_share_9(): return _generate_card_share(9)
    @render.ui
    def card_share_10(): return _generate_card_share(10)

    @render.ui
    def pricing_product_selector():
        product_choices = [
            f"Product {product_no}"
            for product_no in range(1, N_PRODUCTS+1)
            if input[f"product_{product_no}_include"]()
        ]
        return ui.input_select(
            "pricing_product",
            "Select product for pricing analysis",
            choices=product_choices,
        )


    @render.ui
    def optim_product_selector():

        product_choices = [
            f"Product {product_no}"
            for product_no in range(1, N_PRODUCTS + 1)
            if input[f"product_{product_no}_include"]()
        ]

        if len(product_choices) == 0:
            product_choices = ["Product 1"]

        return ui.input_select(
            "optim_product",
            "Target product:",
            choices=product_choices,
            selected=product_choices[0]
        )

    @render.ui
    def optimisation_constraints():
        return _build_optimisation_constraint_ui()




    # -------------------------
    # Restrictions
    # -------------------------
    if not restrictions_df.empty:
        @reactive.Effect
        def enforce_restrictions():
            for p in range(1, N_PRODUCTS + 1):
                if not input[f"product_{p}_include"]():
                    continue
                for _, r in restrictions_df.iterrows():
                    attr_a = clean_attr(r["If Attribute A"])
                    level_a = str(r["Level"])
                    attr_b = clean_attr(r["Then Attribute B"])
                    a_id = f"product_{p}_{make_id(attr_a)}"
                    b_id = f"product_{p}_{make_id(attr_b)}"
                    try:
                        val_a = input[a_id]()
                    except KeyError:
                        continue
                    apply_restrictions(
                        restrictions_df=restrictions_df,
                        current_attr=attr_a,
                        current_value=val_a,
                        target_attr=attr_b,
                        target_input_id=b_id,
                        input=input,
                        session=session
                    )

        # ==================================================
        # PRICING ANALYSIS RESULTS
        # ==================================================


    def _current_pricing_config():
        """Capture the settings that determine the pricing results."""

        p_df = products_df()

        if isinstance(p_df, str) and p_df == "BASECASE_FLAG":
            p_df = BASECASE_DF.copy()

        products_hash = int(
            pd.util.hash_pandas_object(p_df, index=True).sum()
        )

        return (
            input.pricing_product(),
            input.pricing_attribute(),
            input.show_none(),
            tuple(map(str, filtered_respondents())),
            products_hash,
        )

    @reactive.calc
    @reactive.event(input.run_pricing, ignore_none=True)
    def _pricing_results():

        run_config = _current_pricing_config()

        selected_product = int(
            str(input.pricing_product()).replace("Product ", "")
        )

        n_points = 50

        p_df = products_df()

        if isinstance(p_df, str) and p_df == "BASECASE_FLAG":
            p_df = BASECASE_DF.copy()

        include_none = input.show_none()

        # Get currently filtered respondents
        respondent_ids = filtered_respondents()

        # --------------------------------------------------
        # Prevent pricing analysis from running with 0 respondents
        # --------------------------------------------------
        if len(respondent_ids) == 0:
            return pd.DataFrame()

        with ui.Progress(
            min=0,
            max=100
        ) as progress:

            progress.set(
                0,
                message="Starting pricing analysis..."
            )

            result = run_pricing_analysis(
                product_no=selected_product,
                products_df=p_df,
                price_attr=input.pricing_attribute(),
                n_price_points=n_points,
                include_none=include_none,
                respondent_ids=respondent_ids,
                progress=progress
            )

            progress.set(
                100,
                message="Pricing analysis complete"
            )

            result.attrs["pricing_config"] = run_config
            return result

    @reactive.calc
    def _pricing_is_stale():
        result = _pricing_results()

        if result.empty:
            return True

        saved_config = result.attrs.get("pricing_config")

        if saved_config is None:
            return True

        return saved_config != _current_pricing_config()


    @render.ui
    def pricing_status():
        if _pricing_is_stale():
            return ui.div(
                "Your pricing settings have changed. "
                "Click 'Run pricing analysis' to refresh the results.",
                style=(
                    "color: #3C0F03; "
                    "background-color: #ECE7DA; "
                    "padding: 12px; "
                    "border-radius: 6px; "
                    "margin-bottom: 12px; "
                    "font-weight: 600;"
                ),
            )

        return ui.div()


    # ==================================================
    # PRICING PLOT
    # ==================================================

    
    @render.plot
    def pricing_plot():

        pricing_results = _pricing_results()

        if pricing_results.empty or _pricing_is_stale():
            return None

        selected_product = int(
            str(input.pricing_product()).replace("Product ", "")
        )

        price_attr = input.pricing_attribute()

        currency = conjoint_model.ATTRIBUTE_CURRENCIES.get(
            price_attr, {}
        )

        return plot_pricing_results(
            pricing_results_df=pricing_results,
            selected_product=selected_product,
            show_competitors=input.show_competitors(),
            products_df=products_df(),
            price_attr=price_attr,
            currency_symbol=currency.get("symbol", ""),
            currency_decimals=currency.get("decimals", 2)
        )


    # -------------------------
    # Reset
    # -------------------------
    @reactive.Effect
    def reset_to_basecase():
        input.reset()
        for p in range(1, N_PRODUCTS + 1):
            ui.update_checkbox(f"product_{p}_include", value=True)
            for attr in ATTRIBUTES:
                val = BASECASE_DF.loc[p - 1, attr]
                cid = f"product_{p}_{make_id(attr)}"

                if attr in PRICE_ATTRS:
                    ui.update_slider(cid, value=float(val))
                else:
                    ui.update_select(cid, selected=str(val))

    # -------------------------
    # Filtered respondents
    # -------------------------
    @reactive.Calc
    def filtered_data():
        df = filters_df.copy()
        for c in FILTER_COLS:
            cid = make_id(f"filter_{c}")
            try:
                sel = input[cid]()
            except KeyError:
                sel = None
            if sel is None or len(sel) == 0:
                return pd.DataFrame([], columns=filters_df.columns)
            df = df[df[c].astype(str).isin(sel)]
        return df

    @reactive.Calc
    def filtered_respondents():
        return filtered_data()["Respondent"]

    @render.text
    def base_n():
        try:
            weighted_base = filtered_data()["Weight"].sum()
            return f"{weighted_base:,.0f}"
        except KeyError:
            return "-"

    @render.text
    def n_respondents():
        return f"{filtered_respondents().nunique()}"

    @render.text
    def n_attributes():
        return f"{grid_df.shape[1]}"

    # -------------------------
    # Products DF
    # -------------------------
    @reactive.Calc
    def products_df():
        rows = []
        for product_no in range(1, N_PRODUCTS + 1):
            if not input[f"product_{product_no}_include"]():
                continue
            row = {"ProductID": product_no}
            for attr in ATTRIBUTES:
                row[attr] = input[f"product_{product_no}_{make_id(attr)}"]()
            rows.append(row)
            
        df = pd.DataFrame(rows)
        
        # 🌟 THE FIX: Universally cast types at the source!
        # This converts Shiny's text strings back into numbers, completely unlocking 
        # the pricing interpolation engine for all tabs!
        if not df.empty:
            for attr in ATTRIBUTES:
                if attr in PRICE_ATTRS:
                    df[attr] = df[attr].astype(float)
                else:
                    original_vals = grid_df[attr].dropna().unique()
                    str_to_orig = {str(v): v for v in original_vals}
                    df[attr] = df[attr].apply(lambda x: str_to_orig.get(str(x), x))
                    
            df["ProductID"] = df["ProductID"].astype(BASECASE_DF["ProductID"].dtype)
            
        return df

    # -------------------------
    # Restriction helper for shares
    # -------------------------

    def apply_restrictions_to_df(product_df):
        """
        Apply the Excel Restrictions rules directly to a product dataframe
        before it is passed into the conjoint model.
        """

        df = product_df.copy()

        # No restrictions = return unchanged
        if restrictions_df.empty:
            return df

        # Loop through each product
        for p in range(len(df)):

            # Loop through each restriction
            for _, r in restrictions_df.iterrows():

                attr_a = clean_attr(r["If Attribute A"])
                level_a = str(r["Level"]).strip()

                attr_b = clean_attr(r["Then Attribute B"])

                text_to_show = str(
                    r.get("Text to show on B", "NA")
                ).strip()

                # Check attributes exist
                if attr_a not in df.columns or attr_b not in df.columns:
                    continue

                # Current value of Attribute A
                current_value = str(
                    df.iloc[p][attr_a]
                ).strip()

                # Apply restriction
                if current_value == level_a:

                    df.iloc[
                        p,
                        df.columns.get_loc(attr_b)
                    ] = text_to_show

        return df





    # -------------------------
    # Shares
    # -------------------------
    @reactive.Calc
    # -------------------------
    # Shares
    # -------------------------
    @reactive.Calc
    def selected_shares():
        p_df = products_df()
        include_none = input.show_none()
        
        is_basecase = True
        if len(p_df) != len(BASECASE_DF):
            is_basecase = False
            print("🚨 MISMATCH: Number of products included is different!")
        else:
            for i in range(len(p_df)):
                for attr in ATTRIBUTES:
                    # Strip out trailing spaces, .0 decimals, and commas to aggressively check for a match
                    val_ui = str(p_df.iloc[i][attr]).strip().replace(".0", "").replace(",", "")
                    val_base = str(BASECASE_DF.iloc[i][attr]).strip().replace(".0", "").replace(",", "")
                    
                    if val_ui != val_base:
                        # 🌟 THE FIX: Ignore the "-" character created by UI restrictions!
                        if val_ui == "-":
                            continue
                            
                        # THIS WILL PRINT TO YOUR TERMINAL SO WE CAN SEE THE BUG!
                        print(f"🚨 MISMATCH FOUND -> Product {i+1} | Attribute '{attr}': UI sent '{val_ui}' but Basecase has '{val_base}'")
                        is_basecase = False
                        
        if is_basecase:
            print("✅ PERFECT MATCH: Mirroring basecase to avoid Monte Carlo wobble!")
            return basecase_shares()
        else:
            print("▶️ UI IS DIFFERENT: Running conjoint engine...")
            
        # If it IS different, strictly cast the types back to native Python types before running the math
        safe_df = p_df.copy()
        if not safe_df.empty:
            for attr in ATTRIBUTES:
                if attr == PRICE_ATTR:
                    safe_df[attr] = safe_df[attr].astype(float)
                else:
                    original_vals = grid_df[attr].dropna().unique()
                    str_to_orig = {str(v): v for v in original_vals}
                    safe_df[attr] = safe_df[attr].apply(lambda x: str_to_orig.get(str(x), x))
                    
            safe_df["ProductID"] = safe_df["ProductID"].astype(BASECASE_DF["ProductID"].dtype)

        # Apply the Excel restrictions before calculating shares
        safe_df = apply_restrictions_to_df(safe_df)

        print("\n================ SHARE DEBUG ================")
        print("BASECASE DF:")
        print(BASECASE_DF)

        print("\nSCENARIO DF:")
        print(safe_df)

        print("\nBASECASE TYPES:")
        print(BASECASE_DF.dtypes)

        print("\nSCENARIO TYPES:")
        print(safe_df.dtypes)

        print("=============================================\n")

        return conjoint_model.compute_shares(
            safe_df,
            respondent_ids=filtered_respondents(),
            include_none=include_none
        )
    
    @reactive.Calc
    def basecase_shares():
        include_none = input.show_none()

        # Apply the Excel restrictions to the base case
        restricted_basecase = apply_restrictions_to_df(BASECASE_DF)

        print("\n================ BASECASE RESTRICTION DEBUG ================")
        print("ORIGINAL BASECASE:")
        print(BASECASE_DF)

        print("\nRESTRICTED BASECASE:")
        print(restricted_basecase)

        print("=============================================================\n")

        result = conjoint_model.compute_shares(
            restricted_basecase,
            respondent_ids=filtered_respondents(),
            include_none=include_none
        )

        print("\n================ BASECASE SHARES DEBUG ================")
        print(result)
        print("TYPE:", type(result))
        print("=======================================================\n")

        return result

    @render.plot
    def pref_shares_plot():
        fig = plot_product_preference_shares(
            selected_shares=selected_shares(),
            base_shares=basecase_shares(),
            figsize=(4, 7)
        )
        return fig

    @render.ui
    def level_attribute_selector():

        df = level_utilities_df()

        if df.empty:
            return ui.div()

        attributes = (
            df["Attribute"]
            .dropna()
            .drop_duplicates()
            .tolist()
        )

        return ui.div(
            ui.input_select(
                "selected_level_attribute",
                "Attribute",
                choices=attributes,
                selected=attributes[0],
            ),
            style="""
                width: 300px;
            """
        )

    # ==================================================
    # ATTRIBUTE IMPORTANCE KEY INSIGHT
    # ==================================================

    @render.ui
    def attribute_importance_summary():

        df = attribute_importances_df().copy()

        # --------------------------------------------------
        # Handle no data
        # --------------------------------------------------

        if df.empty:
            return ui.HTML(
                "<span>No data available for the selected filters.</span>"
            )

        # --------------------------------------------------
        # Sort attributes by importance
        # --------------------------------------------------

        df = df.sort_values(
            "Importance",
            ascending=False
        ).reset_index(drop=True)

        # --------------------------------------------------
        # Get key attributes
        # --------------------------------------------------

        highest = df.iloc[0]
        lowest = df.iloc[-1]

        highest_attr = highest["Attribute"]
        highest_value = highest["Importance"]

        lowest_attr = lowest["Attribute"]
        lowest_value = lowest["Importance"]

        # --------------------------------------------------
        # Build summary
        # --------------------------------------------------

        summary = (
            f"<span>"
            f"<b>{highest_attr}</b> is the strongest driver of preference, "
            f"with a relative importance of <b>{highest_value:.1f}%</b>. "
            f"This is followed by <b>{df.iloc[1]['Attribute']}</b> "
            f"at <b>{df.iloc[1]['Importance']:.1f}%</b>. "
            f"At the other end of the scale, <b>{lowest_attr}</b> "
            f"has the lowest relative importance at "
            f"<b>{lowest_value:.1f}%</b>."
            f"</span>"
        )

        return ui.div(
            ui.span(
                icon_svg("wand-magic-sparkles"),
                class_="purple-wand-icon",
                style="""
                    font-size: 1.1rem;
                    margin-right: 8px;
                    flex-shrink: 0;
                """
            ),

            ui.HTML(summary),

            style="""
                padding: 12px 15px;
                margin-top: 10px;
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                font-size: 0.95rem;
                display: flex;
                align-items: flex-start;
            """
        )


    # ==================================================
    # LEVEL UTILITIES KEY INSIGHT
    # ==================================================

    @render.ui
    def level_utilities_summary():

        df = level_utilities_df().copy()

        # --------------------------------------------------
        # Handle no data
        # --------------------------------------------------

        if df.empty:
            return ui.HTML(
                "<span>No data available for the selected filters.</span>"
            )

        # --------------------------------------------------
        # Find strongest positive and negative utilities
        # --------------------------------------------------

        df_sorted = df.sort_values(
            "Utility",
            ascending=False
        ).reset_index(drop=True)

        strongest = df_sorted.head(3)

        weakest = df_sorted.tail(3).sort_values(
            "Utility",
            ascending=True
        )

        # --------------------------------------------------
        # Build level labels including attribute
        # --------------------------------------------------

        strongest_levels = [
            f"{row['Attribute']}: {row['Level']}"
            for _, row in strongest.iterrows()
        ]

        weakest_levels = [
            f"{row['Attribute']}: {row['Level']}"
            for _, row in weakest.iterrows()
        ]

        # --------------------------------------------------
        # Format lists naturally
        # --------------------------------------------------

        def format_list(items):

            if len(items) == 1:
                return items[0]

            if len(items) == 2:
                return f"{items[0]} and {items[1]}"

            return (
                ", ".join(items[:-1])
                + " and "
                + items[-1]
            )

        strongest_text = format_list(strongest_levels)
        weakest_text = format_list(weakest_levels)

        # --------------------------------------------------
        # Create concise insight
        # --------------------------------------------------

        summary_html = (
            f"<span>"
            f"Preference is strongest for <b>{strongest_text}</b>, "
            f"while <b>{weakest_text}</b> show the weakest preference signals."
            f"</span>"
        )

        return ui.div(
            ui.span(
                icon_svg("wand-magic-sparkles"),
                class_="purple-wand-icon",
                style="""
                    font-size: 1.1rem;
                    margin-right: 8px;
                    flex-shrink: 0;
                """
            ),

            ui.HTML(summary_html),

            style="""
                padding: 12px 15px;
                margin-top: 10px;
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                font-size: 0.95rem;
                display: flex;
                align-items: flex-start;
            """
        )

    # ==================================================
    # LEVEL UTILITIES ATTRIBUTE SELECTOR
    # ==================================================

    @render.ui
    def level_utilities_attribute_selector():

        df = level_utilities_df()

        # --------------------------------------------------
        # Handle no data
        # --------------------------------------------------

        if df is None or df.empty:
            return ui.div(
                "No attributes available.",
                style="color: #6c757d;"
            )

        # --------------------------------------------------
        # Get available attributes
        # --------------------------------------------------

        attributes = (
            df["Attribute"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        if not attributes:
            return ui.div(
                "No attributes available.",
                style="color: #6c757d;"
            )

        # --------------------------------------------------
        # Create dropdown
        # --------------------------------------------------

        return ui.input_select(
            "selected_level_attribute",
            "Select attribute",
            choices=attributes,
            selected=attributes[0]
        )

    # -------------------------
    # Profile analysis
    # -------------------------
    @reactive.Calc
    def profile_analysis_df():

        # --------------------------------------------------
        # Merge respondent filters with utilities
        # --------------------------------------------------

        merged_results = pd.merge(
            filters_df,
            utils_df,
            on=["Respondent"],
            how="left"
        )

        # --------------------------------------------------
        # Identify utility columns
        # --------------------------------------------------

        util_cols = [
            c
            for c in merged_results.columns
            if c not in filters_df.columns
        ]

        # --------------------------------------------------
        # Convert profile variables into long format
        # --------------------------------------------------

        pivotted_data = pd.melt(
            merged_results,
            id_vars=["Respondent", "Weight"] + util_cols,
            value_vars=FILTER_COLS,
            var_name="Crossbreak",
            value_name="Subgroup"
        )

        # --------------------------------------------------
        # Create profile groups and retain respondent IDs
        # --------------------------------------------------

        prof_analysis_df = (
            pivotted_data
            .groupby(["Crossbreak", "Subgroup"])["Respondent"]
            .apply(list)
            .reset_index(name="Respondent IDs")
        )

        # --------------------------------------------------
        # Preserve the Excel FILTER_COLS order
        # --------------------------------------------------

        prof_analysis_df["Crossbreak"] = pd.Categorical(
            prof_analysis_df["Crossbreak"],
            categories=FILTER_COLS,
            ordered=True
        )

        prof_analysis_df.sort_values(
            ["Crossbreak", "Subgroup"],
            inplace=True,
            ignore_index=True
        )

        # --------------------------------------------------
        # Unweighted respondent base
        # --------------------------------------------------

        prof_analysis_df["# Respondents"] = (
            prof_analysis_df["Respondent IDs"]
            .apply(len)
        )

        # --------------------------------------------------
        # Weighted respondent base
        # --------------------------------------------------

        prof_analysis_df["Weighted base"] = (
            prof_analysis_df["Respondent IDs"]
            .apply(
                lambda ids: merged_results.loc[
                    merged_results["Respondent"].isin(ids),
                    "Weight"
                ].sum()
            )
        )

        # --------------------------------------------------
        # Calculate product shares for each profile
        # --------------------------------------------------

        include_none = input.show_none()

        product_shares = pd.concat(
            [
                conjoint_model.compute_shares(
                    apply_restrictions_to_df(products_df()),
                    respondent_ids=ids,
                    include_none=include_none
                ).set_index("ProductID")
                for ids in prof_analysis_df["Respondent IDs"]
            ],
            axis=1,
            ignore_index=True
        ).T

        # --------------------------------------------------
        # Add NONE column when NONE is not selected
        # --------------------------------------------------

        if not include_none:
            product_shares["NONE"] = 0.0

        # --------------------------------------------------
        # Rename share columns
        # --------------------------------------------------

        product_shares.rename(
            columns=lambda x:
                f"Product {x} Share"
                if x != "NONE"
                else "NONE Share",
            inplace=True
        )

        # --------------------------------------------------
        # Make sure all product columns exist
        # --------------------------------------------------

        pref_cols = []

        for p in range(1, N_PRODUCTS + 1):

            col_name = f"Product {p} Share"

            pref_cols.append(col_name)

            if col_name not in product_shares.columns:
                product_shares[col_name] = 0.0

        # --------------------------------------------------
        # Keep products in Product 1, Product 2...
        # order
        # --------------------------------------------------

        product_shares = product_shares.loc[
            :,
            pref_cols + ["NONE Share"]
        ]

        # Merge profile information with profile shares
        # --------------------------------------------------

        prof_analysis_df = pd.merge(
            prof_analysis_df,
            product_shares,
            left_index=True,
            right_index=True,
            how="inner"
        )

        # --------------------------------------------------
        # Create TOTAL row
        #
        # This uses ALL respondents in the current filtered
        # sample, so it represents the overall preference
        # share rather than a particular profile.
        # --------------------------------------------------

        all_respondents = merged_results["Respondent"].dropna().unique()

        total_shares = conjoint_model.compute_shares(
            apply_restrictions_to_df(products_df()),
            respondent_ids=all_respondents,
            include_none=include_none
        ).set_index("ProductID")

        # --------------------------------------------------
        # Make sure the TOTAL shares have the same columns
        # as the profile rows
        # --------------------------------------------------

        total_row = {}

        total_row["Crossbreak"] = "Total"
        total_row["Subgroup"] = "All respondents"

        total_row["# Respondents"] = len(all_respondents)

        total_row["Weighted base"] = merged_results["Weight"].sum()

        # Product shares
        for p in range(1, N_PRODUCTS + 1):

            col_name = f"Product {p} Share"

            if p in total_shares.index:

                total_row[col_name] = total_shares.loc[
                    p,
                    "PrefShare"
                ]

            else:

                total_row[col_name] = 0.0

        # NONE share
        if include_none:

            if "NONE" in total_shares.index:

                total_row["NONE Share"] = total_shares.loc[
                    "NONE",
                    "PrefShare"
                ]

            else:

                total_row["NONE Share"] = 0.0

        else:

            total_row["NONE Share"] = 0.0

        # --------------------------------------------------
        # Convert total row into a dataframe
        # --------------------------------------------------

        total_df = pd.DataFrame(
            [total_row]
        )

        # --------------------------------------------------
        # Add TOTAL to the top of the table
        # --------------------------------------------------

        prof_analysis_df = pd.concat(
            [
                total_df,
                prof_analysis_df
            ],
            ignore_index=True
        )

        # --------------------------------------------------
        # Respondent IDs are only needed internally
        # --------------------------------------------------

        prof_analysis_df.drop(
            columns="Respondent IDs",
            inplace=True
        )

        return prof_analysis_df


# ======================================================
# PROFILE ANALYSIS TABLE
# ======================================================

    @render.ui
    def profile_analysis_table():

        df = profile_analysis_df().copy()

        # --------------------------------------------------
        # Identify share columns
        # --------------------------------------------------

        share_cols = [
            col
            for col in df.columns
            if "Share" in col
        ]

        # --------------------------------------------------
        # Keep original numeric shares so we can identify
        # the highest share in each row
        # --------------------------------------------------

        numeric_shares = df[share_cols].copy()

        # --------------------------------------------------
        # Format bases
        # --------------------------------------------------

        df["Weighted base"] = (
            df["Weighted base"]
            .round(0)
            .astype(int)
        )

        df["# Respondents"] = (
            df["# Respondents"]
            .astype(int)
        )

        # --------------------------------------------------
        # Format shares as percentages
        # --------------------------------------------------

        for col in share_cols:

            df[col] = df[col].apply(
                lambda x: f"{x * 100:.1f}%"
            )

        # --------------------------------------------------
        # Rename columns
        # --------------------------------------------------

        df.rename(
            columns={
                "Crossbreak": "Profile",
                "Subgroup": "Group",
                "NONE Share": "None"
            },
            inplace=True
        )

        @render.text
        def profiles_clipboard_data():

            df = profile_analysis_df().copy()

            # --------------------------------------------------
            # Identify share columns
            # --------------------------------------------------

            share_cols = [
                col
                for col in df.columns
                if "Share" in col
            ]

            # --------------------------------------------------
            # Format bases
            # --------------------------------------------------

            df["Weighted base"] = (
                df["Weighted base"]
                .round(0)
                .astype(int)
            )

            df["# Respondents"] = (
                df["# Respondents"]
                .astype(int)
            )

            # --------------------------------------------------
            # Format shares as percentages
            # --------------------------------------------------

            for col in share_cols:
                df[col] = (
                    df[col] * 100
                ).round(1).map(lambda x: f"{x:.1f}%")

            # --------------------------------------------------
            # Rename columns
            # --------------------------------------------------

            df.rename(
                columns={
                    "Crossbreak": "Profile",
                    "Subgroup": "Group",
                    "NONE Share": "None"
                },
                inplace=True
            )

            # --------------------------------------------------
            # Convert to tab-separated text
            # --------------------------------------------------

            return df.to_csv(
                sep="\t",
                index=False
            )


        # --------------------------------------------------
        # Styling function
        # --------------------------------------------------

        def style_profile_row(row):

            styles = [""] * len(row)

            # ----------------------------------------------
            # Identify whether this is the Total row
            # ----------------------------------------------

            is_total = (
                str(row["Profile"]).strip().lower()
                == "total"
            )

            # ----------------------------------------------
            # Low respondent base
            # ----------------------------------------------

            is_low_base = (
                not is_total
                and row["# Respondents"] < 100
            )

            # ----------------------------------------------
            # Base row styling
            # ----------------------------------------------

            if is_total:

                styles = [
                    "font-weight: 700; "
                    "background-color: #f3f4f6; "
                    "border-top: 2px solid #460809; "
                    "border-bottom: 2px solid #460809;"
                    for _ in row
                ]

            elif is_low_base:

                styles = [
                    "color: #c0392b; "
                    "font-style: italic;"
                    for _ in row
                ]

            # ----------------------------------------------
            # Identify highest share
            # ----------------------------------------------

            row_shares = numeric_shares.loc[row.name]

            if not row_shares.empty:

                max_share = row_shares.max()

                for original_col in share_cols:

                    if row_shares[original_col] == max_share:

                        display_col = (
                            "None"
                            if original_col == "NONE Share"
                            else original_col
                        )

                        col_position = (
                            df.columns.get_loc(display_col)
                        )

                        # ----------------------------------
                        # Total + highest share
                        # ----------------------------------

                        if is_total:

                            styles[col_position] = (
                                "font-weight: 800; "
                                "background-color: #f3f4f6; "
                                "border-top: 2px solid #460809; "
                                "border-bottom: 2px solid #460809;"
                            )

                        # ----------------------------------
                        # Low base + highest share
                        # ----------------------------------

                        elif is_low_base:

                            styles[col_position] = (
                                "color: #c0392b; "
                                "font-style: italic; "
                                "font-weight: 700;"
                            )

                        # ----------------------------------
                        # Normal + highest share
                        # ----------------------------------

                        else:

                            styles[col_position] = (
                                "font-weight: 700;"
                            )

            return styles

        # --------------------------------------------------
        # Create styled dataframe
        # --------------------------------------------------

        styled_df = (
            df.style
            .apply(
                style_profile_row,
                axis=1
            )

            # ----------------------------------------------
            # General table formatting
            # ----------------------------------------------

            .set_properties(
                **{
                    "padding": "8px 12px",
                    "vertical-align": "middle",
                    "font-size": "13px"
                }
            )

            # ----------------------------------------------
            # Centre numeric columns
            # ----------------------------------------------

            .set_properties(
                subset=[
                    "Weighted base",
                    "# Respondents"
                ] + [
                    col
                    for col in df.columns
                    if "Share" in col
                ] + (
                    ["None"]
                    if "None" in df.columns
                    else []
                ),
                **{
                    "text-align": "center"
                }
            )

            # ----------------------------------------------
            # Left align profile information
            # ----------------------------------------------

            .set_properties(
                subset=["Profile", "Group"],
                **{
                    "text-align": "left"
                }
            )

            # ----------------------------------------------
            # Add CSS class
            # ----------------------------------------------

            .set_table_attributes(
                'class="profile-analysis-table"'
            )

            .hide(axis="index")
        )

        return ui.HTML(
            styled_df.to_html(
                index=False
            )
        )


    # ======================================================
    # PROFILE SHARE CHART
    # ======================================================

    @render.plot
    def profile_share_chart():

        df = profile_analysis_df().copy()

        # --------------------------------------------------
        # Product share columns
        # --------------------------------------------------

        product_cols = [
            f"Product {p} Share"
            for p in range(1, N_PRODUCTS + 1)
        ]

        product_cols = [
            col
            for col in product_cols
            if col in df.columns
        ]

        # Include NONE only when selected
        if (
            input.show_none()
            and "NONE Share" in df.columns
        ):
            product_cols.append("NONE Share")

        # --------------------------------------------------
        # Create readable profile labels
        # --------------------------------------------------

        df["Profile label"] = (
            df["Crossbreak"].astype(str)
            + " — "
            + df["Subgroup"].astype(str)
        )

        # --------------------------------------------------
        # Reverse order so the first profile appears at
        # the top of the chart
        # --------------------------------------------------

        df = (
            df.iloc[::-1]
            .reset_index(drop=True)
        )

        # --------------------------------------------------
        # Create figure
        # --------------------------------------------------

        fig_height = max(
            4,
            len(df) * 0.2
        )

        fig, ax = plt.subplots(
            figsize=(11, fig_height)
        )

        # Alternate between template brown and template orange
        bar_colours = [
            TEMPLATE_ORANGE,
            TEMPLATE_PURPLE,
            TEMPLATE_TEAL
        ]

        # --------------------------------------------------
        # Build 100% stacked bars
        # --------------------------------------------------

        left = np.zeros(len(df))

        for col in product_cols:

            values = (
                df[col]
                .fillna(0)
                .values
            )

            label = col.replace(
                " Share",
                ""
            )

            if label == "NONE":
                label = "None"

            ax.barh(
                df["Profile label"],
                values,
                left=left,
                label=label,
                color=bar_colours[len(ax.containers) % len(bar_colours)],
                height=0.65
            )

            left += values

        # --------------------------------------------------
        # Format chart
        # --------------------------------------------------

        ax.set_xlim(0, 1)

        ax.xaxis.set_major_formatter(
            plt.FuncFormatter(
                lambda x, _: f"{x * 100:.0f}%"
            )
        )

        ax.set_xlabel(
            "Preference share"
        )

        ax.set_ylabel("")

        ax.set_title(
            "Preference share by respondent profile",
            loc="left",
            pad=15,
            fontweight="bold"
        )

        ax.legend(
            title="Product",
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
            frameon=False
        )

        # --------------------------------------------------
        # Clean chart appearance
        # --------------------------------------------------

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)

        ax.tick_params(
            axis="y",
            length=0
        )

        ax.grid(
            axis="x",
            alpha=0.2
        )

        fig.tight_layout()

        return fig





    
    # -------------------------
    # Sensitivities plots
    # -------------------------
    @reactive.Calc
    def attribute_importances_df():
        return conjoint_model.get_attribute_importances(
            respondent_ids=filtered_respondents(),
            exclude_price=input.toggle_price()
        )

    @reactive.Calc
    def level_utilities_df():
        return conjoint_model.get_level_utilities(
            respondent_ids=filtered_respondents()
        )

    @render.plot
    def level_utilities_plot():

        df = level_utilities_df()

        selected_attribute = input.selected_level_attribute()

        # ------------------------------------------------------------
        # Check that utility data exists
        # ------------------------------------------------------------

        if df is None or df.empty:
            return plot_level_utilities(
                pd.DataFrame(),
                figsize=(10, 5)
            )

        # ------------------------------------------------------------
        # Filter to selected attribute
        # ------------------------------------------------------------

        df = df[
            df["Attribute"].astype(str) == str(selected_attribute)
        ].copy()

        # ------------------------------------------------------------
        # Return plot
        # ------------------------------------------------------------

        return plot_level_utilities(
            df,
            figsize=(10, 5)
        )


    @render.plot
    def attribute_importances_plot():
        return plot_attribute_importances(attribute_importances_df())

 

    # -------------------------
    # Optimisation
    # -------------------------
    def _format_price_value(value, attr_name=None):
        currency = conjoint_model.ATTRIBUTE_CURRENCIES.get(
            attr_name, {}
        )
        symbol = currency.get("symbol", "")
        decimals = currency.get("decimals", 2)

        clean_val = str(value)
        if symbol:
            clean_val = clean_val.replace(symbol, "").strip()

        clean_val = clean_val.replace(",", "").strip()

        try:
            return f"{symbol}{float(clean_val):,.{decimals}f}"
        except (ValueError, TypeError):
            return str(value)

    def _price_to_float(value, attr_name=None):
        currency = conjoint_model.ATTRIBUTE_CURRENCIES.get(
            attr_name, {}
        )
        symbol = currency.get("symbol", "").strip()

        clean_val = str(value)
        if symbol:
            clean_val = clean_val.replace(symbol, "").strip()

        return float(clean_val.replace(",", "").strip())

    # ======================================================
    # DYNAMIC OPTIMISATION CONSTRAINTS
    # ======================================================

    def _build_optimisation_constraint_ui():
        """
        Build attribute constraint controls dynamically from
        the levels available in the Excel Grid sheet.

        Each attribute is displayed as a collapsible section.
        All levels are selected by default, meaning the
        optimiser is initially unrestricted.
        """

        controls = []

        for attr in ATTRIBUTES:

            # Get all levels tested in the conjoint design
            levels = (
                grid_df[attr]
                .dropna()
                .astype(str)
                .str.strip()
            )

            # Remove genuinely empty values
            levels = (
                levels[
                    (levels != "")
                    & (levels.str.lower() != "nan")
                ]
                .unique()
                .tolist()
            )

            controls.append(
                ui.accordion_panel(
                    attr,

                    ui.input_checkbox_group(
                        id=f"optim_constraint_{make_id(attr)}",
                        label="Allowed levels",
                        choices=levels,
                        selected=levels,
                        inline=True,
                        width="100%"
                    )
                )
            )

        return ui.accordion(
            *controls,
            open=False,
            multiple=True,
            class_="optimisation-constraints-accordion"
        )

    @output
    @render.ui
    def copy_optimisation_button():

        try:
            res = optimisation_results()

        except SilentException:
            # No optimisation has been run yet
            return ui.div()

        # Hide the button if optimisation failed
        if res is None or "error" in res:
            return ui.div()

        # Show the button after successful optimisation
        return ui.tags.button(
            "Copy data to clipboard",
            id="copy_optimisation",
            class_="btn btn-sm btn-outline-secondary"

        )

    


    @render.ui
    def optimisation_constraints():
        """
        Render the dynamic optimisation constraint controls.
        """
        return _build_optimisation_constraint_ui()





    def _get_best_level_by_utility(attr, level_utils_df):
        """
        Return the highest-utility level for an attribute, subject to
        the levels allowed by the optimisation constraints.

        If all levels are selected, this behaves exactly like the
        original optimiser.

        If specific levels are selected, only those levels are
        considered.
        """

        # Get utilities for this attribute
        df_attr = level_utils_df[
            level_utils_df["Attribute"] == attr
        ].copy()

        # If there are no utility estimates, fall back to the
        # first level in the Excel Grid
        if df_attr.empty:
            return grid_df[attr].iloc[0]

        # --------------------------------------------------
        # Get the levels allowed by the user
        # --------------------------------------------------
        constraint_id = f"optim_constraint_{make_id(attr)}"

        try:
            allowed_levels = input[constraint_id]()
        except Exception:
            allowed_levels = None

        # --------------------------------------------------
        # If the constraint isn't available, or nothing has
        # been selected, retain the original behaviour.
        # --------------------------------------------------
        if allowed_levels is None:
            allowed_levels = []

        allowed_levels = [
            str(x).strip()
            for x in allowed_levels
        ]

        # If ALL levels are selected, no filtering is needed
        if len(allowed_levels) > 0:

            df_attr["_level_str"] = (
                df_attr["Level"]
                .astype(str)
                .str.strip()
            )

            df_attr = df_attr[
                df_attr["_level_str"].isin(allowed_levels)
            ]

        # --------------------------------------------------
        # Safety check
        # --------------------------------------------------
        # If the filtering leaves us with no valid levels,
        # fall back to the first available level rather than
        # allowing the optimiser to crash.
        if df_attr.empty:

            original_df = level_utils_df[
                level_utils_df["Attribute"] == attr
            ].copy()

            if not original_df.empty:
                return original_df.iloc[0]["Level"]

            return grid_df[attr].iloc[0]

        # --------------------------------------------------
        # Select the highest-utility allowed level
        # --------------------------------------------------
        return df_attr.loc[
            df_attr["Utility"].idxmax(),
            "Level"
        ]

    def _validate_optimisation_constraints():
        """
        Validate that the user has selected at least one level
        for every optimisable attribute.
        """

        for attr in ATTRIBUTES:

            # All price attributes are handled separately
            if attr in PRICE_ATTRS:
                continue

            constraint_id = (
                f"optim_constraint_{make_id(attr)}"
            )

            try:
                selected_levels = input[constraint_id]()
            except Exception:
                continue

            if not selected_levels:

                return (
                    f"Please select at least one level for "
                    f"<b>{attr}</b> before running the optimisation."
                )

        return None

    

    def _configuration_satisfies_restrictions(product_row):
        """
        Check whether a proposed product configuration satisfies
        the Excel Restrictions sheet.

        Important:
        If a restriction says:

            Connecting Flight = No
            Then Attribute B = Layover Time
            Level.1 = All
            Action = forbid

        this means Layover Time is NOT APPLICABLE when there is
        no connecting flight.

        It does NOT mean the entire configuration is invalid.

        Therefore, "All" restrictions are treated as conditional
        display / applicability rules rather than hard restrictions.
        """

        if restrictions_df.empty:
            return True

        for _, r in restrictions_df.iterrows():

            attr_a = clean_attr(r["If Attribute A"])
            level_a = str(r["Level"]).strip()

            attr_b = clean_attr(r["Then Attribute B"])

            action = str(
                r.get("Action", "")
            ).strip().lower()

            restricted_level = str(
                r.get("Level.1", "")
            ).strip()

            # Make sure both attributes exist
            if attr_a not in product_row.index:
                continue

            if attr_b not in product_row.index:
                continue

            value_a = str(
                product_row[attr_a]
            ).strip()

            value_b = str(
                product_row[attr_b]
            ).strip()

            # Restriction only applies when A matches
            if value_a != level_a:
                continue

            # --------------------------------------------------
            # "ALL" = attribute B is not applicable
            # --------------------------------------------------
            if (
                action == "forbid"
                and restricted_level.lower() == "all"
            ):

                # This is a display/applicability rule.
                #
                # Example:
                # Connecting Flight = No
                # -> Layover Time is not shown.
                #
                # It should NOT invalidate the configuration.
                continue

            # --------------------------------------------------
            # Specific level restriction
            # --------------------------------------------------
            if action == "forbid":

                if value_b == restricted_level:
                    return False

        return True

    
    
    
    def _exhaustive_optimised_row(
        product_id,
        current_products_df,
        objective="Share",
        progress=None,
        optimise_price=True,
    ):
        """
        Exhaustively evaluate valid product configurations.

        Respects:
        - Selected attribute constraints
        - Excel Restrictions
        - Fixed and optimised price settings
        - Respondent weights from the Filters sheet

        Objectives:
        - Share: maximise weighted preference share
        - Revenue: maximise weighted preference share
        * combined price * units sold
        """

        from itertools import product as cartesian_product

        print("\n========== EXHAUSTIVE OPTIMISATION ==========")

        current_row = current_products_df.loc[
            current_products_df["ProductID"] == product_id
        ].iloc[0].copy()

        # --------------------------------------------------
        # GET FILTERED RESPONDENTS AND THEIR WEIGHTS
        # --------------------------------------------------
        respondent_data = filtered_data()

        respondent_ids = respondent_data["Respondent"].tolist()

        respondent_weights = respondent_data.set_index(
            "Respondent"
        )["Weight"]

        include_none = input.show_none()

        if respondent_data.empty:
            print("No respondents selected for optimisation.")
            return None

        # Prepare utilities once before evaluating combinations.
        evaluate_candidate = conjoint_model.prepare_share_evaluator(
            current_products_df,
            respondent_ids=respondent_ids,
            include_none=include_none,
            respondent_weights=respondent_weights,
        )

        # --------------------------------------------------
        # BUILD ALLOWED NON-PRICE ATTRIBUTE LEVELS
        # --------------------------------------------------
        candidate_levels = {}

        for attr in ATTRIBUTES:

            if attr in PRICE_ATTRS:
                continue

            constraint_id = f"optim_constraint_{make_id(attr)}"

            try:
                allowed_levels = input[constraint_id]()
            except Exception:
                allowed_levels = None

            levels = grid_df[attr].dropna().tolist()

            if allowed_levels:
                allowed_set = {str(x).strip() for x in allowed_levels}

                levels = [
                    level for level in levels
                    if str(level).strip() in allowed_set
                ]

            # Remove duplicates while preserving order.
            levels = list(dict.fromkeys(levels))

            if not levels:
                print(f"No candidate levels available for {attr}")
                return None

            candidate_levels[attr] = levels

        non_price_attrs = [
            attr for attr in ATTRIBUTES
            if attr not in PRICE_ATTRS
        ]

        # --------------------------------------------------
        # BUILD CANDIDATE PRICE LEVELS
        # --------------------------------------------------
        price_options = {}

        for attr in PRICE_ATTRS:

            current_price = _price_to_float(current_row[attr])

            if not optimise_price:
                price_options[attr] = [current_price]
                continue

            attr_id = make_id(attr)

            try:
                mode = input[f"price_mode_{attr_id}"]()
            except Exception:
                mode = "optimise"

            try:
                fixed_value = input[f"fixed_price_{attr_id}"]()
            except Exception:
                fixed_value = None

            if mode == "fixed":

                fixed_price = (
                    current_price
                    if fixed_value is None
                    else float(fixed_value)
                )

                price_options[attr] = [fixed_price]
                continue

            tested_prices = sorted({
                _price_to_float(value)
                for value in grid_df[attr].dropna()
                if pd.notna(_price_to_float(value))
            })

            if not tested_prices:
                price_options[attr] = [current_price]
                continue

            if len(tested_prices) == 1:
                price_options[attr] = tested_prices
                continue

            # Keep the existing price-search interval:
            # one tenth of the smallest interval tested in Excel.
            differences = [
                tested_prices[i + 1] - tested_prices[i]
                for i in range(len(tested_prices) - 1)
                if tested_prices[i + 1] > tested_prices[i]
            ]

            step = min(differences) / 10

            min_price = tested_prices[0]
            max_price = tested_prices[-1]

            candidates = np.arange(
                min_price,
                max_price + step * 0.5,
                step,
            )

            price_options[attr] = sorted(set(
                [
                    round(float(price), 10)
                    for price in candidates
                    if min_price <= price <= max_price
                ] + [min_price, max_price]
            ))

        # --------------------------------------------------
        # GENERATE EXHAUSTIVE COMBINATIONS
        # --------------------------------------------------
        non_price_combinations = list(
            cartesian_product(
                *(candidate_levels[attr] for attr in non_price_attrs)
            )
        )

        price_combinations = (
            list(
                cartesian_product(
                    *(price_options[attr] for attr in PRICE_ATTRS)
                )
            )
            if PRICE_ATTRS
            else [()]
        )

        total = (
            len(non_price_combinations)
            * len(price_combinations)
        )

        print("Non-price combinations:", len(non_price_combinations))
        print("Price combinations:", len(price_combinations))
        print("TOTAL COMBINATIONS:", total)

        if total == 0:
            return None

        # --------------------------------------------------
        # EVALUATE EVERY COMPLETE CONFIGURATION
        # --------------------------------------------------
        best_score = -np.inf
        best_candidate = None
        tested = 0

        # Diagnostics: track which combinations are actually evaluated.
        valid_count = 0
        restriction_rejections = 0

        try:
            units_sold = float(input.units_sold() or 500)
        except Exception:
            units_sold = 500

        for non_price_values in non_price_combinations:

            candidate = current_row.copy()

            for attr, value in zip(
                non_price_attrs,
                non_price_values,
            ):
                candidate[attr] = value

            for price_values in price_combinations:

                tested += 1

                for attr, value in zip(PRICE_ATTRS, price_values):
                    candidate[attr] = value

                # Check complete configuration against Excel restrictions.
                if not _configuration_satisfies_restrictions(candidate):
                    restriction_rejections += 1
                    continue

                valid_count += 1

                product_share = evaluate_candidate(
                    candidate,
                    product_id,
                )

                if objective == "Revenue":

                    combined_price = sum(
                        _price_to_float(candidate[attr])
                        for attr in PRICE_ATTRS
                    )

                    score = (
                        product_share
                        * combined_price
                        * units_sold
                    )

                else:
                    score = product_share

                if score > best_score:
                    best_score = score
                    best_candidate = candidate.copy()

                if progress is not None and (
                    tested % 10 == 0 or tested == total
                ):
                    progress.set(
                        20 + 75 * tested / total,
                        message=(
                            f"Exhaustive search: testing "
                            f"{tested:,} of {total:,} combinations"
                        ),
                    )

        print("Total combinations:", total)
        print("Combinations tested:", tested)
        print("Rejected by restrictions:", restriction_rejections)
        print("Valid configurations evaluated:", valid_count)
        print("Best share:", best_score)

        print(
            "Best configuration:",
            {
                attr: best_candidate[attr]
                for attr in ATTRIBUTES
            } if best_candidate is not None else None
        )
        print("=============================================\n")

        
        if best_candidate is None:
            return None

        # --------------------------------------------------
        # DIAGNOSTIC: COMPARE FAST AND ORIGINAL SHARE CALCULATIONS
        # --------------------------------------------------
        best_products = current_products_df.copy()

        best_mask = best_products["ProductID"] == product_id

        for attr in ATTRIBUTES:
            best_products.loc[best_mask, attr] = best_candidate[attr]

        original_shares = conjoint_model.compute_shares(
            best_products,
            respondent_ids=respondent_ids,
            include_none=include_none,
            respondent_weights=respondent_weights,
        )

        original_share = original_shares.loc[
            original_shares["ProductID"] == product_id,
            "PrefShare",
        ].sum()

        # Diagnostic only: compare with equal respondent weights.
        unweighted_shares = conjoint_model.compute_shares(
            best_products,
            respondent_ids=respondent_ids,
            include_none=include_none,
            respondent_weights=None,
        )

        unweighted_share = unweighted_shares.loc[
            unweighted_shares["ProductID"] == product_id,
            "PrefShare",
        ].sum()

        print(f"Weighted share:   {original_share * 100:.6f}%")
        print(f"Unweighted share: {unweighted_share * 100:.6f}%")
        print(f"NONE included:    {include_none}")

        print("\n========== SHARE CALCULATION COMPARISON ==========")
        print(f"Fast evaluator share: {best_score * 100:.6f}%")
        print(f"Original compute_shares: {original_share * 100:.6f}%")
        print(f"Difference: {(best_score - original_share) * 100:.6f} percentage points")
        print("==================================================\n")

        return best_candidate




    def _build_share_optimised_row(
        product_id,
        current_row=None,
        current_products_df=None,
        progress=None,
        optimise_price=True,
    ):
        """Find the globally best valid configuration for preference share."""

        if current_products_df is None:
            return None

        return _exhaustive_optimised_row(
            product_id=product_id,
            current_products_df=current_products_df,
            objective="Share",
            progress=progress,
            optimise_price=optimise_price,
        )



    
    def _build_revenue_optimised_row(
        product_id,
        current_products_df,
        progress=None,
    ):
        """Find the globally best valid configuration for revenue."""

        return _exhaustive_optimised_row(
            product_id=product_id,
            current_products_df=current_products_df,
            objective="Revenue",
            progress=progress,
            optimise_price=True,
        )


    
    def _metric_for_products(products, objective, scope, product_id):

        shares = conjoint_model.compute_shares(
            products,
            respondent_ids=filtered_respondents(),
            include_none=input.show_none()
        )

        # --------------------------------------------------
        # Preference share
        # --------------------------------------------------
        if objective == "Share":

            if scope == "Portfolio":
                metric = shares.loc[
                    shares["ProductID"] != "NONE",
                    "PrefShare"
                ].sum() * 100

                return metric, "Portfolio preference share (%)"

            product_share = shares.loc[
                shares["ProductID"] == product_id,
                "PrefShare"
            ].sum() * 100

            return product_share, "Product preference share (%)"

        # --------------------------------------------------
        # Revenue: preference share × combined price
        # --------------------------------------------------
        product_rows = products.copy()

        # Convert every price attribute to numeric values
        for attr in PRICE_ATTRS:
            product_rows[attr] = product_rows[attr].apply(
                lambda value: _price_to_float(value, attr)
            )

        # Calculate combined price across all price attributes
        if PRICE_ATTRS:
            product_rows["CombinedPrice"] = product_rows[
                PRICE_ATTRS
            ].sum(axis=1)
        else:
            product_rows["CombinedPrice"] = 0.0

        shares_no_none = shares.loc[
            shares["ProductID"] != "NONE",
            ["ProductID", "PrefShare"]
        ].copy()

        revenue_df = shares_no_none.merge(
            product_rows[["ProductID", "CombinedPrice"]],
            on="ProductID",
            how="left"
        )

        units_sold = input.units_sold()

        revenue_df["Revenue"] = (
            units_sold
            * revenue_df["PrefShare"]
            * revenue_df["CombinedPrice"]
        )

        # --------------------------------------------------
        # Return portfolio or selected-product revenue
        # --------------------------------------------------
        if scope == "Portfolio":
            metric = revenue_df["Revenue"].sum()

            return metric, "Portfolio revenue"

        metric = revenue_df.loc[
            revenue_df["ProductID"] == product_id,
            "Revenue"
        ].sum()

        return metric, "Product revenue"

    

    

    
    @reactive.Calc
    @reactive.event(input.run_optim, ignore_none=True)
    def optimisation_results():

        print("1. OPTIMISATION STARTED")

        with ui.Progress(min=0, max=100) as progress:

            progress.set(
                0,
                message="Starting optimisation..."
            )

            print("2. PROGRESS STARTED")

            # --------------------------------------------------
            # Validate optimisation constraints
            # --------------------------------------------------
            validation_error = _validate_optimisation_constraints()
            print("3. VALIDATION:", validation_error)

            if validation_error is not None:
                return {
                    "error": validation_error
                }
            print("4. PASSED FIRST VALIDATION CHECK")

            # --------------------------------------------------
            # Validate optimisation constraints
            # --------------------------------------------------
            validation_error = _validate_optimisation_constraints()

            if validation_error is not None:
                return {
                    "error": validation_error
                }

            print("5. STARTING PRICE VALIDATION", PRICE_ATTRS)
            
            # --------------------------------------------------
            # Validate each price attribute independently
            # --------------------------------------------------
            """ for attr in PRICE_ATTRS:

                print("5a. CHECKING PRICE ATTRIBUTE:", attr)

                attr_id = make_id(attr)
                print("5b. ATTRIBUTE ID:", attr_id)

                
                try:
                    print("5b1. READING PRICE MODE INPUT:", f"price_mode_{attr_id}")
                    try:
                        mode = input[f"price_mode_{attr_id}"]()
                    except Exception as e:
                        print("PRICE MODE INPUT ERROR:", repr(e))
                        print("PRICE MODE INPUT ID:", f"price_mode_{attr_id}")
                        print("PRICE ATTRIBUTES:", PRICE_ATTRS)
                        raise
                    print("5b2. PRICE MODE VALUE:", mode)
                except Exception as e:
                    print("ERROR READING PRICE MODE:", repr(e))
                    raise

                try:
                    print("5b3. READING FIXED PRICE INPUT:", f"fixed_price_{attr_id}")
                    fixed_value = input[f"fixed_price_{attr_id}"]()
                    print("5b4. FIXED PRICE VALUE:", fixed_value)
                except Exception as e:
                    print("ERROR READING FIXED PRICE:", repr(e))
                    raise

                print("5c. PRICE MODE:", mode)
                print("5d. FIXED VALUE:", fixed_value)

                # Only validate prices explicitly set to fixed
                if mode != "fixed":
                    continue

                try:
                    fixed_price = float(fixed_value)
                except (TypeError, ValueError):
                    return {
                        "error": (
                            f"Please enter a valid fixed price "
                            f"for <b>{attr}</b>."
                        )
                    }

                price_range = conjoint_model.PRICE_RANGES.get(attr)

                if price_range is None:
                    return {
                        "error": (
                            f"Could not determine the allowed price range "
                            f"for <b>{attr}</b> from the Excel Grid."
                        )
                    }

                min_price = price_range["min"]
                max_price = price_range["max"]

                if not min_price <= fixed_price <= max_price:
                    currency = conjoint_model.ATTRIBUTE_CURRENCIES.get(
                        attr, {}
                    )
                    symbol = currency.get("symbol", "")
                    decimals = currency.get("decimals", 2)

                    return {
                        "error": (
                            f"Fixed price for <b>{attr}</b> must be "
                            f"between {symbol}{min_price:,.{decimals}f} "
                            f"and {symbol}{max_price:,.{decimals}f}."
                        )
                    }

            print("6. PRICE VALIDATION COMPLETE") """
            # --------------------------------------------------
            # Get optimisation settings
            # --------------------------------------------------
            objective = input.optim_objective()
            scope = "Product vs competitors"

            scenario = f"{objective} optimisation: {scope}"

            # --------------------------------------------------
            # Get current product configuration
            # --------------------------------------------------
            current_products = products_df().copy()

            if current_products.empty:
                return {
                    "error": (
                        "No products are included. Please include a "
                        "product on the Simulator tab before optimising."
                    )
                }

            # Normalise product IDs so 2 and "2" match consistently.
            numeric_ids = pd.to_numeric(
                current_products["ProductID"],
                errors="coerce"
            )

            if numeric_ids.isna().any():
                return {
                    "error": (
                        "Some product IDs are invalid. "
                        "ProductID must contain numeric product numbers."
                    )
                }

            current_products["ProductID"] = numeric_ids.astype(int)

            # --------------------------------------------------
            # Read the product selected for this run
            # --------------------------------------------------
            raw_selection = input.optim_product()

            print("\n========== OPTIMISER SELECTION ==========")
            print("Run button:", input.run_optim())
            print("Dropdown value:", repr(raw_selection))
            print(
                "Available product IDs:",
                current_products["ProductID"].tolist()
            )

            if raw_selection is None or str(raw_selection).strip() == "":
                return {
                    "error": "Please select a product to optimise."
                }

            try:
                selected_product = int(
                    str(raw_selection).strip().removeprefix("Product ").strip()
                )
            except (TypeError, ValueError):
                print("ERROR: Could not parse the product selection.")
                return {
                    "error": (
                        "The selected product could not be recognised. "
                        "Please select it again."
                    )
                }

            if selected_product not in current_products["ProductID"].tolist():
                print("ERROR: Selected product is not included.")
                return {
                    "error": (
                        f"Product {selected_product} is not included "
                        "in the current simulator configuration."
                    )
                }

            print("Product actually used:", selected_product)
            print("========================================\n")

            # --------------------------------------------------
            # Start with current configuration
            # --------------------------------------------------
            optimised_products = current_products.copy()

            # ==================================================
            # PORTFOLIO OPTIMISATION
            # ==================================================
            if scope == "Portfolio":

                for product_id in optimised_products["ProductID"].tolist():

                    current_row = optimised_products.loc[
                        optimised_products["ProductID"] == product_id
                    ].iloc[0]

                    # ------------------------------------------
                    # Build optimised configuration
                    # ------------------------------------------
                    if objective == "Revenue":

                        optim_row = _build_revenue_optimised_row(
                            product_id=product_id,
                            current_products_df=optimised_products,
                            progress =progress
                        )

                    else:

                        optim_row = _build_share_optimised_row(
                            product_id=product_id,
                            current_row=current_row,
                            current_products_df=optimised_products,
                            progress =progress
                        )

                    # ------------------------------------------
                    # Check for no valid configuration
                    # ------------------------------------------
                    if optim_row is None:

                        return {
                            "error": (
                                f"No valid configuration could be found "
                                f"for Product {product_id} using the selected "
                                f"constraints and restrictions. "
                                f"Please allow additional attribute levels."
                            )
                        }

                    # ------------------------------------------
                    # Apply optimised configuration
                    # ------------------------------------------
                    for attr in ATTRIBUTES:

                        optimised_products[attr] = (
                            optimised_products[attr].astype(object)
                        )

                        optimised_products.loc[
                            optimised_products["ProductID"] == product_id,
                            attr
                        ] = optim_row[attr]

            # ==================================================
            # PRODUCT VS COMPETITORS OPTIMISATION
            # ==================================================
            else:

                current_row = current_products.loc[
                    current_products["ProductID"] == selected_product
                ].iloc[0]

                print("CALLING OPTIMISATION HELPER")

                try:
                    print(
                        f"Starting exhaustive optimisation | "
                        f"Objective={objective} | "
                        f"Product={selected_product}"
                    )

                    if objective == "Revenue":
                        optim_row = _build_revenue_optimised_row(
                            product_id=selected_product,
                            current_products_df=current_products,
                            progress=progress
                        )
                    else:
                        optim_row = _build_share_optimised_row(
                            product_id=selected_product,
                            current_row=current_row,
                            current_products_df=current_products,
                            progress=progress
                        )

                    print("Exhaustive optimisation returned:", optim_row)

                except Exception as e:
                    traceback.print_exc()

                    return {
                        "error": (
                            "Optimisation failed: "
                            f"{type(e).__name__}: {e}"
                        )
                    }

                

                # ----------------------------------------------
                # Check for no valid configuration
                # ----------------------------------------------
                if optim_row is None:

                    return {
                        "error": (
                            f"No valid configuration could be found "
                            f"for Product {selected_product} using the "
                            f"selected constraints and restrictions. "
                            f"Please allow additional attribute levels."
                        )
                    }

                # ----------------------------------------------
                # Apply optimised configuration
                # ----------------------------------------------
                for attr in ATTRIBUTES:

                    optimised_products[attr] = (
                        optimised_products[attr].astype(object)
                    )

                    optimised_products.loc[
                        optimised_products["ProductID"] == selected_product,
                        attr
                    ] = optim_row[attr]


                progress.set(
                    92,
                    message="Calculating final impact..."
                )

            # ==================================================
            # CALCULATE CURRENT PERFORMANCE
            # ==================================================
            current_metric, metric_label = _metric_for_products(
                current_products,
                objective=objective,
                scope=scope,
                product_id=selected_product
            )

            progress.set(
                98,
                message="Finalising optimisation..."
            )

            # ==================================================
            # CALCULATE OPTIMISED PERFORMANCE
            # ==================================================
            optimised_metric, _ = _metric_for_products(
                optimised_products,
                objective=objective,
                scope=scope,
                product_id=selected_product
            )

            # ==================================================
            # CALCULATE INCREMENTAL CHANGE
            # ==================================================
            incremental_metric = (
                optimised_metric - current_metric
            )

            print("\n========== SHARE OPTIMISATION DEBUG ==========")
            print("Objective:", objective)
            print("Current metric:", current_metric)
            print("Optimised metric:", optimised_metric)
            print("Change:", incremental_metric)
            print("\nCurrent product configuration:")
            print(current_products)
            print("\nOptimised product configuration:")
            print(optimised_products)
            print("==============================================\n")

            progress.set(
                100,
                message="Optimisation complete"
            )
            # ==================================================
            # RETURN RESULTS
            # ==================================================
            return {
                "objective": objective,
                "scope": scope,
                "scenario": scenario,
                "selected_product": selected_product,
                "current_products": current_products,
                "optimised_products": optimised_products,
                "current_metric": current_metric,
                "optimised_metric": optimised_metric,
                "incremental_metric": incremental_metric,
                "metric_label": metric_label
            }
    
    @reactive.Effect
    @reactive.event(input.reset_optim)
    def reset_optimisation_controls():
        ui.update_select("optim_objective", selected="Share")

        ui.update_numeric("units_sold", value=500)

        for attr in PRICE_ATTRS:
            attr_id = make_id(attr)

            ui.update_radio_buttons(
                f"price_mode_{attr_id}",
                selected="optimise"
            )

    
    @output
    @render.ui
    def best_product_table():

        res = optimisation_results()

        print("\n========== OPTIMISATION RESULT ==========")
        print(res)
        print("=========================================\n")

        # --------------------------------------------------
        # Handle optimisation error
        # --------------------------------------------------

        if "error" in res:

            return ui.div(
                ui.HTML(
                    f"""
                    <div style="
                        padding: 15px;
                        margin: 10px;
                        border: 1px solid #f5c2c7;
                        background-color: #f8d7da;
                        color: #842029;
                        border-radius: 6px;
                    ">
                        ⚠️ {res["error"]}
                    </div>
                    """
                )
            )

        # --------------------------------------------------
        # Get optimisation results
        # --------------------------------------------------

        scope = res["scope"]
        selected_product = res["selected_product"]

        current_products = res["current_products"]
        optimised_products = res["optimised_products"]

        

        # --------------------------------------------------
        # Determine which products to show
        # --------------------------------------------------

        if scope == "Portfolio":

            product_ids_to_show = (
                optimised_products["ProductID"].tolist()
            )

        else:

            product_ids_to_show = [selected_product]

         # TEMP DEBUG: Check original vs optimised prices
        print("\n--- PRICE COMPARISON DEBUG ---")

        for attr in PRICE_ATTRS:
            print(f"\n{attr}")

            for product_id in product_ids_to_show:
                current_value = current_products.loc[
                    current_products["ProductID"] == product_id, attr
                ].iloc[0]

                optimised_value = optimised_products.loc[
                    optimised_products["ProductID"] == product_id, attr
                ].iloc[0]

                print(
                    f"Product {product_id}: "
                    f"Original={current_value!r}, "
                    f"Optimised={optimised_value!r}"
                )

        print("------------------------------\n")

            

        # --------------------------------------------------
        # Build table data
        # --------------------------------------------------

        data = []

        for product_id in product_ids_to_show:

            current_row = current_products.loc[
                current_products["ProductID"] == product_id
            ].iloc[0]

            optim_row = optimised_products.loc[
                optimised_products["ProductID"] == product_id
            ].iloc[0]

            for attr in ATTRIBUTES:

                cur_val = current_row[attr]
                opt_val = optim_row[attr]

                # Format price consistently
                if attr in PRICE_ATTRS:

                    cur_val_str = _format_price_value(cur_val)
                    opt_val_str = _format_price_value(opt_val)

                else:
                    cur_val_str = str(cur_val)
                    opt_val_str = str(opt_val)

                if attr in PRICE_ATTRS:
                    changed = not np.isclose(
                        _price_to_float(cur_val),
                        _price_to_float(opt_val),
                        atol=1e-6
                    )
                else:
                    changed = cur_val_str != opt_val_str

                data.append(
                    {
                        "Product": f"Product {product_id}",
                        "Attribute": attr,
                        "Original": cur_val_str,
                        "Optimised": opt_val_str,
                        "Changed": changed
                    }
                )

        # --------------------------------------------------
        # Create dataframe
        # --------------------------------------------------

        df = pd.DataFrame(data)

        from html import escape

        # --------------------------------------------------
        # Build HTML table rows
        # --------------------------------------------------

        table_rows = []

        for _, row in df.iterrows():

            changed = row["Changed"]

            row_class = (
                "optimised-changed-row"
                if changed
                else ""
            )

            optimised_class = (
                "optimised-changed-value"
                if changed
                else ""
            )

            table_rows.append(
                f"""
                <tr class="{row_class}">

                    <td>
                        {escape(str(row["Product"]))}
                    </td>

                    <td>
                        {escape(str(row["Attribute"]))}
                    </td>

                    <td>
                        {escape(str(row["Original"]))}
                    </td>

                    <td class="{optimised_class}">
                        {escape(str(row["Optimised"]))}
                    </td>

                </tr>
                """
            )

        # --------------------------------------------------
        # Render table only
        # --------------------------------------------------

        table_html = f"""
        <div class="optimised-table-container">

            <table class="table optimised-comparison-table">

                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Attribute</th>
                        <th>Original</th>
                        <th>Optimised</th>
                    </tr>
                </thead>

                <tbody>
                    {"".join(table_rows)}
                </tbody>

            </table>

        </div>
        """

        return ui.HTML(table_html)

    @render.text
    def optimisation_clipboard_data():

        res = optimisation_results()

        # --------------------------------------------------
        # Handle optimisation error
        # --------------------------------------------------

        if "error" in res:
            return f"Optimisation error:\t{res['error']}"

        # --------------------------------------------------
        # Get optimisation results
        # --------------------------------------------------

        scope = res["scope"]
        selected_product = res["selected_product"]

        current_products = res["current_products"]
        optimised_products = res["optimised_products"]

        # --------------------------------------------------
        # Determine which products to show
        # --------------------------------------------------

        if scope == "Portfolio":
            product_ids_to_show = (
                optimised_products["ProductID"].tolist()
            )
        else:
            product_ids_to_show = [selected_product]

        # --------------------------------------------------
        # Build table data
        # --------------------------------------------------

        data = []

        for product_id in product_ids_to_show:

            current_row = current_products.loc[
                current_products["ProductID"] == product_id
            ].iloc[0]

            optim_row = optimised_products.loc[
                optimised_products["ProductID"] == product_id
            ].iloc[0]

            for attr in ATTRIBUTES:

                cur_val = current_row[attr]
                opt_val = optim_row[attr]

                # Format price consistently
                if attr in PRICE_ATTRS:

                    cur_val_str = _format_price_value(
                        cur_val
                    )

                    opt_val_str = _format_price_value(
                        opt_val
                    )

                else:

                    cur_val_str = str(cur_val)
                    opt_val_str = str(opt_val)

                changed = (
                    cur_val_str != opt_val_str
                )

                data.append({
                    "Product": f"Product {product_id}",
                    "Attribute": attr,
                    "Original": cur_val_str,
                    "Optimised": opt_val_str,
                    "Status": "Updated" if changed else ""
                })

        # --------------------------------------------------
        # Convert to dataframe
        # --------------------------------------------------

        df = pd.DataFrame(data)

        # --------------------------------------------------
        # Convert to tab-separated text
        # --------------------------------------------------

        return df.to_csv(
            sep="\t",
            index=False
        )

    @render.ui
    def optim_config_summary_text():

        res = optimisation_results()

        if "error" in res:
            return ui.HTML(
                f"""
                <div style="
                    padding: 15px;
                    margin: 10px;
                    border: 1px solid #f5c2c7;
                    background-color: #f8d7da;
                    color: #842029;
                    border-radius: 6px;
                ">
                    ⚠️ {res["error"]}
                </div>
                """
            )
        
        current_products = res["current_products"]
        optimised_products = res["optimised_products"]
        scope = res["scope"]
        selected_product = res["selected_product"]
        
        if scope == "Portfolio":
            product_ids_to_show = optimised_products["ProductID"].tolist()
        else:
            product_ids_to_show = [selected_product]

        changes_count = 0
        changed_attrs = []
        
        for product_id in product_ids_to_show:
            current_row = current_products.loc[current_products["ProductID"] == product_id].iloc[0]
            optim_row = optimised_products.loc[optimised_products["ProductID"] == product_id].iloc[0]
            
            for attr in ATTRIBUTES:

                cur_val = current_row[attr]
                opt_val = optim_row[attr]

                if attr in PRICE_ATTRS:

                    # Compare prices numerically, not as formatted strings
                    cur_num = _price_to_float(cur_val)
                    opt_num = _price_to_float(opt_val)

                    changed = (
                        pd.notna(cur_num)
                        and pd.notna(opt_num)
                        and not np.isclose(
                            float(cur_num),
                            float(opt_num),
                            atol=1e-6
                        )
                    )

                else:

                    changed = str(cur_val) != str(opt_val)

                if changed:
                    changes_count += 1

                    if attr not in changed_attrs:
                        changed_attrs.append(attr)
                        
        if changes_count == 0:

            return ui.div(

                ui.span(
                    icon_svg("wand-magic-sparkles"),
                    class_="purple-wand-icon",
                    style="""
                        font-size: 1.1rem;
                        margin-right: 8px;
                        flex-shrink: 0;
                    """
                ),

                ui.HTML(
                    "<span>"
                    "The original configuration is already perfectly aligned with this objective. "
                    "<b>No attributes were changed.</b>"
                    "</span>"
                ),

                style="""
                    font-size: 0.95rem;
                    display: flex;
                    align-items: flex-start;
                """
            )
            
        attr_str = ", ".join([f"<b>{a}</b>" for a in changed_attrs])
        
        return ui.div(
            ui.span(
                icon_svg("wand-magic-sparkles"),
                class_="purple-wand-icon",
                style="""
                    font-size: 1.1rem;
                    margin-right: 8px;
                    flex-shrink: 0;
                """
            ),

            ui.HTML(
                f"<span>"
                f"The optimiser made <b>{changes_count} adjustments</b> to the original "
                f"configuration to maximise {res.get('objective', 'Share').lower()}. "
                f"Modifications were applied to: {attr_str}."
                f"</span>"
            ),

            style="""
                font-size: 0.95rem;
                display: flex;
                align-items: flex-start;
            """
        )
    
    @render.plot
    def optim_plot():

        res = optimisation_results()

        if "error" in res:
            return None

        current_metric = res["current_metric"]
        optimised_metric = res["optimised_metric"]
        incremental_metric = res["incremental_metric"]
        metric_label = res["metric_label"]

        # Detect the currency used by the price attributes
        currency = (
            conjoint_model.ATTRIBUTE_CURRENCIES.get(
                PRICE_ATTRS[0], {}
            )
            if PRICE_ATTRS
            else {}
        )
        currency_symbol = currency.get("symbol", "")
        currency_decimals = currency.get("decimals", 2)

        if res.get("objective") == "Revenue":
            metric_label = "Revenue"

        # ==================================================
        # FIGURE SETUP
        # ==================================================

        fig, ax = plt.subplots(figsize=(6.5, 4.5))

        x = [0, 1]
        width = 0.42

        # Green for an improvement, red for a reduction
        optimised_colour = (
            "#28A745"
            if incremental_metric >= 0
            else "#DC3545"
        )

        # ==================================================
        # BARS
        # ==================================================

        # Original value
        ax.bar(
            x[0],
            current_metric,
            color="#858484",
            width=width,
            zorder=2
        )

        # Optimised value
        ax.bar(
            x[1],
            optimised_metric,
            color=optimised_colour,
            width=width,
            zorder=2
        )

        # ==================================================
        # AXIS LABELS AND TITLE
        # ==================================================

        ax.set_xticks(x)
        ax.set_xticklabels(
            ["Original", "Optimised"],
            fontsize=10
        )

        ax.set_ylabel(metric_label)

        short_scope = (
            "Product"
            if res["scope"] == "Product vs competitors"
            else "Portfolio"
        )

        ax.set_title(
            f"{res['objective']} optimisation: {short_scope}",
            pad=15,
            fontsize=12,
            fontweight="bold"
        )

        # ==================================================
        # VALUE LABELS
        # ==================================================

        if metric_label.endswith("(%)"):

            ax.yaxis.set_major_locator(
                mticker.MultipleLocator(5)
            )

            current_label = f"{current_metric:.2f}%"
            optimised_label = f"{optimised_metric:.2f}%"
            incremental_label = f"{incremental_metric:+.2f} pts"

        else:

            if res.get("objective") == "Revenue":

                decimals = 0 if currency_decimals == 0 else 0

                current_label = (
                    f"{currency_symbol}"
                    f"{current_metric:,.{decimals}f}"
                )
                optimised_label = (
                    f"{currency_symbol}"
                    f"{optimised_metric:,.{decimals}f}"
                )

                incremental_sign = (
                    "+" if incremental_metric >= 0 else "-"
                )

                incremental_label = (
                    f"{incremental_sign}{currency_symbol}"
                    f"{abs(incremental_metric):,.{decimals}f}"
                )

            else:

                current_label = f"{current_metric:.2f}"
                optimised_label = f"{optimised_metric:.2f}"
                incremental_label = f"{incremental_metric:+.2f}"

        # ==================================================
        # Y-AXIS LIMITS
        # ==================================================

        max_value = max(
            current_metric,
            optimised_metric,
            0
        )

        if max_value == 0:

            upper_lim = 1

        elif metric_label.endswith("(%)"):

            # Leave room for the value labels and impact annotation
            upper_lim = math.ceil(
                (max_value + 8) / 5
            ) * 5

        else:

            # Leave space above the bars
            upper_lim = max_value * 1.25

        ax.set_ylim(0, upper_lim)

        # ==================================================
        # LABELS ABOVE EACH BAR
        # ==================================================

        label_offset = upper_lim * 0.025

        ax.text(
            x[0],
            current_metric + label_offset,
            current_label,
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="black"
        )

        ax.text(
            x[1],
            optimised_metric + label_offset,
            optimised_label,
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="black"
        )

        # ==================================================
        # IMPACT ANNOTATION
        # ==================================================

        impact_y = max(
            current_metric,
            optimised_metric
        ) + upper_lim * 0.12

        impact_colour = (
            "#28A745"
            if incremental_metric >= 0
            else "#DC3545"
        )

        ax.text(
            0.5,
            impact_y,
            incremental_label,
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color=impact_colour
        )

        # ==================================================
        # STYLING
        # ==================================================

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_visible(False)

        ax.yaxis.set_ticks_position("none")
        ax.xaxis.set_ticks_position("none")

    
        # No legend needed because values are labelled directly

        fig.subplots_adjust(
            bottom=0.12,
            top=0.82,
            left=0.12,
            right=0.95
        )

        return fig

    # ==================================================
    # PROFILE PREFERENCE SHARE KEY INSIGHT
    # ==================================================

    @render.ui
    def profile_preference_summary():

        df = profile_analysis_df().copy()

        # --------------------------------------------------
        # Handle no data
        # --------------------------------------------------

        if df.empty:
            return ui.HTML(
                "<span>No data available for the selected filters.</span>"
            )

        # --------------------------------------------------
        # Remove TOTAL row
        # --------------------------------------------------

        profile_df = df[
            df["Crossbreak"] != "Total"
        ].copy()

        if profile_df.empty:
            return ui.HTML(
                "<span>No profile data available.</span>"
            )

        # --------------------------------------------------
        # Identify product share columns
        # --------------------------------------------------

        share_cols = [
            c for c in profile_df.columns
            if c.startswith("Product ") and c.endswith(" Share")
        ]

        if not share_cols:
            return ui.HTML(
                "<span>No product preference share data available.</span>"
            )

        # --------------------------------------------------
        # Find the largest profile difference
        # --------------------------------------------------

        differences = []

        for col in share_cols:

            max_idx = profile_df[col].idxmax()
            min_idx = profile_df[col].idxmin()

            max_value = profile_df.loc[max_idx, col]
            min_value = profile_df.loc[min_idx, col]

            difference = max_value - min_value

            differences.append({
                "Product": col.replace(" Share", ""),
                "Difference": difference,
                "Highest": profile_df.loc[max_idx, "Subgroup"],
                "HighestValue": max_value,
                "Lowest": profile_df.loc[min_idx, "Subgroup"],
                "LowestValue": min_value
            })

        differences_df = pd.DataFrame(differences)

        # --------------------------------------------------
        # Find the product with the biggest profile difference
        # --------------------------------------------------

        biggest = differences_df.loc[
            differences_df["Difference"].idxmax()
        ]

        product = biggest["Product"]
        difference = biggest["Difference"]
        highest_group = biggest["Highest"]
        lowest_group = biggest["Lowest"]

        # Convert share difference to percentage points
        difference_pp = difference * 100

        # --------------------------------------------------
        # Decide whether the difference is meaningful
        # --------------------------------------------------

        if difference_pp < 5:

            summary = (
                "Preference shares are broadly consistent across "
                "respondent profiles, with no substantial differences "
                "between groups."
            )

        else:

            summary = (
                f"<b>{product}</b> shows the greatest variation across "
                f"profiles, with preference highest among "
                f"<b>{highest_group}</b> and lowest among "
                f"<b>{lowest_group}</b> "
                f"({difference_pp:.1f} percentage points apart)."
            )

        return ui.div(
            ui.span(
                icon_svg("wand-magic-sparkles"),
                class_="purple-wand-icon",
                style="""
                    font-size: 1.1rem;
                    margin-right: 8px;
                    flex-shrink: 0;
                """
            ),

            ui.HTML(
                f"<span>{summary}</span>"
            ),

            style="""
                padding: 12px 15px;
                margin-top: 10px;
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                font-size: 0.95rem;
                display: flex;
                align-items: flex-start;
            """
        )

    @render.ui
    def optim_summary_text():
        res = optimisation_results()

        if "error" in res:
            return ui.HTML(
                f"""
                <div style="
                    padding: 15px;
                    margin: 10px 0;
                    border: 1px solid #f5c2c7;
                    background-color: #f8d7da;
                    color: #842029;
                    border-radius: 6px;
                ">
                    ⚠️ {res["error"]}
                </div>
                """
            )

        objective = res.get("objective", "Share")
        scope = "a single product vs competitors" if res.get("scope") == "Product vs competitors" else "the entire portfolio"
        
        current = res["current_metric"]
        optimised = res["optimised_metric"]
        incremental = res["incremental_metric"]

        is_revenue = (objective == "Revenue")

        
        # --------------------------------------------------
        # DYNAMIC OPTIMISATION ASSUMPTIONS FOR SUMMARY
        # --------------------------------------------------
        pricing_summary = ""

        if is_revenue:
            expected_units = input.units_sold()
            price_details = []

            for attr in PRICE_ATTRS:
                attr_id = make_id(attr)
                mode = input[f"price_mode_{attr_id}"]()

                currency = conjoint_model.ATTRIBUTE_CURRENCIES.get(attr, {})
                symbol = currency.get("symbol", "")
                decimals = currency.get("decimals", 2)

                if mode == "fixed":
                    # Use the fixed price specified in the UI
                    price_value = input[f"fixed_price_{attr_id}"]()
                    price_description = "fixed price"
                else:
                    # Use the resulting optimised price
                    price_rows = res["optimised_products"]

                    if res.get("scope") == "Product vs competitors":
                        price_rows = price_rows.loc[
                            price_rows["ProductID"] == res["selected_product"]
                        ]

                    price_value = (
                        price_rows[attr].iloc[0]
                        if not price_rows.empty
                        else None
                    )
                    price_description = "optimised price"

                price_article = "an" if price_description == "optimised price" else "a"

                try:
                    price_value = _price_to_float(price_value, attr)
                    formatted_price = f"{symbol}{price_value:,.{decimals}f}"

                    price_details.append(
                        f"{price_article} <b>{price_description}</b> of "
                        f"<b>{formatted_price}</b>"
                    )
                except (TypeError, ValueError):
                    price_details.append(
                        f"{price_article} <b>{price_description}</b> for <b>{attr}</b>"
                    )

            if price_details:
                pricing_summary = (
                    ", considering "
                    + " and ".join(price_details)
                    + f" with <b>{expected_units:,.0f} expected units sold</b>"
                )


        currency = (
            conjoint_model.ATTRIBUTE_CURRENCIES.get(
                PRICE_ATTRS[0], {}
            )
            if PRICE_ATTRS
            else {}
        )
        currency_symbol = currency.get("symbol", "")

        if is_revenue:
            unit = "revenue"
            curr_str = f"{currency_symbol}{current:,.0f}"
            opt_str = f"{currency_symbol}{optimised:,.0f}"
            inc_str = f"{currency_symbol}{abs(incremental):,.0f}"
        else:
            unit = "percentage points"
            curr_str = f"{current:.1f}%"
            opt_str = f"{optimised:.1f}%"
            inc_str = f"{abs(incremental):.1f}"

        if incremental > 0.01:
            direction_text = "an estimated gain"
            color = "#28A745" 
        elif incremental < -0.01:
            direction_text = "an estimated loss"
            color = "#DC3545" 
        else:
            return ui.div(
                ui.span(
                    icon_svg("wand-magic-sparkles"),
                    class_="purple-wand-icon",
                    style="""
                        font-size: 1.1rem;
                        margin-right: 8px;
                        flex-shrink: 0;
                    """
                ),

                ui.HTML(
                    f"<span>"
                    f"Optimising for <b>{objective}</b> on <b>{scope}</b> yielded no significant changes. "
                    f"The metric remains at <b>{curr_str}</b>."
                    f"</span>"
                ),

                style="""
                    font-size: 0.95rem;
                    display: flex;
                    align-items: flex-start;
                """
            )

        summary_html = (
            f"<span style='font-size: 0.95rem;'>"
            f"By optimising for <b>{objective}</b> on <b>{scope}</b>, the simulation projects "
            f"<b style='color: {color};'>{direction_text} of {inc_str} {unit}</b>. "
            f"The baseline shifts from <b>{curr_str}</b> to an optimised total of "
            f"<b>{opt_str}</b>{pricing_summary}."
            f"</span>"
        )

        return ui.div(
            ui.span(
                icon_svg("wand-magic-sparkles"),
                class_="purple-wand-icon",
                style="""
                    font-size: 1.1rem;
                    margin-right: 8px;
                    flex-shrink: 0;
                """
            ),

            ui.HTML(summary_html),

            style="""
                font-size: 0.95rem;
                display: flex;
                align-items: flex-start;
            """
        )

   
    

    @render.ui
    @reactive.event(input.run_pricing, ignore_none=False)
    def selected_product_pricing():
        selected_product_str = input.pricing_product()
        if not selected_product_str:
            return ui.HTML("")
            
        p_id = int(str(selected_product_str).replace("Product ", ""))
        
        # Safely get the backend configuration
        p_df = products_df()
        if isinstance(p_df, str) and p_df == "BASECASE_FLAG":
            p_df = BASECASE_DF.copy()
            
        row = p_df[p_df["ProductID"].astype(str) == str(p_id)]
        if row.empty:
            return ui.HTML("")
            
        row = row.iloc[0]
        
        # Build a sleek UI box for the sidebar
        html = [f"<div style='font-size: 0.9rem; background-color: #f8f9fa; padding: 12px; border-radius: 6px; border: 1px solid #dee2e6;'>"]
        html.append(f"<strong style='color: #495057;'>{selected_product_str} Base Configuration:</strong>")
        html.append("<ul style='margin-top: 8px; margin-bottom: 0; padding-left: 20px; color: #495057;'>")
        
        for attr in ATTRIBUTES:
            val = row[attr]

            if attr in PRICE_ATTRS:
                val_str = _format_price_value(val, attr)

                html.append(
                    f"<li style='margin-bottom: 4px;'>"
                    f"<b>{attr}:</b> {val_str}"
                    f"</li>"
                )

            else:
                html.append(
                    f"<li style='margin-bottom: 4px;'>"
                    f"<b>{attr}:</b> {val}"
                    f"</li>"
                )

        html.append("</ul></div>")
        return ui.HTML("".join(html))

    

    @render.ui
    @reactive.event(input.run_pricing, ignore_init=True)
    def pricing_summary_text():

        res_df = _pricing_results()

        selected_product_str = input.pricing_product()
        p_id = str(int(selected_product_str.replace("Product ", "")))

        price_attr = PRICE_ATTRS[0] if PRICE_ATTRS else None
        currency_symbol = (
            conjoint_model.ATTRIBUTE_CURRENCIES.get(
                price_attr, {}
            ).get("symbol", "")
            if price_attr
            else ""
        )

        

        # --------------------------------------------------
        # Calculate revenue and revenue-maximising price
        # --------------------------------------------------
        res_df = res_df.copy()
        res_df["Revenue"] = res_df[p_id] * res_df["Price point"]

        max_rev_idx = res_df["Revenue"].idxmax()
        optimal_price = res_df.loc[max_rev_idx, "Price point"]

        min_price = res_df["Price point"].min()
        max_price = res_df["Price point"].max()

        start_share = (
            res_df.loc[
                res_df["Price point"] == min_price, p_id
            ].values[0] * 100
        )

        end_share = (
            res_df.loc[
                res_df["Price point"] == max_price, p_id
            ].values[0] * 100
        )

        # --------------------------------------------------
        # Build current filter description
        # --------------------------------------------------
        filter_parts = []

        for c in FILTER_COLS:
            cid = make_id(f"filter_{c}")

            try:
                selected = input[cid]()
            except KeyError:
                selected = None

            if selected:
                selected = [str(x) for x in selected]

                available = filters_df[c].dropna().astype(str).unique()

                if set(selected) == set(available):
                    filter_text = "All"
                else:
                    filter_text = ", ".join(selected)

                filter_parts.append(
                    f"<b>{c}:</b> {filter_text}"
                )

        # --------------------------------------------------
        # Calculate base size
        # --------------------------------------------------
        try:
            base_size = filtered_data()["Respondent"].nunique()
        except Exception:
            base_size = 0

        # --------------------------------------------------
        # Build filter text
        # --------------------------------------------------
        if not filter_parts:
            filter_html = "<b>All respondents</b>"
        else:
            filter_html = " &nbsp;|&nbsp; ".join(filter_parts)

        # Add base size
        filter_html += (
            f" &nbsp;|&nbsp; <b>Base:</b> {base_size:,}"
        )

        # --------------------------------------------------
        # Add caution if base < 100
        # --------------------------------------------------
        caution_html = ""

        if base_size < 100:
            caution_html = (
                "<div style='margin-top: 5px; color: #B02A37; "
                "font-size: 0.82rem; font-style: italic;'>"
                "⚠ Results should be interpreted with caution due to "
                "a base size below 100."
                "</div>"
            )
        # --------------------------------------------------
        # Final footer text
        # --------------------------------------------------
        min_price_str = _format_price_value(min_price, price_attr)
        max_price_str = _format_price_value(max_price, price_attr)
        optimal_price_str = _format_price_value(
            optimal_price, price_attr
        )

        html_text = (
            f"<div style='font-size: 0.95rem;'>"

            f"<div style='margin-bottom: 8px;'>"
            f"The pricing simulation for <b>{selected_product_str}</b> "
            f"shows preference share dropping from "
            f"<b>{start_share:.1f}%</b> at {min_price_str} "
            f"down to <b>{end_share:.1f}%</b> at {max_price_str}. "
            f"Factoring in this elasticity, the projected revenue trajectory "
            f"peaks at a revenue-maximising price of "
            f"<b style='color: #28A745;'>{optimal_price_str}</b>."
            f"</div>"

            f"<div style='font-size: 0.85rem; color: #6c757d; "
            f"border-top: 1px solid #dee2e6; padding-top: 7px;'>"
            f"<b>Analysis based on:</b> {filter_html}"
            f"{caution_html}"
            f"</div>"

            f"</div>"
        )

        return ui.HTML(html_text)

    @render.data_frame
    @reactive.event(input.run_pricing, ignore_init=True)
    def pricing_df():
        return render.DataGrid(
            _pricing_results(),
            summary=True
        )

    @render.ui
    def pricing_assumptions_controls():

        controls = []

        for attr in PRICE_ATTRS:

            # Get this attribute's tested prices from Excel
            prices = (
                pd.to_numeric(grid_df[attr], errors="coerce")
                .dropna()
                .unique()
            )
            prices = sorted(float(p) for p in prices)

            if not prices:
                continue

            min_price = prices[0]
            max_price = prices[-1]

            # Infer the price increment from the Excel levels
            differences = [
                prices[i + 1] - prices[i]
                for i in range(len(prices) - 1)
                if prices[i + 1] > prices[i]
            ]

            step = min(differences) if differences else 1.0

            # Use the basecase value as the initial fixed price
            default_price = min_price

            if attr in BASECASE_DF.columns:
                basecase_price = pd.to_numeric(
                    pd.Series([BASECASE_DF.iloc[0][attr]]),
                    errors="coerce"
                ).iloc[0]

                if pd.notna(basecase_price):
                    default_price = float(basecase_price)

            # Use the detected currency for this attribute
            currency = conjoint_model.ATTRIBUTE_CURRENCIES.get(attr, {})
            symbol = currency.get("symbol", "")
            decimals = currency.get("decimals", 2)

            attr_id = make_id(attr)

            controls.extend([
                ui.tags.div(
                    attr,
                    style=(
                        "font-weight: 600; "
                        "color: #3C0F03; "
                        "margin-top: 12px; "
                        "margin-bottom: 6px;"
                    )
                ),

                ui.input_radio_buttons(
                    f"price_mode_{attr_id}",
                    "Price setting",
                    choices={
                        "optimise": "Optimise price",
                        "fixed": "Fix price"
                    },
                    selected="optimise",
                    inline=True
                ),

                ui.input_numeric(
                    f"fixed_price_{attr_id}",
                    "Fixed price",
                    value=default_price,
                    min=min_price,
                    max=max_price,
                    step=step,
                    width="100%"
                ),

                ui.tags.small(
                    (
                        f"Allowed range: {symbol}"
                        f"{min_price:,.{decimals}f} – "
                        f"{symbol}{max_price:,.{decimals}f}"
                    ),
                    style=(
                        "display: block; "
                        "margin-top: -6px; "
                        "color: #6c757d;"
                    )
                )
            ])

        return ui.TagList(*controls)


    # ==================================================
    # PRICING KEY INSIGHT
    # ==================================================

    @render.ui
    def pricing_summary():
        pricing_results = _pricing_results()

        if pricing_results.empty or _pricing_is_stale():
            return ui.div()

        # --------------------------------------------------
        # Handle no data
        # --------------------------------------------------

        if pricing_results.empty:
            return ui.HTML(
                "<span>No pricing data available for the selected filters.</span>"
            )

        # --------------------------------------------------
        # Selected product
        # --------------------------------------------------

        selected_product = int(
            str(input.pricing_product()).replace("Product ", "")
        )

        p_col = str(selected_product)

        # --------------------------------------------------
        # Find revenue-maximising price
        # --------------------------------------------------

        pricing_results["Revenue"] = (
            pricing_results[p_col]
            * pricing_results["Price point"]
        )

        max_rev_idx = pricing_results["Revenue"].idxmax()

        optimal_price = pricing_results.loc[
            max_rev_idx,
            "Price point"
        ]

        optimal_share = pricing_results.loc[
            max_rev_idx,
            p_col
        ]

        # --------------------------------------------------
        # Current price
        # --------------------------------------------------

        selected_price_attr = input.pricing_attribute()

        currency_symbol = (
            conjoint_model.ATTRIBUTE_CURRENCIES.get(
                selected_price_attr, {}
            ).get("symbol", "")
        )

        current_price = products_df().loc[
            products_df()["ProductID"] == selected_product,
            selected_price_attr
        ].iloc[0]

        # --------------------------------------------------
        # Competitors OFF
        # --------------------------------------------------

        if not input.show_competitors():

            summary = (
                f"<span>"
                f"<b>Product {selected_product}</b>'s revenue is maximised "
                f"at around <b>{currency_symbol}{optimal_price:,.2f}</b>, where its preference "
                f"share is <b>{optimal_share:.1%}</b>. "
                f"This highlights the trade-off between increasing price and "
                f"maintaining preference share."
                f"</span>"
            )

        # --------------------------------------------------
        # Competitors ON
        # --------------------------------------------------

        else:

            competitor_cols = [
                c for c in pricing_results.columns
                if c not in [
                    "Price point",
                    "Revenue",
                    p_col,
                    "NONE"
                ]
            ]

            if competitor_cols:

                # Find competitor with highest share at revenue-maximising price
                competitor_shares = {
                    c: pricing_results.loc[
                        max_rev_idx,
                        c
                    ]
                    for c in competitor_cols
                }

                strongest_competitor = max(
                    competitor_shares,
                    key=competitor_shares.get
                )

                strongest_competitor_share = competitor_shares[
                    strongest_competitor
                ]

                summary = (
                    f"<span>"
                    f"At the revenue-maximising price of "
                    f"<b>{currency_symbol}{optimal_price:,.2f}</b>, "
                    f"<b>Product {selected_product}</b> has a preference share "
                    f"of <b>{optimal_share:.1%}</b>, compared with "
                    f"<b>Product {strongest_competitor}</b> at "
                    f"<b>{strongest_competitor_share:.1%}</b>. "
                    f"The chart shows how changing price shifts demand "
                    f"between products."
                    f"</span>"
                )

            else:

                summary = (
                    f"<span>"
                    f"<b>Product {selected_product}</b>'s revenue is maximised "
                    f"at around <b>{currency_symbol}{optimal_price:,.2f}</b>, with a preference "
                    f"share of <b>{optimal_share:.1%}</b>."
                    f"</span>"
                )

        return ui.div(
            ui.span(
                icon_svg("wand-magic-sparkles"),
                class_="purple-wand-icon",
                style="""
                    font-size: 1.1rem;
                    margin-right: 8px;
                    flex-shrink: 0;
                """
            ),

            ui.HTML(summary),

            style="""
                padding: 12px 15px;
                margin-top: 10px;
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                font-size: 0.95rem;
                display: flex;
                align-items: flex-start;
            """
        )


app = App(
    app_ui,
    server,
    static_assets=Path(__file__).parent / "shared" / "www"
)
