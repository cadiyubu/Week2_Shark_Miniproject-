"""
shark.py — Shark Attack Dataset Cleaning Module
================================================
Ironhack Data Analytics Bootcamp | Week 2 Project
Authors: Diana Carolina Yule Burbano & Irene Fafian

Business Case:
    Marine biology research institution optimising fieldwork locations and timing
    based on historical shark incident data.

Hypotheses:
    H1 — Incidents cluster in specific coastal regions (geographic hotspots).
    H2 — Incidents peak during specific seasons (seasonal/behavioural patterns).
    H3 — Species variety vs. dominant-species quantity as incident predictor.

Usage:
    from shark import clean_shark_df
    clean_df = clean_shark_df("GSAF5.xls")

Structure (by chapter):
    Ch.1  load_data                  — read raw XLS
    Ch.2  drop_irrelevant_columns    — remove non-hypothesis columns
    Ch.3  check_and_drop_id_columns  — evaluate Case Number, then drop
    Ch.4  standardize_col_names      — strip + capitalize + rename Fatal y/n
    Ch.5  clean_string_columns       — Country, State, Location, Fatality
    Ch.6  clean_activity             — keyword-based activity unification
    Ch.7  clean_species              — keyword-based species unification
    Ch.8  standardize_type           — 5 official GSAF categories
    Ch.9  clean_dates                — multi-pass date parsing (Diana)
    Ch.10 check_duplicates           — deduplication
    Ch.11 clean_shark_df             — orchestrator (calls all steps)

PEP8 compliant. All functions independently callable and importable.
"""

import logging
import pandas as pd

# ---------------------------------------------------------------------------
# LOGGING SETUP
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger(__name__)


# ===========================================================================
# CHAPTER 1 — DATA LOADING
# ===========================================================================

def load_data(filepath: str) -> pd.DataFrame:
    """
    Load the GSAF Excel file into a DataFrame.

    Args:
        filepath: Relative or absolute path to GSAF5.xls

    Returns:
        Raw DataFrame as loaded from disk.

    Raises:
        FileNotFoundError: If the file does not exist at filepath.
    """
    try:
        df = pd.read_excel(filepath)
        log.info("Dataset loaded: %d rows × %d columns", df.shape[0], df.shape[1])
        return df
    except FileNotFoundError:
        log.error("File not found: %s", filepath)
        raise


# ===========================================================================
# CHAPTER 2 — DROP IRRELEVANT COLUMNS
# ===========================================================================

COLS_TO_DROP = [
    'Age', 'Name', 'Sex', 'Source', 'Injury', 'pdf',
    'href formula', 'href', 'original order',
    'Unnamed: 21', 'Unnamed: 22'
]


def drop_irrelevant_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop columns with no analytical value for the business case.
    Technique: column dropping.

    Dropped: Age, Name, Sex, Source, Injury, pdf, href formula, href,
             original order, Unnamed: 21, Unnamed: 22
    Rationale: confirmed in D1-PLAN.docx (YES/NO/MAYBE column list).

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with irrelevant columns removed.
    """
    present = [c for c in COLS_TO_DROP if c in df.columns]
    df = df.drop(columns=present, errors='ignore')
    log.info("Dropped %d irrelevant columns.", len(present))
    return df


# ===========================================================================
# CHAPTER 3 — CHECK AND DROP ID COLUMNS
# ===========================================================================

def check_and_drop_id_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluate Case Number columns for use as a primary key, then drop.
    Technique: deduplication check / column dropping.

    Neither 'Case Number' nor 'Case Number.1' is unique — both contain
    duplicates, so neither qualifies as a reliable index.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with Case Number columns removed.
    """
    for col in ['Case Number', 'Case Number.1']:
        if col in df.columns:
            dupes = df.duplicated(subset=[col]).sum()
            log.info("'%s' duplicates: %d — dropping.", col, dupes)
    df = df.drop(columns=['Case Number', 'Case Number.1'], errors='ignore')
    return df


# ===========================================================================
# CHAPTER 4 — STANDARDIZE COLUMN NAMES
# ===========================================================================

