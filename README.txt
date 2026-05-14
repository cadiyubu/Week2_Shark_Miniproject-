================================================================================
🦈 SHARK ATTACK INCIDENT ANALYSIS — PROJECT README
================================================================================
Ironhack Data Analytics Bootcamp | Week 2
Authors : Diana Carolina Yule Burbano & Irene Fafian
Dataset : Global Shark Attack File (GSAF5.xls) — sharkattackfile.net
Status  : ⚠️  DATA CLEANING PHASE — EDA & hypothesis validation pending
--------------------------------------------------------------------------------

================================================================================
1. PROJECT OVERVIEW
================================================================================

BUSINESS CASE
-------------
A marine biology research institution running master's and PhD programmes
needs to optimise where and when to deploy fieldwork teams. By analysing
historical shark incident data, it can focus resources on high-activity
coastal regions and peak seasonal periods — maximising student exposure to
real shark behaviour while managing risk.

HYPOTHESES
----------
H1 — Geographic Hotspots
     Shark incidents (provoked and unprovoked) cluster in specific coastal
     regions, indicating that environmental or ecological conditions make
     certain areas structurally higher-risk.
     Status: 📌 Pending EDA validation

H2 — Seasonal Patterns
     Incidents peak during specific times of year, consistent with known
     shark behavioural cycles: mating, migration, and feeding.
     Status: 📌 Pending EDA validation — year_ext/month_ext/Season columns ready

H3 — Species Diversity vs. Quantity
     A more varied species sample correlates differently with incident
     frequency than a single dominant species.
     Status: 📌 Pending EDA validation — Species column unified and ready

DATASET DESCRIPTION
-------------------
Source    : Global Shark Attack File (GSAF), sharkattackfile.net
File      : GSAF5.xls (included in repo)
Raw shape : 7,087 rows × 23 columns
Kept cols : Date, Year, Type, Country, State, Location,
            Activity, Fatality, Time, Species
            + derived: year_ext, month_ext, Season

Incident categories:
  - Unprovoked   : Shark initiated contact without human provocation
  - Provoked     : Human drew first blood (spearing, hooking, capturing)
  - Watercraft   : Boat bitten or rammed
  - Sea Disaster : Maritime or aviation accidents
  - Questionable : Insufficient data to confirm shark involvement


================================================================================
2. REPOSITORY STRUCTURE
================================================================================

Shark_project_week2/
│
├── GSAF5.xls                           ← Raw dataset (do not edit)
├── shark.py                            ← Cleaning module (importable, 11 chapters)
├── Shark_df_Analysis_DY.ipynb          ← Main analysis notebook (use this one)
├── Shark_df_Analysis_Notebook.ipynb    ← Colleague's original (reference only)
├── D1-PLAN.docx                        ← Project plan & hypothesis document
├── README.txt                          ← This file
└── anaconda_projects/
    └── db/                             ← SQL database files (pending)


================================================================================
3. INSTALLATION & DEPENDENCIES
================================================================================

Python    : 3.8+
Packages  :
  pandas          — data manipulation and cleaning
  openpyxl        — Excel file reading (required by pandas for .xls)
  python-dateutil — fuzzy date parsing (used in Ch.9 date cleaning)

Install all:
  pip install pandas openpyxl python-dateutil

Or with conda:
  conda install pandas openpyxl python-dateutil

Packages for future EDA phase (not yet needed):
  matplotlib, seaborn


================================================================================
4. HOW TO RUN
================================================================================

STEP 1 — Clone the repository
  git clone <repo-url>
  cd Shark_project_week2

STEP 2 — Install dependencies (see Section 3)

STEP 3 — Open the main notebook
  jupyter notebook Shark_df_Analysis_DY.ipynb

STEP 4 — Run all cells in order (Kernel → Restart & Run All)

HOW THE NOTEBOOK USES shark.py
  The notebook currently runs cleaning step-by-step inline for full transparency.
  shark.py consolidates the same logic into importable functions. To use the module:

    from shark import clean_shark_df
    clean_df = clean_shark_df("GSAF5.xls")

  This is equivalent to running all Section 4 cells in sequence.


================================================================================
5. CLEANING PROCESS — WHAT HAS BEEN DONE
================================================================================

NOTEBOOK: Shark_df_Analysis_DY.ipynb (Sections 3–4)
MODULE:   shark.py (Chapters 1–10)

Ch.1 / Sec 2 — Data Loading
  pd.read_excel() with relative path. Working copy (shark_clean) preserved
  separately from raw (shark_df).

Ch.2 / Sec 4.1 — Column Dropping
  Dropped 11 columns: Age, Name, Sex, Source, Injury, pdf, href formula,
  href, original order, Unnamed: 21, Unnamed: 22.
  Rationale: D1-PLAN.docx NO/MAYBE column classification.

Ch.3 / Sec 4.1b — ID Column Evaluation
  Case Number and Case Number.1 checked for uniqueness → both contain
  duplicates → neither suitable as primary key → both dropped.

Ch.4 / Sec 4.2 — Column Name Standardization
  strip().capitalize() applied to all column names.
  'Fatal y/n' renamed to 'Fatality'.

