"""
shark.py — Shark Attack Dataset Cleaning Module
================================================
Ironhack Data Analytics Bootcamp | Week 2 Project
Team: Diana Carolina Yule Burbano & Irene Fafian

Business Case:
    A marine biology research institution needs to optimise when and where to
    deploy fieldwork teams. Using 26 years of global incident data (2000–2026),
    this analysis identifies the geographic locations and seasonal windows that
    maximise student exposure to real shark behaviour.

Hypotheses:
    H1 — Incidents cluster in specific geographic hotspots (Irene — pending)
    H2 — Incidents peak in summer months, hemisphere-adjusted (Diana — ✅ confirmed)

Usage:
    from shark import clean_shark_df, scope_modern_era
    shark_clean   = clean_shark_df("GSAF5.xls")
    shark_newera  = scope_modern_era(shark_clean)

Pipeline (clean_shark_df):
    Ch.1  load_data
    Ch.2  drop_irrelevant_columns
    Ch.3  check_and_drop_id_columns
    Ch.4  standardize_col_names
    Ch.5  clean_string_columns          (Country, State, Location, Fatality)
    Ch.6  clean_activity                (keyword map → 10 categories)
    Ch.7  clean_species                 (keyword map → 15 named species)
    Ch.8  standardize_type              (5 official GSAF categories)
    Ch.9  clean_dates                   (4-pass pipeline → year, month, season)
    Ch.10 finalize_columns              (drop raw date cols, lowercase all names)
    Ch.11 deduplicate_and_validate      (dedup, drop personal cols, date validation,
                                         artifact fix, null year cleanup)
    Ch.12 scope_modern_era              (filter to 2000 onwards — called separately)

PEP8 compliant. All functions are independently callable and importable.
"""

import logging
import pandas as pd
from dateutil import parser as dateutil_parser

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
    'Source', 'Injury', 'pdf', 'href formula', 'href',
    'original order', 'Unnamed: 21', 'Unnamed: 22'
]


def drop_irrelevant_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop columns with no analytical value for the business case.
    Technique: column dropping.

    Dropped: Source, Injury, pdf, href formula, href,
             original order, Unnamed: 21, Unnamed: 22

    Note: Age, Name, Sex are retained until after deduplication (Ch.11).

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
    Evaluate Case Number columns for uniqueness, then drop both.
    Technique: uniqueness check + column dropping.

    Neither 'Case Number' nor 'Case Number.1' is unique — both contain
    duplicates, so neither qualifies as a reliable primary key.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with Case Number columns removed.
    """
    for col in ['Case Number', 'Case Number.1']:
        if col in df.columns:
            n = df.duplicated(subset=[col]).sum()
            log.info("'%s' has %d duplicate values — dropping.", col, n)
    df = df.drop(columns=['Case Number', 'Case Number.1'], errors='ignore')
    return df


# ===========================================================================
# CHAPTER 4 — STANDARDIZE COLUMN NAMES
# ===========================================================================

def standardize_col_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strip whitespace and capitalize the first letter of each column name.
    Rename 'Fatal y/n' → 'Fatality'.
    Technique: column renaming.

    Note: Full lowercase is applied later in Ch.10 after date extraction.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with standardized column names.
    """
    df.columns = df.columns.map(lambda c: c.strip().capitalize())
    df.rename(columns={'Fatal y/n': 'Fatality'}, inplace=True)
    log.info("Column names standardized.")
    return df


# ===========================================================================
# CHAPTER 5 — CLEAN STRING COLUMNS
# ===========================================================================

