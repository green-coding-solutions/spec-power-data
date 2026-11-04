#!/bin/bash
# Downloads all SPECpower_ssj2008 results (.html and .txt) and sorts them into spec-power-raw/:
#   spec-power-raw/text/ gets every result
#   spec-power-raw/html/ only gets Single Node results that have an "Active Idle" row
#                    (i.e. no Multi Node and no non-compliant results)
# Existing files are overwritten with the current version from spec.org. Nothing is deleted.
set -euo pipefail

spec_url="https://spec.org/power_ssj2008/results/power_ssj2008"
repo_dir="$(cd "$(dirname "$0")" && pwd)"
staging_dir="$(mktemp -d)"
trap 'rm -rf "$staging_dir"' EXIT

wget -nv -nd -r -l 1 -P "$staging_dir" -A 'power_ssj2008-*.html,power_ssj2008-*.txt' "$spec_url"

mkdir -p "$repo_dir/spec-power-raw/text" "$repo_dir/spec-power-raw/html"
for txt in "$staging_dir"/power_ssj2008-*.txt; do
    cp "$txt" "$repo_dir/spec-power-raw/text/"
    if grep -qE '^[[:space:]]*Test Method:[[:space:]]*Single Node' "$txt" && grep -q 'Active Idle' "$txt"; then
        cp "${txt%.txt}.html" "$repo_dir/spec-power-raw/html/"
    fi
done

echo "text: $(ls "$repo_dir/spec-power-raw/text" | wc -l) files, html: $(ls "$repo_dir/spec-power-raw/html" | wc -l) files"
