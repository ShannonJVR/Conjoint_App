# CONJOINT MODEL CORE
# --------------------------------------------------
# Responsibilities:
# - Load conjoint outputs
# - Translate simulator selections into utilities
# - Compute preference shares INCLUDING NONE
#
# GUARANTEES:
# - ProductID types match UI (ints + "NONE")
# - No NaN values
# - NONE behaves like a real alternative
# --------------------------------------------------

import pandas as pd
import numpy as np
import re

from shiny import ui


# ======================================================
# HELPERS
# ======================================================

import re

def make_id(value):
    """Convert a label into a valid Shiny input ID."""
    value = str(value).strip()
    value = re.sub(r"[^A-Za-z0-9_]", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")

def clean_attr(x):
    return str(x).strip().replace("\u00a0", " ")


# --------------------------------------------------
# LOAD EXCEL DATA
# --------------------------------------------------
def load_excel():
    """
    Loads the Excel file specified by EXCEL_PATH and returns the main tabs as DataFrames.
    Existing tabs:
        - Grid: Attribute definitions and levels
        - Results: Respondent-level utilities
        - Filters: Any respondent filters
        - Settings: Optional app settings
        - Default: Default product selections
        - Restrictions: Optional product restrictions
    """
    data_path = r"./shared/data/Workbook/App_Workbook.xlsx"

    # Read all sheets into a dict
    sheets = pd.read_excel(
    data_path,
    sheet_name=None,
    keep_default_na=False
    )


    # -----------------------------
    # Section to add new tabs:
    # If your Excel file has additional sheets in the future, you can retrieve them here
    # e.g., sheets.get("NewTabName", pd.DataFrame())
    # -----------------------------
    grid = sheets["Grid"]
    grid.columns = [clean_attr(c) for c in grid.columns]

    # Convert blank cells in Grid to NaN
    # This prevents empty strings from mixing with numeric price levels
    grid = grid.replace(r"^\s*$", np.nan, regex=True)



    level_utilities = sheets["Level Utilities"].drop(
        columns=["RLH", "Num Parameters"],  # Drop extra columns if present
        errors="ignore"  # If they don't exist, ignore errors
        )
    
    attribute_importances = sheets["Attribute Importances"]
    
    filters = sheets["Filters"]
    filters.columns = [clean_attr(c) for c in filters.columns]

    settings = sheets.get("Settings", pd.DataFrame())  # Optional settings tab

    default = sheets["Default"]  # Default product configuration
    
    restrictions = sheets.get("Restrictions", pd.DataFrame())  # Optional restrictions tab
    if not restrictions.empty:
        restrictions.columns = [clean_attr(c) for c in restrictions.columns]

    return (
        grid,
        level_utilities,
        attribute_importances,
        filters,
        settings,
        default,
        restrictions
    )


# ======================================================
# RESTRICTIONS HELPER
# ======================================================

def apply_restrictions(
    restrictions_df,
    current_attr,
    current_value,
    target_attr,
    target_input_id,
    input,
    session
):
    all_levels = sorted(
        grid_df[target_attr].dropna().astype(str).unique()
    )

    sub = restrictions_df[
        (restrictions_df["If Attribute A"] == current_attr) &
        (restrictions_df["Level"].astype(str) == str(current_value)) &
        (restrictions_df["Then Attribute B"] == target_attr)
    ]

    if sub.empty:
        selected_val = (
            input[target_input_id]()
            if input[target_input_id]() in all_levels
            else all_levels[0]
        )

        ui.update_select(
            target_input_id,
            choices=all_levels,
            selected=selected_val
        )

        return

    r = sub.iloc[0]

    text_to_show = str(
        r.get("Text to show on B", "NA")
    )

    ui.update_select(
        target_input_id,
        choices=[text_to_show],
        selected=text_to_show
    )


def apply_restrictions_to_df(product_df):
    """
    Apply the Excel Restrictions rules directly to a product dataframe.

    This is separate from apply_restrictions(), which controls the
    Shiny UI. This function makes sure the dataframe passed into
    the conjoint model also respects the same restrictions.
    """

    df = product_df.copy()

    # If there are no restrictions, return the dataframe unchanged
    if restrictions_df.empty:
        return df

    # Loop through each product
    for p in range(len(df)):

        # Loop through each restriction from Excel
        for _, r in restrictions_df.iterrows():

            attr_a = clean_attr(r["If Attribute A"])
            level_a = str(r["Level"]).strip()

            attr_b = clean_attr(r["Then Attribute B"])

            text_to_show = str(
                r.get("Text to show on B", "NA")
            ).strip()

            # Make sure both attributes exist in the dataframe
            if attr_a not in df.columns or attr_b not in df.columns:
                continue

            # Current value of Attribute A for this product
            current_value = str(
                df.iloc[p][attr_a]
            ).strip()

            # If the restriction condition is met,
            # change Attribute B to the restricted value
            if current_value == level_a:

                df.iloc[
                    p,
                    df.columns.get_loc(attr_b)
                ] = text_to_show

    return df    

# ======================================================
# LOAD DATA
# ======================================================
grid_df, utils_df, attributes_df, filters_df, settings_df, default_df, restrictions_df = load_excel()
grid_df.columns = [clean_attr(c) for c in grid_df.columns]
filters_df.columns = [clean_attr(c) for c in filters_df.columns]


ATTRIBUTES = grid_df.columns.tolist()


# Detect currency symbols and codes in attribute labels.
# Extend this mapping as required by future Excel templates.
CURRENCY_PATTERNS = {
    "£": {"symbol": "£", "code": "GBP", "decimals": 2},
    "€": {"symbol": "€", "code": "EUR", "decimals": 2},
    "$": {"symbol": "$", "code": "USD", "decimals": 2},
    "¥": {"symbol": "¥", "code": "JPY", "decimals": 0},
    "₹": {"symbol": "₹", "code": "INR", "decimals": 2},
    "₩": {"symbol": "₩", "code": "KRW", "decimals": 0},
    "CHF": {"symbol": "CHF ", "code": "CHF", "decimals": 2},
    "CAD": {"symbol": "C$", "code": "CAD", "decimals": 2},
    "AUD": {"symbol": "A$", "code": "AUD", "decimals": 2},
}

def detect_currency(attr_name):
    """Return currency metadata if the attribute label identifies a currency."""
    label = str(attr_name)

    for marker, details in CURRENCY_PATTERNS.items():
        if marker in label:
            return details.copy()

    return None


# Detect currency-valued attributes from Excel labels
ATTRIBUTE_CURRENCIES = {
    attr: currency
    for attr in ATTRIBUTES
    if (currency := detect_currency(attr)) is not None
}


def format_price(value, attr, decimals=None):
    """Format a price using the currency detected from its Excel attribute label."""
    currency = ATTRIBUTE_CURRENCIES.get(attr, {})
    symbol = currency.get("symbol", "")
    
    if decimals is None:
        decimals = currency.get("decimals", 2)

    if value is None or pd.isna(value):
        return ""

    return f"{symbol}{float(value):,.{decimals}f}"


# Identify price attributes separately.
# A currency symbol alone does not necessarily mean an attribute is a price.
PRICE_ATTRS = [
    attr for attr in ATTRIBUTES
    if "price" in str(attr).lower()
    or "cost" in str(attr).lower()
    if attr in ATTRIBUTE_CURRENCIES
]

# Keep the original variable for compatibility with existing code
PRICE_ATTR = PRICE_ATTRS[0] if PRICE_ATTRS else None



# Calculate separate numeric ranges for each price attribute
PRICE_RANGES = {}

for attr in PRICE_ATTRS:
    numeric_prices = pd.to_numeric(
        grid_df[attr].replace(r"^\s*$", np.nan, regex=True),
        errors="coerce"
    ).dropna()

    if not numeric_prices.empty:
        PRICE_RANGES[attr] = {
            "min": float(numeric_prices.min()),
            "max": float(numeric_prices.max()),
            "levels": sorted(numeric_prices.unique().tolist())
        }

# Preserve existing single-price settings for compatibility
if PRICE_ATTR is not None and PRICE_ATTR in PRICE_RANGES:
    MIN_PRICE = PRICE_RANGES[PRICE_ATTR]["min"]
    MAX_PRICE = PRICE_RANGES[PRICE_ATTR]["max"]
else:
    MIN_PRICE = None
    MAX_PRICE = None

FILTER_COLS = [
    c for c in filters_df.columns
    if c not in ("Respondent", "Weight")
]

N_PRODUCTS = default_df.shape[1] - 1

LEVELS = {
    attr: (
        grid_df[attr]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda s: (s != "") & (s.str.lower() != "nan")]
        .drop_duplicates()
        .tolist()
    )
    for attr in ATTRIBUTES
}