def clean_string(value) -> str:
    """Strip whitespace and convert to uppercase. Returns None for nulls."""
    return None if pd.isnull(value) else str(value).strip().upper()


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
        else any(not (ch.isupper() or ch.isspace()) for ch in str(x))
    )
    return df[condition][column].value_counts()


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
    Strip + uppercase for Country, State, Location, Fatality.
    Apply country-specific normalization and manual mapping to Country.
    Technique: string cleaning + manual category mapping.

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
    Unify Activity column into 10 standard categories via keyword matching.
    Technique: keyword-based category mapping.

    Categories: FISHING, SWIMMING, SURFING, DIVING, BOATING, KAYAKING,
                STATIONARY, MARITIME ACCIDENT, OTHER, UNKNOWN

    Note: The next() iterator returns the first matching keyword. Key order
    in _ACTIVITY_MAP is intentional — more specific terms precede general ones.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with Activity standardized.
    """
    if 'Activity' not in df.columns:
        log.warning("'Activity' not found — skipping.")
        return df
    df['Activity'] = df['Activity'].apply(clean_string)
    df['Activity'] = df['Activity'].apply(_unify_activity)
    log.info("Activity: %d categories.", df['Activity'].nunique())
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
    Unify Species column into 15 named species + OTHER + UNKNOWN.
    Technique: keyword-based species mapping.

    Note: A significant share of records will remain UNKNOWN — this reflects
    the difficulty of species identification in incident field conditions,
    not a cleaning failure.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with Species standardized.
    """
    if 'Species' not in df.columns:
        log.warning("'Species' not found — skipping.")
        return df
    df['Species'] = df['Species'].apply(clean_string)
    df['Species'] = df['Species'].apply(_unify_species)
    log.info("Species: %d categories.", df['Species'].nunique())
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
        log.warning("'Type' not found — skipping.")
        return df
    df['Type'] = df['Type'].replace(_TYPE_MAP)
    log.info("Type standardized: %s", df['Type'].value_counts(dropna=False).to_dict())
    return df


# ===========================================================================
# CHAPTER 9 — DATE COLUMN CLEANING (Diana's multi-pass pipeline)
# ===========================================================================

