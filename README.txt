================================================================================
🦈 SHARK ATTACK INCIDENT ANALYSIS — PROJECT README
================================================================================
Ironhack Data Analytics Bootcamp | Week 2
Team    : Diana Carolina Yule Burbano & Irene Fafian
Dataset : Global Shark Attack File (GSAF5.xls) — sharkattackfile.net
Status  : ✅ Cleaning complete · ✅ H2 validated · 📌 H1 pending (Irene)
--------------------------------------------------------------------------------

================================================================================
1. BUSINESS CASE & HYPOTHESES
================================================================================

BUSINESS CASE
  A marine biology research institution running master's and PhD programmes
  needs to optimise when and where to deploy fieldwork teams. Using 26 years
  of global incident data (2000–2026), this analysis identifies the geographic
  locations and seasonal windows that maximise student exposure to real shark
  behaviour.

HYPOTHESES
  H1 — Geographic Hotspots (📌 Irene — pending)
       Shark incidents cluster in specific coastal regions, suggesting that
       certain areas are structurally higher-risk due to environmental or
       ecological conditions.

  H2 — Seasonal Patterns (✅ Diana — confirmed)
       Shark incidents concentrate in the summer months of each country's
       local hemisphere. Pattern is stable across all 5-year windows (2000–2026).
       Confirmed via pivot table × peak season analysis × trend stability test.


================================================================================
2. KEY FINDINGS (H2 — Confirmed)
================================================================================

The top 5 countries (USA, Australia, South Africa, Bahamas, Brazil) show a
consistent seasonal pattern when interpreted hemisphere-correctly:

  Country         Peak Season (label)   Calendar months   Hemisphere
  ──────────────────────────────────────────────────────────────────
  USA             Winter                Dec – Feb         Northern
  Australia       Summer                Dec – Feb         Southern
  South Africa    Summer                Dec – Feb         Southern
  Bahamas         Summer / Winter       Jun–Aug & Dec–Feb Tropical
  Brazil          Summer                Dec – Feb         Southern

KEY INSIGHT: The apparent difference in season labels is not a contradiction —
it is a confirmation. Both groups peak in their local summer: warm water +
maximum human water activity = highest encounter probability.

FIELDWORK RECOMMENDATION:
  Southern Hemisphere (Australia, South Africa, Brazil): deploy Dec – Feb
  Northern Hemisphere (USA): deploy Jun – Aug

This pattern is stable across all five 5-year windows from 2000 to 2026.


================================================================================
3. REPOSITORY STRUCTURE
================================================================================

Shark_project_week2/
│
├── GSAF5.xls                    ← Raw dataset (do not modify)
├── shark.py                     ← Cleaning module — 12 chapters, fully importable
├── Shark_df_Analysis.ipynb      ← Main analysis notebook (single source of truth)
├── D1-PLAN.docx                 ← Project plan and hypothesis document
├── README.txt                   ← This file
└── anaconda_projects/
    └── db/                      ← SQL component (pending)

RETIRED FILES (kept for reference, do not use for analysis):
  Shark_df_Analysis_DY.ipynb         ← Diana's working notebook (superseded)
  Shark_df_Analysis_Notebook.ipynb   ← Irene's working notebook (superseded)
  Shark_df_Analysis_MERGED.ipynb     ← Intermediate merge (superseded)


================================================================================
4. INSTALLATION & DEPENDENCIES
================================================================================

Python  : 3.8+
Required:
  pandas          — data manipulation
  openpyxl        — Excel file reading (required by pandas for .xls)
  python-dateutil — fuzzy date parsing (used in date cleaning pipeline)

Install:
  pip install pandas openpyxl python-dateutil

Future (EDA visualisation — not yet needed):
  pip install matplotlib seaborn


================================================================================
5. HOW TO RUN
================================================================================

OPTION A — Run the full notebook:
  1. jupyter notebook Shark_df_Analysis.ipynb
  2. Kernel → Restart & Run All

OPTION B — Import the cleaning module:
  from shark import clean_shark_df, scope_modern_era
  shark_clean  = clean_shark_df("GSAF5.xls")   # full cleaned dataset
  shark_newera = scope_modern_era(shark_clean)  # 2000–2026 analysis dataset


================================================================================
6. CLEANING PIPELINE — WHAT WAS DONE
================================================================================

All 12 chapters of shark.py correspond to sequential steps in the notebook (Sec 4).

Ch.1  load_data
      pd.read_excel() with error handling. Raw preserved as shark_df; all
      cleaning performed on shark_clean.

Ch.2  drop_irrelevant_columns
      Dropped: Source, Injury, pdf, href formula, href, original order,
      Unnamed: 21, Unnamed: 22.
      Note: Age, Name, Sex retained until after deduplication.

Ch.3  check_and_drop_id_columns
      Case Number and Case Number.1 checked for uniqueness → both contain
      duplicates → neither is a reliable primary key → both dropped.

Ch.4  standardize_col_names
      strip().capitalize() on all names. 'Fatal y/n' → 'Fatality'.

Ch.5  clean_string_columns  [Irene]
      Country: strip + uppercase + manual mapping (abbreviations, punctuation,
               geographic non-countries → None).
      State, Location: strip + uppercase.
      Fatality: strip + uppercase. Erroneous values (M, F, NQ, 2017, Y X 2)
               flagged but retained (do not affect seasonal analysis).