if not restrictions_df.empty:
    restrictions_df.columns = [clean_attr(c) for c in restrictions_df.columns]


# ======================================================
# BASE CASE
# ======================================================
def build_basecase():
    df = default_df.copy()
    df.iloc[:, 0] = df.iloc[:, 0].apply(clean_attr)
    rows = []
    for p in range(N_PRODUCTS):
        row = {"ProductID": p + 1}
        for attr in ATTRIBUTES:
            row[attr] = df.loc[df.iloc[:, 0] == attr, df.columns[p + 1]].values[0]
        rows.append(row)
    return pd.DataFrame(rows)

## TODO: Fix basecase (Connecting flight: No should not be showing Layover time!)
BASECASE_DF = build_basecase()



# --------------------------------------------------
# DETECT PRICE ATTRIBUTES
# --------------------------------------------------
def detect_price_attributes(grid_df):
    """
    Detects all attributes containing 'price', case-insensitive.
    Returns a list of attribute names.
    """
    return [
        c for c in grid_df.columns
        if "price" in str(c).lower()
    ]


def detect_price_attribute(grid_df):
    """
    Backwards-compatible helper.
    Returns the first detected price attribute, or None.
    """
    attrs = detect_price_attributes(grid_df)
    return attrs[0] if attrs else None