_MONTHS = [
    'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december',
    'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
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
    Normalize a raw Date string toward a parseable format.
    Handles: ordinal suffixes, 'MonthName DD', 'DD-Mon-YYYY',
    'YYYY-Mon-DD', and dual-year ranges (returns midpoint).
    """
    if not isinstance(val, str):
        return val
    for s in ['st', 'nd', 'rd', 'th']:
        val = val.replace(s, '')
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
    parts_d = val.lower().replace('-', ' ').split()
    if len(parts_d) == 3:
        if parts_d[1] in _MONTHS and parts_d[2].isdigit() and len(parts_d[2]) == 4:
            return f"{parts_d[1]} {parts_d[2]}"
        if parts_d[0].isdigit() and len(parts_d[0]) == 4 and parts_d[1] in _MONTHS:
            return f"{parts_d[1]} {parts_d[0]}"
    return val


def month_year_f(df: pd.DataFrame, col_date: str) -> pd.DataFrame:
    """Apply month_year() to every value in col_date. Returns a copy."""
    df = df.copy()
    df[col_date] = df[col_date].apply(month_year)
    return df


def flex_dateparse(text: str):
    """
    Attempt fuzzy date parsing using dateutil.
    fuzzy=True ignores words like 'Reported', 'Ca.', 'Late'.
    Returns None on failure.
    """
    try:
        return dateutil_parser.parse(str(text), fuzzy=True)
    except Exception:
        return None


def smart_cleaner(df: pd.DataFrame, col_date: str) -> pd.DataFrame:
    """
    Apply flex_dateparse only to rows that pd.to_datetime cannot parse.
    Technique: fuzzy date parsing (dateutil).
    """
    df = df.copy()
    df['fdate_check'] = pd.to_datetime(df[col_date], errors='coerce', dayfirst=True)
    mask = df['fdate_check'].isnull()
    df.loc[mask, col_date] = df.loc[mask, col_date].apply(flex_dateparse)
    df = df.drop('fdate_check', axis=1)
    return df


def word_cleaner(df: pd.DataFrame, col_date: str, words_remove: list) -> pd.DataFrame:
    """
    Strip noise words from date strings that pd.to_datetime still cannot parse.
    Applied selectively — only to rows where parsing already failed.

    Args:
        df: Input DataFrame.
        col_date: Date column name.
        words_remove: List of noise word strings to remove.
    """
    df = df.copy()
    df['fdate_check'] = pd.to_datetime(df[col_date], errors='coerce', dayfirst=True)
    pattern = '|'.join(words_remove)
    mask = df['fdate_check'].isnull()
    df.loc[mask, col_date] = (
        df.loc[mask, col_date]
        .astype(str)
        .str.replace(pattern, '', regex=True)
        .str.strip()
    )
    df = df.drop('fdate_check', axis=1)
    return df


def recog_daytimef(df: pd.DataFrame, col_date: str) -> pd.DataFrame:
    """
    Convert parseable date strings to datetime objects.
    Rows that still fail remain as strings (errors='coerce' writes NaT).
    """
    df = df.copy()
    df['fdate_check'] = pd.to_datetime(df[col_date], errors='coerce', dayfirst=True)
    mask = df['fdate_check'].notna()
    df.loc[mask, 'Date'] = df.loc[mask, 'fdate_check']
    return df


def ext_year_month(date_val, fallback_year) -> tuple:
    """
    Extract (year, month) from a cleaned date value.
    Handles: datetime objects, parseable strings, month-name-only strings,
    and epoch artifacts (1970-01-01 with microsecond-encoded year).
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
        year = micro_str[-4:]
        return (int(year) if year.isdigit() else fallback_year), None
    return fallback_year, None


def clean_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Multi-pass date cleaning pipeline (Diana).
    Technique: regex noise removal + fuzzy parsing + epoch artifact handling.

    Pass 1: month_year_f  — normalize to 'Mon YYYY' format
    Pass 2a: smart_cleaner — fuzzy parse remaining strings (dateutil)
    Pass 2b: word_cleaner  — strip noise words from still-failing rows
    Pass 3: recog_daytimef — convert parseable strings to datetime objects
    Pass 4: ext_year_month — extract year_ext, month_ext; handle epoch artifacts
    Pass 5: Derive Season from month_ext for H2 analysis

    Args:
        df: Input DataFrame (must contain 'Date' and 'Year' columns).

    Returns:
        DataFrame with year_ext, month_ext, Season columns added.
    """
    if 'Date' not in df.columns:
        log.warning("'Date' not found — skipping date cleaning.")
        return df

    df = month_year_f(df, 'Date')
    df = smart_cleaner(df, 'Date')
    df = word_cleaner(df, 'Date', _WORDS_REMOVE)
    df = recog_daytimef(df, 'Date')

    df[['year_ext', 'month_ext']] = df.apply(
        lambda row: pd.Series(ext_year_month(row['Date'], row.get('Year'))),
        axis=1
    )
    df['Season'] = df['month_ext'].map(_SEASON_MAP)

    artifact_count = (df['year_ext'] == 0).sum()
    log.info(
        "Date cleaning done. year_ext/month_ext/Season added. "
        "Rows with year_ext == 0: %d", artifact_count
    )
    return df


# ===========================================================================
# CHAPTER 10 — COLUMN FINALIZATION
# ===========================================================================

def finalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop raw date/time columns superseded by year_ext/month_ext/Season.
    Rename year_ext → year, month_ext → month.
    Lowercase all column names for consistent downstream access.
    Technique: column cleanup + renaming.

    Dropped: Date, Year, Time, fdate_check

    Args:
        df: Input DataFrame (after clean_dates).

    Returns:
        DataFrame with finalized column names.
    """
    cols_drop = ['Date', 'Year', 'Time', 'fdate_check']
    df = df.drop(columns=cols_drop, errors='ignore')
    df = df.rename(columns={'year_ext': 'year', 'month_ext': 'month'})
    df.columns = df.columns.map(str.lower)
    log.info("Columns finalized: %s", list(df.columns))
    return df


# ===========================================================================
# CHAPTER 11 — DEDUPLICATION & VALIDATION
# ===========================================================================

def deduplicate_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Five-step final validation and cleanup pass.
    Technique: deduplication + date validation + artifact correction.

    Step 1: Remove fully duplicate rows
    Step 2: Drop personal columns (name, age, sex) — safe after dedup
    Step 3: Drop rows with no valid year AND no valid month
    Step 4: Fix year artifact 9955 → 1995 (epoch parsing error)
    Step 5: Drop the 2 remaining rows where year is null or 0

    Args:
        df: Input DataFrame (after finalize_columns — columns are lowercase).

    Returns:
        Validated DataFrame ready for scoping.
    """
    # Step 1
    n = df.duplicated().sum()
    if n > 0:
        df = df.drop_duplicates()
        log.info("Step 1: Removed %d duplicate rows.", n)
    else:
        log.info("Step 1: No duplicates found.")

    # Step 2
    personal = ['name', 'age', 'sex']
    df = df.drop(columns=[c for c in personal if c in df.columns], errors='ignore')
    log.info("Step 2: Personal columns dropped.")

    # Step 3
    no_date_mask = (
        (df['year'].isnull() | (df['year'] == 0)) &
        (df['month'].isnull() | (df['month'] == 0))
    )
    n_no_date = no_date_mask.sum()
    df = df.drop(index=df[no_date_mask].index)
    log.info("Step 3: Dropped %d rows with no valid year AND no valid month.", n_no_date)

    # Step 4
    bad_years = df[df['year'] > 2026]
    if len(bad_years) > 0:
        df['year'] = df['year'].replace(9955, 1995)
        log.info("Step 4: Corrected year artifact 9955 → 1995.")

    # Step 5
    null_year = df[df['year'].isnull() | (df['year'] == 0)]
    if len(null_year) > 0:
        df = df.drop(index=null_year.index).reset_index(drop=True)
        log.info("Step 5: Dropped %d rows with unresolvable year.", len(null_year))

    log.info("Validation complete. Shape: %d rows × %d columns", df.shape[0], df.shape[1])
    return df


# ===========================================================================
# CHAPTER 12 — SCOPE TO MODERN ERA
# ===========================================================================

def scope_modern_era(df: pd.DataFrame, year_from: int = 2000) -> pd.DataFrame:
    """
    Filter the cleaned dataset to year_from onwards (default: 2000).

    Rationale: Data quality and reporting consistency improve significantly
    from 2000 onwards. Earlier records have systematically higher rates of
    missing dates and incomplete location data. For fieldwork planning,
    recent decades are both more reliable and more relevant.

    Args:
        df: Cleaned DataFrame (output of clean_shark_df).
        year_from: Start year for the modern era filter (inclusive).

    Returns:
        Filtered DataFrame scoped to year_from–present.
    """
    df_modern = df[df['year'] >= year_from].copy().reset_index(drop=True)
    log.info(
        "Scoped to %d onwards: %d rows (from %d total).",
        year_from, len(df_modern), len(df)
    )
    return df_modern


# ===========================================================================
# ORCHESTRATOR
# ===========================================================================

def clean_shark_df(filepath: str) -> pd.DataFrame:
    """
    Full cleaning pipeline for the GSAF shark attack dataset.

    Returns shark_clean (all years after cleaning).
    Call scope_modern_era(shark_clean) separately to get shark_newera (2000+).

    Orchestration order:
        1.  load_data
        2.  drop_irrelevant_columns
        3.  check_and_drop_id_columns
        4.  standardize_col_names
        5.  clean_string_columns
        6.  clean_activity
        7.  clean_species
        8.  standardize_type
        9.  clean_dates                 → adds year_ext, month_ext, Season
        10. finalize_columns            → lowercase, drop raw date cols
        11. deduplicate_and_validate    → dedup, personal cols, artifacts

    Args:
        filepath: Path to GSAF5.xls.

    Returns:
        Fully cleaned DataFrame ready for scope_modern_era() and analysis.
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
    df = finalize_columns(df)
    df = deduplicate_and_validate(df)

    log.info(
        "=== Pipeline COMPLETE — %d rows × %d columns ===",
        df.shape[0], df.shape[1]
    )
    return df
