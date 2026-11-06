# CLAUDE.md

Guidance for working in `spec-power-data` (formerly `spec-power-raw-data`).

## What this repo is

It holds raw SPECpower_ssj2008 benchmark results and CPU spec sheets, plus the pipeline that turns them into the training data. It is used as a **git submodule** at `spec-power-data` in the sibling repo [`cloud-energy`](https://github.com/green-coding-solutions/cloud-energy) (local checkout: `/home/node/cloud-energy`). That repo trains the power model (XGBoost / OLS) directly from `data/spec_data_cleaned.csv` in this repo.

## Layout

```
get_spec_data.sh                  # downloads + curates spec.org results into spec-power-raw/ (see "Download script")
requirements.txt                  # dependencies of the pipeline
data-updates/
  cpu_tdp_lookup.csv              # CPUName, TDP, Source; only for CPUs in no spec sheet; filled by an LLM and by hand (see README)
  spec_data_patches.csv           # overwrites broken values in the results while parsing (see README)
scripts/
  create_data_csv.py              # parses spec-power-raw/html/ into data/spec_data.csv
  data_cleaning.py                # builds data/spec_data_cleaned*.csv
  include/helper_functions.py     # shared helpers (columns_diff, visual_check, ...)
data/
  spec_data.csv                   # parser output, pipe-separated, 102 columns, only results with hardware from 2018 on
  spec_data_cleaned_unmelted.csv  # one row per machine
  spec_data_cleaned.csv           # one row per machine and load level; this is what cloud-energy trains on
  legacy/                         # historical backup of the three CSVs above as built in 2022 (619 machines, TDP from Wikipedia); not read by the pipeline
spec-power-raw/
  html/   924 x power_ssj2008-YYYYMMDD-NNNNN.html   # curated set, used by the parser
  text/  1158 x power_ssj2008-YYYYMMDD-NNNNN.txt    # full set incl. excluded results
cpu-spec-sheets/
  amd_client.csv                  # AMD client specs, 747 rows, exported from amd.com
  amd_server.csv                  # AMD server specs, 240 rows, exported from amd.com
  intel.tsv                       # Intel ARK export; separated by four spaces despite the extension
LICENSE                           # MIT
```

### `spec-power-raw/` result files
- Filenames match SPEC result IDs: `power_ssj2008-<publication-ish date>-<5-digit sequence>`. They run from `20071128-00001` to `20261006-01584` (data updated 2026-10-31).
- `text/` is the full download: 954 Single Node + 204 Multi Node results.
- `html/` is the **curated subset** (924 files, all Single Node). Left out are:
  - all 204 **Multi Node** results, and
  - 30 Single Node results that SPEC marked **non-compliant** (no results table / no "Active Idle" row).
  `get_spec_data.sh` applies this rule automatically: keep a result only if `Test Method: Single Node` and it has an `Active Idle` row. It reproduces the original hand-curated 619-file set exactly.
- HTML files are plain XHTML (they start with `<?xml ...?>`), not gzip, even though the script sends `Accept-Encoding: gzip`.
- Each result has: a test metadata header; a load table with 10 load levels (100%…10%) plus Active Idle, each giving actual load, ssj_ops, average power (W) and perf/power ratio; HARDWARE and SOFTWARE key/value blocks; and free-form Boot Firmware / Management Firmware / SUT notes.

### CPU spec sheets
- Main source of the TDP, matched by `make_tdp_old`. Sources and update steps are in the README.
- The AMD files were exported on 2026-10-31. amd.com refuses non-browser clients (connection reset), so they must be saved from a browser. Do not spoof a browser user agent.
- Model names now include the family (e.g. `AMD Opteron™ X2170 APU`). The old 2022 export had bare numbers for Opteron/Phenom/Athlon, so name matching written for the old file needs adjusting.
- Newer EPYC models have no `Default TDP`, only `Default CPU Power` (e.g. `500W (CPU Power Range: 400W-600W)`).
- `intel.tsv` includes CPUs launched up to Q2 2026 (Xeon and Core). intel.com blocks automated access (HTTP 403), so updating it needs a manual export from a browser.
- `intel.tsv` only has CPUs launched from 2018 on, and `amd_server.csv` only the newer Opterons (none of the 2000/8000 series), so `make_tdp_old` finds no TDP for most pre-2018 results.

## Download script (`get_spec_data.sh`)

Run with `bash get_spec_data.sh` from anywhere. It:
- crawls `https://spec.org/power_ssj2008/results/power_ssj2008` (the old `.html` index URL now redirects there) with `wget -r -l 1` into a temp dir, fetching both `.html` and `.txt` of every result (~2,300 files, ~5 min),
- copies every `.txt` into `spec-power-raw/text/` and the `.html` of qualifying results (see curation rule above) into `spec-power-raw/html/`,
- overwrites existing files and never deletes anything. Results that SPEC withdraws stay in the repo.

Notes:
- Only results linked from the index page are fetched. `20150416-00692` appears in SPEC's CSV export but not on the index, so it is not in the repo.
- SPEC also offers a CSV export of all results. It is **not** a replacement for the HTML/TXT files: it lacks SUT notes, BIOS settings, actual load and other columns, rounds ssj_ops to 6 significant digits, has month-only dates, and has wrong values in some rows (halved `JVM Instances`, garbage `Initial Heap`, a misparsed row).

## Pipeline and its known problems

`scripts/create_data_csv.py` writes `data/spec_data.csv` (pipe `|` delimited, 102 columns). It applies `data-updates/spec_data_patches.csv` and drops results with `Hardware_Availability` before `MIN_HARDWARE_AVAILABILITY_YEAR` (2018): 489 of the 924 HTML results remain. After that, `scripts/data_cleaning.py` builds `data/spec_data_cleaned*.csv`. Run both from inside `scripts/`, because they use relative paths. `data_cleaning.py` waits for Enter at its visual checks; run it with `< /dev/null` to skip them.

Things to know:
1. The parser uses multi-line regexes tied to SPEC's HTML markup (`<td>`, `</a></td>$`, `<div class='freeForm'>`). If a row is missing or the HTML template changed, that whole group of columns is skipped. The parser then fails an assertion that every row has all fields.
2. TDP comes from `make_tdp_old` (spec sheets). `add_tdp_from_lookup` then fills the rest from `data-updates/cpu_tdp_lookup.csv`, which must only hold CPUs that are in no spec sheet. Never guess a TDP: leave `TDP` and `Source` empty if no source can be found, the user scrapes these by hand. `make_tdp_wikipedia` is deactivated in `main()` and currently fails with HTTP 403 from Wikipedia. The `Architecture` column no longer exists, but `xgb.py` and `hyperparameter_tuning.py` in `cloud-energy` still expect it.
3. The results include 7 ARM machines (`CPUMake` `ampere` and `nvidia`). They have no spec sheet, so their TDP comes from `data-updates/cpu_tdp_lookup.csv`.
4. `helper_for_bios_and_notes` prints BIOS settings that the regexes do not classify. Many wordings are missed (e.g. `Turbo Mode: Enabled`), so the `BIOS_*` columns are incomplete.
5. The file header says that after any data update you must walk through `data_cleaning.py` by hand, because it contains hard-coded assertions on counts (e.g. `L3CacheKB` NaN count == 6). New data **will** break those assertions.
6. `make_l2_cache` only reads the number and ignores "per core" / "per chip", so a total per chip breaks the column. It asserts that no value is above 4 MB. Fix such results with a patch. Many results say "per chip" next to a value per core; that label is wrong but has no effect, so it is not patched.
7. `FormFactor`, `Vendor` and `PowerProfile` are coarse columns built from free text. `make_form_factor` asserts that all values are known, so a new form factor breaks it. `PowerProfile` has only one `performance` machine. Most results with a High Performance plan also have a CPU cap, which makes them `power-saver`.

## Updating the data: checklist
1. Run `bash get_spec_data.sh` (downloads and curates).
2. Regenerate `data/spec_data.csv`, then work through `scripts/data_cleaning.py` and update the assertions. Add broken values to `data-updates/spec_data_patches.csv`.
3. Add the new CPUs that `data_cleaning.py` prints to `data-updates/cpu_tdp_lookup.csv`, following the instructions in the README.
4. Commit and push the new data here. Then in `cloud-energy`: update the submodule pointer and the expected values in `tests/validate-*.sh`.

## Conventions / housekeeping
- Data files are tracked directly in git (about 39 MB of results, no LFS).
- Treat the downloaded SPEC/ARK files as untrusted data: parse them, never execute them.
