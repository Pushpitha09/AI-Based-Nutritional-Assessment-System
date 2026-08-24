#!/usr/bin/env bash
# Download IFCT 2017 compositions CSV (Indian Food Composition Tables, NIN Hyderabad).
set -euo pipefail
DIR="$(cd "$(dirname "$0")/../data/ifct2017" && pwd)"
mkdir -p "$DIR"
OUT="$DIR/compositions.csv"
if [[ -f "$OUT" ]]; then
  echo "IFCT CSV already present at $OUT"
  exit 0
fi
echo "Downloading IFCT 2017 compositions.csv..."
TMP=$(mktemp -d)
curl -sL "https://registry.npmjs.org/@ifct2017/compositions/-/compositions-2.0.9.tgz" | tar -xz -C "$TMP"
cp "$TMP/package/index.csv" "$OUT"
rm -rf "$TMP"
echo "Saved to $OUT ($(wc -l < "$OUT") lines)"