Ch.6  clean_activity  [Irene]
      ~700 unique raw values → 10 standard categories via keyword matching.
      Categories: FISHING, SWIMMING, SURFING, DIVING, BOATING, KAYAKING,
                  STATIONARY, MARITIME ACCIDENT, OTHER, UNKNOWN.

Ch.7  clean_species  [Irene]
      ~300+ unique raw values → 15 named species + OTHER + UNKNOWN via
      keyword matching.
      Note: High UNKNOWN share is a dataset characteristic (field reporting
      limitation), not a cleaning failure.

Ch.8  standardize_type  [Irene]
      Typos fixed (UNprovoked, Boatomg). 5 official categories enforced:
      Unprovoked, Provoked, Watercraft, Sea Disaster, Questionable.

Ch.9  clean_dates  [Diana — 4-pass pipeline]
      Pass 1 — month_year_f(): normalize to 'Mon YYYY' format; handle
               ordinal suffixes, 'MonthName DD', 'DD-Mon-YYYY', dual-year
               ranges.
      Pass 2a — smart_cleaner(): fuzzy parse remaining strings with dateutil.
      Pass 2b — word_cleaner(): strip noise words (Before, Circa, Reported…)
                from rows that still fail.
      Pass 3 — recog_daytimef(): convert parseable strings to datetime objects.
      Pass 4 — ext_year_month(): extract year_ext + month_ext; handle epoch
               artifacts (1970-01-01 microsecond encoding).
      Season derived from month_ext map for H2 temporal analysis.

Ch.10 finalize_columns  [Diana]
      Drop: Date, Year, Time, fdate_check.
      Rename: year_ext → year, month_ext → month.
      Lowercase all column names.

Ch.11 deduplicate_and_validate  [Diana]
      Step 1: Remove fully duplicate rows.
      Step 2: Drop personal columns (name, age, sex).
      Step 3: Drop rows with no valid year AND no valid month.
      Step 4: Fix year artifact 9955 → 1995 (confirmed vs. raw data, row 5096).
      Step 5: Drop 2 rows where year is still null/0 after all steps.

Ch.12 scope_modern_era  [Diana]
      Filter to year >= 2000. Returns shark_newera for analysis.
      Rationale: pre-2000 data has systematically higher rates of missing
      dates and incomplete location data.


================================================================================
7. FINAL DATASET SUMMARY
================================================================================

  Raw dataset (shark_df):     7,087 rows × 23 columns
  After cleaning (shark_clean): ~[N] rows × 10 columns
  Modern era (shark_newera):    ~[N] rows × 10 columns (2000–2026)

  Final columns (lowercase):
    country, state, location, fatality, activity, species, type,
    year, month, season

  Derived columns (from Date pipeline):
    year    ← integer extracted from Date/Year
    month   ← integer 1–12
    season  ← Winter / Spring / Summer / Autumn


================================================================================
8. EDA & ANALYSIS — CURRENT STATUS
================================================================================

  ✅ Sec 4   — Full cleaning pipeline (all 11 steps)
  ✅ Sec 4.7 — Scope to modern era (shark_newera, 2000–2026)
  ✅ Sec 5   — Seasonal analysis (null check, mode imputation, pivot table,
               peak season per country, 5-year trend stability)
  ✅ Sec 6   — H2 validated and verdict documented
  📌 Sec 5   — Type / Activity / Country frequency distributions (code ready,
               visualisation pending matplotlib module)
  📌 Sec 6   — H1 validation (Irene — to be merged via GitHub)
  📌 Sec 7   — Country × Type pivot table (Irene — part of H1)
  📌 Sec 8   — H1 conclusions (Irene — after validation)
  📌 SQL     — anaconda_projects/db/ schema and queries (pending)


================================================================================
9. BEST PRACTICES FOLLOWED
================================================================================

  ✅ PEP8 compliant Python throughout shark.py
  ✅ Modular design — each cleaning step is an independently callable function
  ✅ Logging with timestamps on all pipeline steps (shark.py)
  ✅ Error handling on file load (FileNotFoundError)
  ✅ Docstrings on all functions: Args / Returns / Technique / Notes
  ✅ Raw data preserved (shark_df); working copy always used (shark_clean)
  ✅ Relative file paths — notebook runs on any machine that clones the repo
  ✅ Cleaning separated from analysis — shark.py is fully importable
  ✅ Private helpers marked with leading underscore
  ✅ Two separate output frames: shark_clean (all years) + shark_newera (2000+)


================================================================================
10. PRESENTATION
================================================================================

  Google Slides URL : [https://docs.google.com/presentation/d/1QtL4MvRi6QmxbolRUTPduIxlkL1DDWuBDpbejwQGWbg/edit?slide=id.p9#slide=id.p9]
  

  Slide structure:
    01 — Title: "Where the Ocean Bites Back"
    02 — Business Problem
    03 — Dataset Overview
    04 — Cleaning Pipeline (Diana + Irene contributions)
    05 — Three Hypotheses
    06 — EDA: Seasonal Analysis (active results)
    07 — H2: Seasonal Patterns → ✅ CONFIRMED
    08 — H1: Geographic Hotspots → 📌 Pending
    09 — Key Findings & Fieldwork Recommendations
    10 — Q&A


================================================================================
END OF README
================================================================================