# --------------------------------------------------
# PARSE PRICE LEVELS FROM RESULTS
# --------------------------------------------------

def parse_price_levels(util_df, attr):
    """
    Extract numeric price levels and their corresponding
    utility columns using the currency detected for the attribute.
    """
    levels = []

    currency = ATTRIBUTE_CURRENCIES.get(attr, {})
    symbol = currency.get("symbol", "").strip()

    for c in util_df.columns:
        if not str(c).startswith(f"{attr} - "):
            continue

        level_label = str(c).split(f"{attr} - ", 1)[1].strip()

        # Remove the detected currency symbol, if present.
        if symbol:
            level_label = level_label.replace(symbol, "").strip()

        # Also allow plain numeric levels from Excel.
        level_label = level_label.replace(",", "")

        try:
            price = float(level_label)
        except ValueError:
            continue

        levels.append((price, c))

    return sorted(levels, key=lambda x: x[0])



# --------------------------------------------------
# CALCULATE PRICE UTILITY
# --------------------------------------------------
def get_price_utility(util_df, attr, price):
    """
    Interpolates utility for a given price.
    If the price matches a known level, use that utility.
    Otherwise, linearly interpolate between the two nearest price points.
    """
    levels = parse_price_levels(util_df, attr)
    if not levels:
        return 0.0  # No price levels found

    prices = [p for p, _ in levels]

    # Below lowest level
    if price <= prices[0]:
        return util_df[levels[0][1]]

    # Above highest level
    if price >= prices[-1]:
        return util_df[levels[-1][1]]

    # Interpolate between two nearest levels
    for i in range(len(levels) - 1):
        p1, c1 = levels[i]
        p2, c2 = levels[i + 1]
        if p1 <= price <= p2:
            w = (price - p1) / (p2 - p1)
            return util_df[c1] * (1 - w) + util_df[c2] * w

    return 0.0