def standardize_col_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strip whitespace, capitalize first letter of each column name.
    Rename 'Fatal y/n' → 'Fatality'.
    Technique: column renaming.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with standardized column names.
    """
    df.columns = df.columns.map(lambda c: c.strip().capitalize())
    df.rename(columns={'Fatal y/n': 'Fatality'}, inplace=True)
    log.info("Column names standardized: %s", list(df.columns))
    return df


# ===========================================================================
# CHAPTER 5 — CLEAN STRING COLUMNS
# ===========================================================================

def clean_string(value) -> str:
    """
    Strip whitespace and convert to uppercase.
    Returns None for null values.
    """
    return value if pd.isnull(value) else str(value).strip().upper()


def find_weird_strings(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Identify values containing non-uppercase, non-space characters.
    Useful for spotting typos, punctuation, or encoding issues.

    Args:
        df: Input DataFrame.
        column: Column name to inspect.

    Returns:
        Value counts of strings with unexpected characters.
    """
    condition = df[column].apply(
        lambda x: False if pd.isnull(x)
        else any(not (char.isupper() or char.isspace()) for char in str(x))
    )
    return df[condition][column].value_counts()


# Manual mapping for ambiguous / multi-name country entries
_COUNTRY_MAP = {
    'ST KITTS ? NEVIS': 'SAINT KITTS AND NEVIS',
    'ST. MARTIN': 'SAINT MARTIN',
    'ST. MAARTIN': 'SAINT MARTIN',
    'TURKS & CAICOS': 'TURKS AND CAICOS ISLANDS',
    'TRINIDAD & TOBAGO': 'TRINIDAD AND TOBAGO',
    'UNITED ARAB EMIRATES (UAE)': 'UNITED ARAB EMIRATES',
    'ST HELENA, BRITISH OVERSEAS TERRITORY': 'SAINT HELENA',
    'CEYLON (SRI LANKA)': 'SRI LANKA',
    'ANDAMAN / NICOBAR ISLANDS': 'INDIA',
    'SUDAN?': 'SUDAN',
    'MID-PACIFC OCEAN': None,
    'ASIA': None,
    'INDIAN OCEAN': None,
    'RED SEA': None,
}


def _normalize_country(x: str) -> str:
    """Remove punctuation and geographic noise from country strings."""
    if pd.isna(x):
        return None
    x = x.replace('?', '').replace('.', '').replace('&', 'AND')
    if 'BETWEEN' in x:
        return None
    return x.split('/')[0].strip()


def clean_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply strip + uppercase to Country, State, Location, Fatality.
    Apply country-specific mapping and normalization to Country.
    Technique: string cleaning + manual mapping.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with string columns cleaned.
    """
    for col in ['Country', 'State', 'Location', 'Fatality']:
        if col in df.columns:
            before = df[col].nunique()
            df[col] = df[col].apply(clean_string)
            if col == 'Country':
                df[col] = df[col].replace(_COUNTRY_MAP)
                df[col] = df[col].apply(_normalize_country)
            log.info("'%s': %d → %d unique values after cleaning.", col, before, df[col].nunique())
    return df


# ===========================================================================
# CHAPTER 6 — CLEAN ACTIVITY COLUMN
# ===========================================================================

_ACTIVITY_MAP = {
    'fish': 'FISHING',
    'swim': 'SWIMMING',
    'bath': 'SWIMMING',
    'surf': 'SURFING',
    'board': 'SURFING',
    'div': 'DIVING',
    'ship': 'BOATING',
    'sail': 'BOATING',
    'boat': 'BOATING',
    'kayak': 'KAYAKING',
    'canoe': 'KAYAKING',
    'wading': 'STATIONARY',
    'stand': 'STATIONARY',
    'tread': 'STATIONARY',
    'capsize': 'MARITIME ACCIDENT',
    'sank': 'MARITIME ACCIDENT',
    'burn': 'MARITIME ACCIDENT',
    'drop': 'MARITIME ACCIDENT',
    'explo': 'MARITIME ACCIDENT',
    'fell': 'MARITIME ACCIDENT',
    'fall': 'MARITIME ACCIDENT',
}


def _unify_activity(x: str) -> str:
    """Map raw activity string to a standard category via keyword matching."""
    if pd.isna(x):
        return 'UNKNOWN'
    x_lower = str(x).lower()
    return next(
        (label for key, label in _ACTIVITY_MAP.items() if key in x_lower),
        'OTHER'
    )


def clean_activity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Unify Activity column into standard categories via keyword matching.
    Technique: keyword-based category mapping (regex-free, interpretable).

    Categories: FISHING, SWIMMING, SURFING, DIVING, BOATING, KAYAKING,
                STATIONARY, MARITIME ACCIDENT, OTHER, UNKNOWN

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with Activity standardized.
    """
    if 'Activity' not in df.columns:
        log.warning("Column 'Activity' not found — skipping.")
        return df

    df['Activity'] = df['Activity'].apply(clean_string)
    df['Activity'] = df['Activity'].apply(_unify_activity)
    log.info("Activity unified: %d categories.", df['Activity'].nunique())
    return df


