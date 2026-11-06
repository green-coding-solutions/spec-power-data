# spec-power-data

Raw data and the pipeline that turns it into the training data for the model in the
[cloud energy repo](https://github.com/green-coding-solutions/cloud-energy), where this repository is included as a submodule.

## SPECpower results

Just run `bash get_spec_data.sh` and it will get the newest version of the data.

It downloads all results from spec.org and puts them into `spec-power-raw/`:
- `spec-power-raw/text/` gets every result as `.txt`
- `spec-power-raw/html/` only gets the `.html` of Single Node results that have an "Active Idle" row
  (no Multi Node and no non-compliant results)

Existing files are overwritten with the current version from spec.org. Nothing is deleted.


## Building the training data

Both scripts use relative paths, so run them from inside `scripts/`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
cd scripts
python3 create_data_csv.py
python3 data_cleaning.py
```

- `create_data_csv.py` parses `spec-power-raw/html/` into `data/spec_data.csv`. It applies `data-updates/spec_data_patches.csv` and
  cuts off all results with a `Hardware Availability` older than 2018. The files in `spec-power-raw/` stay untouched, so
  the cut-off year can be changed with `MIN_HARDWARE_AVAILABILITY_YEAR`.
- `data_cleaning.py` builds `data/spec_data_cleaned_unmelted.csv` and `data/spec_data_cleaned.csv`. It gets the TDP
  from `cpu-spec-sheets/` and, for CPUs that are in no spec sheet, from `data-updates/cpu_tdp_lookup.csv`. It prints which results
  have no TDP, by year and by CPU. The results with no TDP keep an empty `TDP` column. The TDP matching from Wikipedia (`make_tdp_wikipedia`) is
  deactivated for now.

If the SPECpower data ever gets updated walk through `data_cleaning.py` manually from top to bottom.
It contains asserts with hard-coded counts and asks for visual checks on the way.

The cloud energy repo trains directly on `data/spec_data_cleaned.csv` from this repo. So commit the new data here and then
update the submodule pointer and the expected values of the tests in the cloud energy repo.


## TDP lookup (`data-updates/cpu_tdp_lookup.csv`)
SPECpower has no TDP, so `data_cleaning.py` adds it. It first matches the CPUs against the files in `cpu-spec-sheets/`.
This lookup file is only for the CPUs that are in no spec sheet. CPUs that are in a spec sheet must not be in here, and the
script fails if they are.

| Column | Content |
|---|---|
| `CPUName` | The normalized name that `data_cleaning.py` creates, e.g. `xeonplatinum8180` |
| `TDP` | TDP in Watts per CPU. Empty if it is not known yet |
| `Source` | The URL the TDP comes from. Must be set if there is a TDP |

### Every time new data is added: An LLM adds the new CPUs
Run the two scripts and give the output of `data_cleaning.py` to the LLM together with these instructions:

> `data_cleaning.py` printed the CPUs that are in no spec sheet and not in `data-updates/cpu_tdp_lookup.csv` yet.
> Add one row per CPU, with `CPUName` exactly as printed.
> - Use the product page of the vendor, and only then other sources, with the URL as `Source`.
> - If a CPU has a TDP range use the upper bound.
> - Never guess or estimate. If you find no source leave `TDP` and `Source` empty, but still add the row.
> - Do not change existing rows.

### Missing TDPs are scraped manually
Some TDPs will always be missing, as they are in no spec sheet (e.g. CPUs that Intel no longer lists).
These are the rows with an empty `TDP`, and `data_cleaning.py` prints them under "CPUs without TDP". Look them up on the
internet by hand and enter both the `TDP` and the URL as `Source`.


## Patches for broken results (`data-updates/spec_data_patches.csv`)
Some SPEC results contain wrong values, e.g. `1280 MB` L2 cache per core instead of `1280 KB`. The downloaded files are
overwritten by `get_spec_data.sh`, so we do not fix them there. `create_data_csv.py` overwrites the values while parsing.

| Column | Content |
|---|---|
| `Result_ID` | The name of the result file without extension. It is also the `Result_ID` column in `data/spec_data.csv` |
| `Column` | The column to overwrite, as named in `data/spec_data.csv`, e.g. `HW_SecondaryCache` |
| `Old_Value` | The current value. The script fails if it finds a different one, e.g. because SPEC changed the result |
| `New_Value` | The value to write |
| `Date` | When the patch was introduced |
| `Comment` | Why the value is wrong and how we know the new one |

Results older than the cut-off are also checked, so only add patches for results you use.


## CPU spec sheets (`cpu-spec-sheets/`)
The main source of the TDP. `data_cleaning.py` reads them directly.

### AMD (`amd_client.csv`, `amd_server.csv`)
Exported from the AMD processor specification pages on amd.com (last updated 2026-10-31):
- Client processors, in `amd_client.csv`: https://www.amd.com/en/products/specifications/processors.html
- Server processors (EPYC, Opteron), in `amd_server.csv`: https://www.amd.com/en/products/specifications/server-processor.html

amd.com does not serve these pages to scripts, but has a handy save icon on the top right.
Just download the CSV file of each page and replace the matching `amd_*.csv` file with it.

The files have one row per processor with the values as displayed on amd.com (e.g. `280W`).
The two files have different columns. Not every processor has a `Default TDP`: Newer EPYC models only
have a `Default CPU Power` (e.g. `600W (CPU Power Range: 400W-600W)`), a column which only exists in `amd_server.csv`.

### Intel (`intel.tsv`)
Manual export from the Intel ARK website.

Despite the file extension the columns are separated by four spaces and not by tabs.
A few rows only contain a product name.

Got to the [product filter](https://www.intel.com/content/www/us/en/ark/featurefilter.html?productType=873) page
and filter by TDP and use the lowest value of.

This should give you a list with all CPUs independent of architecture.

This was the URL at the time of writing: https://www.intel.com/content/www/us/en/ark/featurefilter.html?productType=873&3_MaxTDP-Min=0.03

Then click on *Load More* until 8 years ago. Older data is typically not relevant anymore and will be pruned later anyway.