def compute_shares(
    products_df,
    respondent_ids=None,
    include_none=True,
    respondent_weights=None,
):
    """
    Computes respondent-level Share of Preference.

    Categorical attributes use exact level matching.
    Price attributes are interpolated between their Excel utility levels.

    If respondent_weights is supplied, preference shares are aggregated
    using respondent weights aligned by Respondent ID.
    Otherwise, shares are averaged equally across respondents.
    """

    # --------------------------------------------------
    # LOAD EXCEL DATA
    # --------------------------------------------------
    grid_df, utils_df, _, _, _, default_df, _ = load_excel()
    grid_df.columns = [clean_attr(c) for c in grid_df.columns]

    # --------------------------------------------------
    # FILTER RESPONDENTS
    # --------------------------------------------------
    if respondent_ids is not None:
        utils_df = utils_df[
            utils_df["Respondent"].isin(respondent_ids)
        ].copy()

    product_ids = products_df["ProductID"].tolist()

    if include_none:
        product_ids.append("NONE")

    if utils_df.empty:
        return pd.DataFrame({
            "ProductID": product_ids,
            "PrefShare": 0.0,
        })

    # Preserve respondent order for weight alignment.
    respondent_order = utils_df["Respondent"].tolist()

    # --------------------------------------------------
    # PREPARE RESPONDENT UTILITIES
    # --------------------------------------------------
    utils_df = utils_df.drop(
        columns=["RLH", "Num Parameters"],
        errors="ignore",
    )

    util_matrix = (
        utils_df
        .drop(columns=["Respondent"])
        .astype(float)
        .fillna(0.0)
    )

    utility_cols = util_matrix.columns.tolist()

    # --------------------------------------------------
    # IDENTIFY UTILITY COLUMNS BY ATTRIBUTE
    # --------------------------------------------------
    attribute_utility_cols = {}

    for col in utility_cols:
        if " - " not in col:
            continue

        attr_name, level = col.split(" - ", 1)
        attr_name = attr_name.strip()
        level = level.strip()

        if attr_name not in products_df.columns:
            continue

        if attr_name in PRICE_ATTRS:
            currency = ATTRIBUTE_CURRENCIES.get(attr_name, {})
            symbol = currency.get("symbol", "").strip()

            numeric_level_text = level

            if symbol:
                numeric_level_text = numeric_level_text.replace(
                    symbol, ""
                ).strip()

            try:
                numeric_level = float(
                    numeric_level_text.replace(",", "").strip()
                )
            except ValueError:
                continue

            attribute_utility_cols.setdefault(
                attr_name, []
            ).append((numeric_level, col))

    # Sort price anchor levels numerically.
    for attr_name in attribute_utility_cols:
        attribute_utility_cols[attr_name].sort(
            key=lambda item: item[0]
        )

    price_attrs = [
        attr for attr in products_df.columns
        if attr in attribute_utility_cols
    ]

    # --------------------------------------------------
    # BUILD CATEGORICAL PRODUCT MATRIX
    # --------------------------------------------------
    product_matrix = pd.DataFrame(
        0.0,
        index=products_df.index,
        columns=utility_cols,
    )

    for col in utility_cols:
        if " - " not in col:
            continue

        attr_name, level = col.split(" - ", 1)
        attr_name = attr_name.strip()
        level = level.strip()

        if attr_name not in products_df.columns:
            continue

        # Price utilities are handled separately by interpolation.
        if attr_name in PRICE_ATTRS:
            continue

        product_matrix[col] = (
            products_df[attr_name].astype(str).str.strip()
            == level
        ).astype(float)

    # Product x respondent utility matrix.
    utility_matrix = (
        product_matrix.to_numpy()
        @ util_matrix.to_numpy().T
    )

    # --------------------------------------------------
    # INTERPOLATE EACH PRICE ATTRIBUTE
    # --------------------------------------------------
    for attr_name in price_attrs:

        anchors = attribute_utility_cols[attr_name]

        if not anchors:
            continue

        anchor_prices = np.array(
            [price for price, _ in anchors],
            dtype=float,
        )

        # Respondents x price-level anchors.
        anchor_utilities = util_matrix[
            [col for _, col in anchors]
        ].to_numpy(dtype=float)

        currency = ATTRIBUTE_CURRENCIES.get(attr_name, {})
        symbol = currency.get("symbol", "").strip()

        price_values = (
            products_df[attr_name]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )

        if symbol:
            price_values = price_values.str.replace(
                symbol, "", regex=False
            ).str.strip()

        product_prices = pd.to_numeric(
            price_values,
            errors="coerce",
        ).to_numpy(dtype=float)

        for row_idx, price in enumerate(product_prices):

            if not np.isfinite(price):
                raise ValueError(
                    f"Invalid price for attribute '{attr_name}': "
                    f"{products_df.iloc[row_idx][attr_name]!r}"
                )

            if len(anchor_prices) == 1:
                interpolated = anchor_utilities[:, 0]

            elif price <= anchor_prices[0]:
                interpolated = anchor_utilities[:, 0]

            elif price >= anchor_prices[-1]:
                interpolated = anchor_utilities[:, -1]

            else:
                upper_idx = np.searchsorted(
                    anchor_prices, price, side="right"
                )
                lower_idx = upper_idx - 1

                lower_price = anchor_prices[lower_idx]
                upper_price = anchor_prices[upper_idx]

                lower_utility = anchor_utilities[:, lower_idx]
                upper_utility = anchor_utilities[:, upper_idx]

                weight = (
                    (price - lower_price)
                    / (upper_price - lower_price)
                )

                interpolated = (
                    lower_utility
                    + weight * (upper_utility - lower_utility)
                )

            utility_matrix[row_idx, :] += interpolated

    # --------------------------------------------------
    # HANDLE NONE OPTION
    # --------------------------------------------------
    if include_none:
        if "NONE" in util_matrix.columns:
            none_util = util_matrix["NONE"].to_numpy(dtype=float)
        else:
            none_util = np.zeros(
                len(util_matrix),
                dtype=float,
            )

        utility_matrix = np.vstack([
            utility_matrix,
            none_util,
        ])

    # --------------------------------------------------
    # SHARE OF PREFERENCE
    # Numerically stable multinomial-logit calculation.
    # --------------------------------------------------
    utility_matrix = np.nan_to_num(
        utility_matrix,
        nan=0.0,
        posinf=700.0,
        neginf=-700.0,
    )

    utility_matrix = utility_matrix - np.max(
        utility_matrix,
        axis=0,
        keepdims=True,
    )

    exp_util = np.exp(utility_matrix)

    pref_share = exp_util / exp_util.sum(
        axis=0,
        keepdims=True,
    )

    # --------------------------------------------------
    # AGGREGATE RESPONDENT SHARES
    # --------------------------------------------------
    if respondent_weights is None:
        avg_share = pref_share.mean(axis=1)

    else:
        weights = pd.Series(
            respondent_weights,
            dtype=float,
        )

        # Align weights to the same respondent order as utilities.
        weights = weights.reindex(respondent_order)

        weights = weights.fillna(0.0).to_numpy(dtype=float)

        if len(weights) != pref_share.shape[1]:
            raise ValueError(
                "Respondent weights do not match the utility records."
            )

        if (
            not np.all(np.isfinite(weights))
            or np.any(weights < 0)
            or weights.sum() <= 0
        ):
            raise ValueError(
                "Respondent weights must be finite, non-negative, "
                "and have a positive total."
            )

        avg_share = np.average(
            pref_share,
            axis=1,
            weights=weights,
        )

    # --------------------------------------------------
    # RETURN RESULTS
    # --------------------------------------------------
    return pd.DataFrame({
        "ProductID": product_ids,
        "PrefShare": avg_share / avg_share.sum(),
    })