# ===========================================================================
# CHAPTER 7 — CLEAN SPECIES COLUMN
# ===========================================================================

_SPECIES_MAP = {
    'great white': 'WHITE SHARK',
    'white': 'WHITE SHARK',
    'tiger': 'TIGER SHARK',
    'bull': 'BULL SHARK',
    'hammer': 'HAMMERHEAD SHARK',
    'blacktip': 'BLACKTIP SHARK',
    'mako': 'MAKO SHARK',
    'coral reef': 'REEF SHARK',
    'whitetip reef': 'REEF SHARK',
    'reef': 'REEF SHARK',
    'sand tiger': 'SAND SHARK',
    'sandbar': 'SAND SHARK',
    'sand shark': 'SAND SHARK',
    'blue': 'BLUE SHARK',
    'nurse': 'NURSE SHARK',
    'wobbegong': 'WOBBEGONG SHARK',
    'lemon': 'LEMON SHARK',
    'thresher': 'THRESHER SHARK',
}


def _unify_species(x: str) -> str:
    """Map raw species string to a standard name via keyword matching."""
    if pd.isna(x):
        return 'UNKNOWN'
    x_lower = str(x).lower()
    return next(
        (label for key, label in _SPECIES_MAP.items() if key in x_lower),
        'OTHER'
    )


def clean_species(df: pd.DataFrame) -> pd.DataFrame:
    """
    Unify Species column into named shark categories.
    Technique: keyword-based species mapping.

    Named species: WHITE SHARK, TIGER SHARK, BULL SHARK, HAMMERHEAD SHARK,
                   BLACKTIP SHARK, MAKO SHARK, REEF SHARK, SAND SHARK,
                   BLUE SHARK, NURSE SHARK, WOBBEGONG SHARK, LEMON SHARK,
                   THRESHER SHARK, OTHER, UNKNOWN

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with Species standardized.
    """
    if 'Species' not in df.columns:
        log.warning("Column 'Species' not found — skipping.")
        return df

    df['Species'] = df['Species'].apply(clean_string)
    df['Species'] = df['Species'].apply(_unify_species)
    log.info("Species unified: %d categories.", df['Species'].nunique())
    return df


# ===========================================================================
# CHAPTER 8 — STANDARDIZE TYPE COLUMN
# ===========================================================================

_TYPE_MAP = {
    'UNprovoked': 'Unprovoked',
    'unprovoked': 'Unprovoked',
    'UNPROVOKED': 'Unprovoked',
    'provoked': 'Provoked',
    'PROVOKED': 'Provoked',
    'Boatomg': 'Watercraft',
    'Invalid': 'Questionable',
}


