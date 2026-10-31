# spec-power-raw-data
Raw data to be used as submodule in [cloud energy repo](https://github.com/green-coding-solutions/cloud-energy)

## SPECpower results
Just run `bash get_spec_data.sh` and it will get the newest version of the data.

It downloads all results from spec.org and puts them into `spec-power/`:
- `spec-power/text/` gets every result as `.txt`
- `spec-power/html/` only gets the `.html` of Single Node results that have an "Active Idle" row
  (no Multi Node and no non-compliant results)

Existing files are overwritten with the current version from spec.org. Nothing is deleted.


## CPU spec sheets (`cpu_spec_sheets/`)
Used to look up the TDP of the CPUs in the SPECpower results.

### AMD (`amd.csv`)
Generated from the AMD processor specification pages on amd.com (last updated 2026-10-31):
- Client processors: https://www.amd.com/en/products/specifications/processors.html
- Server processors (EPYC, Opteron): https://www.amd.com/en/products/specifications/server-processor.html

amd.com does not serve these pages to scripts, but has a handy save icon on the top right.
Just download the CSV files, merge them and update the `amd_*.csv` files with it

The pages embed all products as JSON. The script writes one row per processor with the values
as displayed on amd.com (e.g. `280W`). The `Segment` column says which page a processor came from.
Newer EPYC models (e.g. EPYC 9005 "F" parts) have no `Default TDP`, only a `Default CPU Power`.

### Intel (`intel.tsv`)
Manual exports from the Intel ARK website.

Got to the [product filter](https://www.intel.com/content/www/us/en/ark/featurefilter.html?productType=873) page
and filter by TDP and use the lowest value of.

This should give you a list with all CPUs independent of architecture.

This was the URL at the time of writing: https://www.intel.com/content/www/us/en/ark/featurefilter.html?productType=873&3_MaxTDP-Min=0.03

Then click on *Load More* until 8 years ago. Older data is typically not relevant anymore and will be pruned later anyway.