def prepare_share_evaluator(
    products_df,
    respondent_ids=None,
    include_none=True,
    respondent_weights=None,
):
    """
    Prepare utilities once for exhaustive optimisation.

    Returns a function that evaluates the weighted preference share
    of a candidate product against unchanged competitors.

    Uses the same categorical matching, linear price interpolation,
    NONE treatment and respondent-level multinomial-logit calculation
    as compute_shares().
    """

    # --------------------------------------------------
    # LOAD AND FILTER RESPONDENT UTILITIES ONCE
    # --------------------------------------------------
    _, utils_df, _, _, _, _, _ = load_excel()

    if respondent_ids is not None:
        utils_df = utils_df[
            utils_df["Respondent"].isin(respondent_ids)
        ].copy()

    if utils_df.empty:
        raise ValueError(
            "No respondent utilities available for optimisation."
        )

    respondent_order = utils_df["Respondent"].tolist()

    util_matrix = (
        utils_df
        .drop(
            columns=["RLH", "Num Parameters", "Respondent"],
            errors="ignore",
        )
        .astype(float)
        .fillna(0.0)
    )

    utility_cols = util_matrix.columns.tolist()
    respondent_utilities = util_matrix.to_numpy(dtype=float)
    n_respondents = len(respondent_order)

    # --------------------------------------------------
    # PREPARE RESPONDENT WEIGHTS
    # --------------------------------------------------
    if respondent_weights is None:
        weights = np.ones(n_respondents, dtype=float)

    else:
        weights = pd.Series(
            respondent_weights,
            dtype=float,
        ).reindex(respondent_order)

        weights = weights.fillna(0.0).to_numpy(dtype=float)

        if (
            len(weights) != n_respondents
            or not np.all(np.isfinite(weights))
            or np.any(weights < 0)
            or weights.sum() <= 0
        ):
            raise ValueError(
                "Respondent weights must align with the utility records "
                "and be finite, non-negative, with a positive total."
            )

    # --------------------------------------------------
    # PREPARE CATEGORICAL UTILITIES AND PRICE ANCHORS
    # --------------------------------------------------
    categorical_utilities = {}
    price_anchors = {}

    for col_idx, col in enumerate(utility_cols):

        if " - " not in col:
            continue

        attr_name, level = col.split(" - ", 1)
        attr_name = attr_name.strip()
        level = level.strip()

        if attr_name not in products_df.columns:
            continue

        utility_vector = respondent_utilities[:, col_idx]

        if attr_name in PRICE_ATTRS:

            currency = ATTRIBUTE_CURRENCIES.get(attr_name, {})
            symbol = currency.get("symbol", "").strip()

            numeric_level = level

            if symbol:
                numeric_level = numeric_level.replace(
                    symbol, ""
                ).strip()

            try:
                numeric_level = float(
                    numeric_level.replace(",", "").strip()
                )
            except ValueError:
                continue

            price_anchors.setdefault(attr_name, []).append(
                (numeric_level, utility_vector)
            )

        else:
            # Add matching utility columns together, as the original
            # product-matrix calculation does.
            categorical_utilities.setdefault(
                attr_name, {}
            )

            if level in categorical_utilities[attr_name]:
                categorical_utilities[attr_name][level] += utility_vector
            else:
                categorical_utilities[attr_name][level] = (
                    utility_vector.copy()
                )

    for attr_name in price_anchors:
        price_anchors[attr_name].sort(key=lambda item: item[0])

    # --------------------------------------------------
    # HELPER: CALCULATE ONE PRODUCT'S UTILITY
    # --------------------------------------------------
    def calculate_product_utility(product_row):

        utility = np.zeros(n_respondents, dtype=float)

        # Categorical attribute contributions.
        for attr_name, levels in categorical_utilities.items():

            value = str(product_row[attr_name]).strip()

            if value in levels:
                utility += levels[value]

        # Price attribute contributions, using the same interpolation
        # and endpoint behaviour as compute_shares().
        for attr_name, anchors in price_anchors.items():

            if not anchors:
                continue

            raw_price = str(product_row[attr_name])
            raw_price = raw_price.replace(",", "").strip()

            currency = ATTRIBUTE_CURRENCIES.get(attr_name, {})
            symbol = currency.get("symbol", "").strip()

            if symbol:
                raw_price = raw_price.replace(symbol, "").strip()

            price = pd.to_numeric(raw_price, errors="coerce")

            if pd.isna(price) or not np.isfinite(price):
                raise ValueError(
                    f"Invalid price for '{attr_name}': "
                    f"{product_row[attr_name]!r}"
                )

            anchor_prices = np.array(
                [item[0] for item in anchors],
                dtype=float,
            )

            anchor_utilities = np.column_stack(
                [item[1] for item in anchors]
            )

            if len(anchor_prices) == 1 or price <= anchor_prices[0]:
                interpolated = anchor_utilities[:, 0]

            elif price >= anchor_prices[-1]:
                interpolated = anchor_utilities[:, -1]

            else:
                upper_idx = np.searchsorted(
                    anchor_prices, price, side="right"
                )
                lower_idx = upper_idx - 1

                lower_price = anchor_prices[lower_idx]
                upper_price = anchor_prices[upper_idx]

                weight = (
                    (price - lower_price)
                    / (upper_price - lower_price)
                )

                interpolated = (
                    anchor_utilities[:, lower_idx]
                    + weight * (
                        anchor_utilities[:, upper_idx]
                        - anchor_utilities[:, lower_idx]
                    )
                )

            utility += interpolated

        return utility

    # --------------------------------------------------
    # PRECOMPUTE ALL UNCHANGED COMPETITOR UTILITIES
    # --------------------------------------------------
    product_ids = products_df["ProductID"].tolist()

    if len(set(product_ids)) != len(product_ids):
        raise ValueError(
            "ProductID values must be unique for optimisation."
        )

    product_positions = {
        product_id: idx
        for idx, product_id in enumerate(product_ids)
    }

    base_utilities = np.vstack([
        calculate_product_utility(row)
        for _, row in products_df.iterrows()
    ])

    # The NONE utility is constant across candidate configurations.
    if include_none and "NONE" in util_matrix.columns:
        none_utility = util_matrix["NONE"].to_numpy(dtype=float)
    else:
        none_utility = np.zeros(n_respondents, dtype=float)

    # --------------------------------------------------
    # RETURN FAST CANDIDATE EVALUATOR
    # --------------------------------------------------
    def evaluate_candidate(candidate_row, product_id):

        if product_id not in product_positions:
            raise ValueError(
                f"Unknown ProductID: {product_id!r}"
            )

        target_idx = product_positions[product_id]

        # Only replace the target product's utility row.
        # Competitor utilities are reused.
        candidate_utilities = base_utilities.copy()

        candidate_utilities[target_idx, :] = (
            calculate_product_utility(candidate_row)
        )

        if include_none:
            candidate_utilities = np.vstack([
                candidate_utilities,
                none_utility,
            ])

        # Numerically stable multinomial-logit calculation.
        candidate_utilities = np.nan_to_num(
            candidate_utilities,
            nan=0.0,
            posinf=700.0,
            neginf=-700.0,
        )

        candidate_utilities -= np.max(
            candidate_utilities,
            axis=0,
            keepdims=True,
        )

        exp_utilities = np.exp(candidate_utilities)

        respondent_shares = exp_utilities / exp_utilities.sum(
            axis=0,
            keepdims=True,
        )

        # Aggregate each option's shares using respondent weights,
        # then apply the same normalisation as compute_shares().
        average_shares = np.average(
            respondent_shares,
            axis=1,
            weights=weights,
        )

        average_shares /= average_shares.sum()

        return float(average_shares[target_idx])

    return evaluate_candidate
            