def standardize_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize 'Type' column to 5 official GSAF categories.
    Technique: string mapping / typo correction.

    Official categories: Unprovoked, Provoked, Watercraft,
                         Sea Disaster, Questionable.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with Type standardized.
    """
    if 'Type' not in df.columns:
        log.warning("Column 'Type' not found — skipping.")
        return df

    df['Type'] = df['Type'].replace(_TYPE_MAP)
    log.info("Type standardized: %s", df['Type'].value_counts(dropna=False).to_dict())
    return df


# ===========================================================================
# CHAPTER 9 — DATE COLUMN CLEANING (Diana's multi-pass pipeline)
# ===========================================================================

_MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec"
]

_WORDS_REMOVE = [
    'Before', 'Reported', 'of', 'No date', 'Circa', 'Prior to',
    'After', 'or', 'late', 'A few years before', 'Between',
    'After Augu', 'before', 'Said to be'
]

_MONTH_MAP = {
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2,
    'mar': 3, 'march': 3, 'apr': 4, 'april': 4, 'ap': 4,
    'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
    'aug': 8, 'august': 8, 'augu': 8, 'sep': 9, 'september': 9,
    'oct': 10, 'october': 10, 'nov': 11, 'november': 11,
    'dec': 12, 'december': 12
}

_SEASON_MAP = {
    1: 'Winter', 2: 'Winter', 3: 'Spring', 4: 'Spring',
    5: 'Spring', 6: 'Summer', 7: 'Summer', 8: 'Summer',
    9: 'Autumn', 10: 'Autumn', 11: 'Autumn', 12: 'Winter'
}


def month_year(val: str) -> str:
    """
    Normalise messy date string toward 'Mon YYYY' or parseable format.
    Handles ordinal suffixes, 'MonthName DD', 'DD-Mon-YYYY', dual-year ranges.
    """
    if not isinstance(val, str):
        return val

    for s in ["st", "nd", "rd", "th"]:
        val = val.replace(s, "")
    val = val.strip()

    parts = val.lower().split()
    if len(parts) == 2:
        if parts[1].isdigit() and len(parts[1]) <= 2 and parts[0] in _MONTHS:
            return parts[0]
        if parts[0].isdigit() and len(parts[0]) <= 2 and parts[1] in _MONTHS:
            return parts[1]
        if (parts[0].isdigit() and parts[1].isdigit()
                and len(parts[0]) == 4 and len(parts[1]) == 4):
            return str(round((int(parts[0]) + int(parts[1])) / 2))

    parts_dash = val.lower().replace('-', ' ').split()
    if len(parts_dash) == 3:
        if parts_dash[1] in _MONTHS and parts_dash[2].isdigit() and len(parts_dash[2]) == 4:
            return f"{parts_dash[1]} {parts_dash[2]}"
        if parts_dash[0].isdigit() and len(parts_dash[0]) == 4 and parts_dash[1] in _MONTHS:
            return f"{parts_dash[1]} {parts_dash[0]}"

    return val


def month_year_f(df: pd.DataFrame, col_date: str) -> pd.DataFrame:
    """Apply month_year normalisation to a date column."""
    df = df.copy()
    df[col_date] = df[col_date].apply(month_year)
    return df


def word_cleaner(df: pd.DataFrame, col_date: str, words_remove: list) -> pd.DataFrame:
    """
    Remove known noise words from unparseable date strings.
    Only applied to rows where pd.to_datetime already failed.
    """
    df = df.copy()
    df['_fdate_check'] = pd.to_datetime(df[col_date], errors='coerce', dayfirst=True)
    pattern = '|'.join(words_remove)
    mask = df['_fdate_check'].isnull()
    df.loc[mask, col_date] = (
        df.loc[mask, col_date].str.replace(pattern, '', regex=True).str.strip()
    )
    df = df.drop(columns=['_fdate_check'])
    return df


def recog_daytimef(df: pd.DataFrame, col_date: str) -> pd.DataFrame:
    """
    Convert parseable date strings to datetime objects.
    Rows that fail parsing retain their string value (NaT in fdate_check).
    """
    df = df.copy()
    df['fdate_check'] = pd.to_datetime(df[col_date], errors='coerce', dayfirst=True)
    mask = df['fdate_check'].notna()
    df.loc[mask, col_date] = df.loc[mask, 'fdate_check']
    return df


def ext_year_month(date_val, fallback_year) -> tuple:
    """
    Extract (year, month) from a cleaned date value.
    Handles datetime objects, parseable strings, and epoch artifacts.
    Returns (fallback_year, None) for unresolvable entries.
    """
    date_str = str(date_val).strip().lower()

    parsed = pd.to_datetime(date_str, errors='coerce')
    if parsed is not pd.NaT and parsed.year != 1970:
        return parsed.year, parsed.month

    for name, num in _MONTH_MAP.items():
        if name in date_str:
            return fallback_year, num

    if '1970' in date_str and '.' in date_str:
        micro_str = date_str.split('.')[-1]
        year_str = micro_str[-4:]
        return (int(year_str) if year_str.isdigit() else fallback_year), None

    return fallback_year, None


def clean_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Multi-pass date cleaning pipeline (Diana's approach).
    Technique: regex noise removal + fuzzy date parsing + epoch artifact handling.

    Pass 1: Normalise to 'Mon YYYY' format (month_year)
    Pass 2: Strip noise words (Before, Circa, Reported, etc.)
    Pass 3: Convert parseable strings to datetime objects (recog_daytimef)
    Pass 4: Extract year_ext (int) and month_ext (int) from cleaned Date
    Pass 5: Derive Season (Winter/Spring/Summer/Autumn) for H2

    Args:
        df: Input DataFrame (must contain 'Date' and 'Year' columns).

    Returns:
        DataFrame with year_ext, month_ext, Season columns added.
    """
    if 'Date' not in df.columns:
        log.warning("Column 'Date' not found — skipping date cleaning.")
        return df

    df = month_year_f(df, 'Date')
    df = word_cleaner(df, 'Date', _WORDS_REMOVE)
    df = recog_daytimef(df, 'Date')

    df[['year_ext', 'month_ext']] = df.apply(
        lambda row: pd.Series(ext_year_month(row['Date'], row.get('Year', None))),
        axis=1
    )
    df['Season'] = df['month_ext'].map(_SEASON_MAP)

    unresolved = (df['year_ext'] == 0).sum()
    log.info(
        "Date cleaning done. year_ext/month_ext/Season added. "
        "Unresolved year_ext==0: %d rows.", unresolved
    )
    return df