Ch.5 / Sec 4.3 — String Cleaning (Irene's work)
  Country: strip/uppercase + manual mapping (ambiguous names, punctuation,
           geographic non-countries set to None).
  State, Location: strip/uppercase.
  Fatality: strip/uppercase. Erroneous values flagged (F, M, NQ, 2017, Y X 2).
  Helper functions: clean_string(), find_weird_strings()

Ch.6 / Sec 4.3 — Activity Unification (Irene's work)
  ~700 unique raw values → 10 standard categories.
  Keyword-based mapping via next() iterator (FISHING, SWIMMING, SURFING,
  DIVING, BOATING, KAYAKING, STATIONARY, MARITIME ACCIDENT, OTHER, UNKNOWN).

Ch.7 / Sec 4.3 — Species Unification (Irene's work)
  ~300+ unique raw values → 15 named species + OTHER + UNKNOWN.
  Keyword-based mapping (WHITE SHARK, TIGER SHARK, BULL SHARK, etc.).
  Note: Many records are 'UNKNOWN' — this is a known data quality limitation.

Ch.8 / Sec 4.4 — Type Standardization
  Typos fixed (UNprovoked, Boatomg) → mapped to 5 official GSAF categories.

Ch.9 / Sec 4.5 — Date Cleaning (Diana's work)
  Multi-pass pipeline:
    Pass 1: month_year() — normalise to 'Mon YYYY' format, handle ordinal
             suffixes, 'MonthName DD', 'DD-Mon-YYYY', dual-year ranges.
    Pass 2: word_cleaner() — strip noise words (Before, Circa, Reported…)
             only from rows pd.to_datetime couldn't parse.
    Pass 3: recog_daytimef() — convert parseable strings to datetime objects.
    Pass 4: ext_year_month() — extract year_ext (int) and month_ext (int),
             handling epoch artifacts from numeric year-only strings.
    Pass 5: Season derived from month_ext map (for H2 temporal analysis).
  Result: year_ext, month_ext, Season columns added.

Ch.10 / Sec 4.6 — Deduplication
  check_duplicates() — fully duplicate rows removed (first kept).


================================================================================
6. WHAT IS STILL PENDING
================================================================================

📌 Section 4.7 — Year Dtype Fix
  Convert Year column float → Int64 (nullable integer).
  Validate year_ext range; flag/filter pre-1900 records if needed.

📌 Section 4.8 — Additional Transformations
  Any remaining feature engineering or data shaping before EDA.
  e.g. filtering to modern era (1950–present), binning years.

📌 Section 5 — EDA (Exploratory Data Analysis)
  Distribution of incident types, top countries, top activities,
  yearly trend (1900–present), monthly/seasonal distribution,
  species frequency breakdown.
  → Requires matplotlib / seaborn (not yet covered in course).

📌 Section 6 — Hypothesis Validation
  H1: Geographic aggregation — top countries / regions by incident count.
  H2: Monthly + seasonal distribution using month_ext / Season columns.
  H3: Species frequency and diversity analysis.

📌 Section 7 — Aggregation & Pivot Tables
  Country × Type cross-tabulation (heatmap or pivot table).
  Species × Incident Type breakdown.

📌 Section 8 — Key Insights & Conclusions
  To be filled after EDA and hypothesis validation are complete.

📌 SQL Component (anaconda_projects/db/)
  Normalized database schema (3NF minimum).
  Advanced SQL queries: CTEs, Window Functions, Subqueries.

📌 Presentation
  Final slides with actual charts and validated conclusions.
  Google Slides URL: [ADD BEFORE PRESENTATION DAY]


================================================================================
7. CLEANING SUMMARY TABLE
================================================================================

Step  | Column(s)                              | Technique               | Status
------|----------------------------------------|-------------------------|--------
4.1   | 11 columns                             | Column dropping         | ✅ Done
4.1b  | Case Number, Case Number.1             | ID check + drop         | ✅ Done
4.2   | All                                    | Name standardization    | ✅ Done
4.3a  | Country                                | String + manual mapping | ✅ Done
4.3b  | State, Location, Fatality              | String cleaning         | ✅ Done
4.3c  | Activity                               | Keyword category map    | ✅ Done
4.3d  | Species                                | Keyword species map     | ✅ Done
4.4   | Type                                   | Typo fix + category map | ✅ Done
4.5   | Date → year_ext, month_ext, Season     | Multi-pass date parsing | ✅ Done
4.6   | All                                    | Deduplication           | ✅ Done
4.7   | Year                                   | Dtype + range validation| 📌 Pending
4.8   | TBD                                    | Feature engineering     | 📌 Pending


================================================================================
8. BEST PRACTICES FOLLOWED (so far)
================================================================================

  ✅ PEP8 compliant Python throughout shark.py
  ✅ Modular design — each cleaning step is an independently callable function
  ✅ Logging with timestamps on all pipeline steps (shark.py)
  ✅ Error handling on file load (FileNotFoundError)
  ✅ Docstrings on all functions (Args / Returns / Technique label)
  ✅ Relative file paths — notebook runs on any machine with the repo
  ✅ Raw data preserved (shark_df); working copy always used (shark_clean)
  ✅ Helper functions defined once and reused across columns (clean_string,
     find_weird_strings, _unify_activity, _unify_species)
  ✅ Cleaning logic separated from analysis (shark.py is fully importable)
  ✅ Private helper functions marked with leading underscore (_unify_activity)


================================================================================
9. PRESENTATION
================================================================================

Google Slides URL : https://docs.google.com/presentation/d/1fUfaoPmaiCLCEeGMWcXY9B58B9Ye8q3P-nq9LP3NzME/edit?usp=sharing
Expected delivery : [X] minutes + [X] minutes Q&A

Slide structure:
  01 — Title (hook)
  02 — Business Problem
  03 — Dataset Overview
  04 — Cleaning Pipeline (what we built)
  05 — EDA Overview (📌 pending)
  06 — H1: Geographic Hotspots (📌 pending)
  07 — H2: Seasonal Patterns (📌 pending)
  08 — H3: Species Analysis (📌 pending)
  09 — Key Findings & Recommendations (📌 pending)
  10 — Q&A


================================================================================
END OF README
================================================================================