def get_level_utilities(respondent_ids=None):
    """
    Calculate average utility for each level across respondents.
    
    Args:
        respondent_ids: List of respondent IDs to filter. If None, uses all.
        
    Returns:
        DataFrame with columns: Attribute, Level, Utility
    """
    grid_df, utils_df, _, _, _, _, _ = load_excel()
    grid_df.columns = [clean_attr(c) for c in grid_df.columns]
    
    if respondent_ids is not None:
        utils_df = utils_df[
            utils_df["Respondent"].isin(respondent_ids)
        ].copy()
    
    if utils_df.empty:
        return pd.DataFrame({
            "Attribute": [],
            "Level": [],
            "Utility": []
        })
    
    # utils_df = utils_df.drop(columns=["Respondent"]).astype(float)
    # utils_df.insert(0, "Respondent", utils_df["Respondent"])
    
    # Extract utilities for each level
    level_utilities = []
    
    for col in utils_df.columns:
        if col == "Respondent" or col == "NONE":
            continue
        
        # Parse attribute and level from column name (e.g., "Attribute - Level Value")
        if " - " in col:
            parts = col.split(" - ", 1)
            if len(parts) == 2:
                attr = parts[0].strip()
                level = parts[1].strip()
                avg_utility = utils_df[col].mean()
                level_utilities.append({
                    "Attribute": attr,
                    "Level": level,
                    "Utility": avg_utility
                })
    
    result_df = pd.DataFrame(level_utilities)
    
    if not result_df.empty:
        result_df = result_df.sort_values(["Attribute", "Utility"])
    
    return result_df