# ===========================================================================
# CHAPTER 10 — DEDUPLICATION
# ===========================================================================

def check_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Check for and remove fully duplicate rows.
    Technique: deduplication.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with duplicate rows removed (if any found).
    """
    n_dupes = df.duplicated().sum()
    if n_dupes > 0:
        df = df.drop_duplicates()
        log.info("Removed %d fully duplicate rows.", n_dupes)
    else:
        log.info("No fully duplicate rows found.")
    return df


# ===========================================================================
# CHAPTER 11 — ORCHESTRATOR
# ===========================================================================

def clean_shark_df(filepath: str) -> pd.DataFrame:
    """
    Full cleaning pipeline for the GSAF shark attack dataset.

    Orchestration order (update this docstring when adding steps):
        1.  load_data                  — read raw XLS
        2.  drop_irrelevant_columns    — remove non-hypothesis columns
        3.  check_and_drop_id_columns  — evaluate + drop Case Number cols
        4.  standardize_col_names      — strip/capitalize + rename Fatal y/n
        5.  clean_string_columns       — Country, State, Location, Fatality
        6.  clean_activity             — keyword-based Activity unification
        7.  clean_species              — keyword-based Species unification
        8.  standardize_type           — 5 official GSAF Type categories
        9.  clean_dates                — multi-pass Date → year_ext/month_ext/Season
        10. check_duplicates           — deduplication

    Placeholders (to be added in future sprints):
        - Year column dtype fix (float → Int64)
        - Year range validation (filter/flag pre-1900 records)
        - Additional feature engineering before EDA

    Args:
        filepath: Path to GSAF5.xls.

    Returns:
        Fully cleaned DataFrame ready for EDA and hypothesis testing.
    """
    log.info("=== Shark Cleaning Pipeline START ===")

    df = load_data(filepath)
    df = drop_irrelevant_columns(df)
    df = check_and_drop_id_columns(df)
    df = standardize_col_names(df)
    df = clean_string_columns(df)
    df = clean_activity(df)
    df = clean_species(df)
    df = standardize_type(df)
    df = clean_dates(df)
    df = check_duplicates(df)

    log.info(
        "=== Shark Cleaning Pipeline COMPLETE — %d rows × %d columns ===",
        df.shape[0], df.shape[1]
    )
    return df
