#!/usr/bin/env bash
set -euo pipefail

package_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
package_name="$(basename -- "$package_dir")"
archive_path="$package_dir/dev/$package_name.zip"
temp_dir="$(mktemp -d "$package_dir/dev/.package.XXXXXX")"
trap 'rm -rf -- "$temp_dir"' EXIT

# Build a fresh archive so deleted files cannot survive from an earlier run.
cd -- "$package_dir/.."
zip -qr "$temp_dir/$package_name.zip" "$package_name" \
    -x "$package_name/dev/*" '*/.*'
mv -- "$temp_dir/$package_name.zip" "$archive_path"

printf 'Created %s\n' "$archive_path"