def get_attribute_importances(respondent_ids=None, exclude_price=False):
    """
    Calculate attribute importance based on utility ranges.

    Args:
        respondent_ids: List of respondent IDs to filter. If None, uses all.
        exclude_price: If True, excludes price attributes from importance.

    Returns:
        DataFrame with columns: Attribute, Importance (%)
    """
    attributes_filters_df = pd.merge(
        filters_df.loc[
            :, [c for c in filters_df.columns if c not in FILTER_COLS]
        ],
        attributes_df,
        on="Respondent",
        how="inner"
    )

    # Remove accidental whitespace from column names
    attributes_filters_df.columns = (
        attributes_filters_df.columns.str.strip()
    )

    if respondent_ids is not None:
        attributes_filters_df = attributes_filters_df.loc[
            attributes_filters_df["Respondent"].isin(respondent_ids)
        ].copy()

    # If no respondents after filtering, return empty DataFrame
    if attributes_filters_df.empty:
        return pd.DataFrame({
            "Attribute": [],
            "Importance": []
        })

    # Use the Excel-defined attributes
    if exclude_price:
        attributes_list = [
            attr for attr in ATTRIBUTES
            if attr not in PRICE_ATTRS
        ]
    else:
        attributes_list = ATTRIBUTES

    importances = []

    for attr in attributes_list:
        imp = (
            attributes_filters_df["Weight"]
            * attributes_filters_df[attr]
        ).sum() / attributes_filters_df["Weight"].sum()

        importances.append(float(imp))

    importances = np.array(importances)
    importances = 100 * importances / importances.sum()

    return pd.DataFrame({
        "Attribute": attributes_list,
        "Importance": importances
    })



def _create_n_price_points(n):
    return np.linspace(MIN_PRICE, MAX_PRICE, n+1).round()  # Round to nearest 10 for aesthetics



def run_pricing_analysis(
    product_no,
    products_df,
    price_attr,
    n_price_points=50,
    include_none=True,
    respondent_ids=None,
    progress=None
):
    import numpy as np
    from scipy.interpolate import make_interp_spline

    # 1. Get the exact price points tested in the survey
    exact_prices = sorted(
        pd.to_numeric(
            grid_df[price_attr],
            errors="coerce"
        )
        .dropna()
        .unique()
    )

    if len(exact_prices) < 2:
        raise ValueError(
            f"Pricing analysis for '{price_attr}' requires "
            "at least two numeric price levels in the Excel Grid."
        )

    current_state = products_df.copy()
    results_list = []

    # 2. Calculate shares at each exact survey price point
    for i, price in enumerate(exact_prices):

        if progress is not None:
            progress.set(
                10 + (i / len(exact_prices)) * 20,
                message=(
                    f"Calculating {price_attr}: {price:,.2f}..."
                )
            )

        current_state.loc[
            current_state["ProductID"] == int(product_no),
            price_attr
        ] = float(price)

        shares = compute_shares(
            current_state,
            include_none=include_none,
            respondent_ids=respondent_ids
        )

        share_dict = {
            "Price point": float(price)
        }

        for _, row in shares.iterrows():

            product_id = row["ProductID"]

            if pd.notna(product_id):
                try:
                    product_id = str(int(float(product_id)))
                except (ValueError, TypeError):
                    product_id = str(product_id)

            share_dict[product_id] = row["PrefShare"]

        results_list.append(share_dict)

    exact_df = pd.DataFrame(results_list)

    # 3. Generate evenly spaced prices across this attribute's range
    smooth_prices = np.linspace(
        min(exact_prices),
        max(exact_prices),
        n_price_points
    )

    smooth_results = {
        "Price point": smooth_prices
    }

    # 4. Interpolate between the exact survey price points
    if progress is not None:
        progress.set(
            35,
            message="Building interpolated price curve..."
        )

    k_val = min(2, len(exact_prices) - 1)

    for col in exact_df.columns:

        if col == "Price point":
            continue

        spline = make_interp_spline(
            exact_df["Price point"],
            exact_df[col],
            k=k_val
        )

        smooth_results[col] = spline(smooth_prices)

    result_df = pd.DataFrame(smooth_results)

    print("Pricing attribute:", price_attr)
    print("Pricing result columns:", result_df.columns.tolist())
    print("Selected product:", product_no)

    return result_df


