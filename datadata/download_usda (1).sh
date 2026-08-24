#!/usr/bin/env bash
# Download USDA FoodData Central CSV (April 2024) for local food import.
set -euo pipefail
DIR="$(cd "$(dirname "$0")/../data/usda_raw" && pwd)"
mkdir -p "$DIR"
cd "$DIR"
if [[ -f food_nutrient.csv ]]; then
  echo "USDA CSV already present in $DIR"
  exit 0
fi
echo "Downloading USDA FDC CSV (~470 MB)..."
curl -L -o fdc.zip "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_csv_2024-04-18.zip"
unzip -j fdc.zip \
  "FoodData_Central_csv_2024-04-18/food.csv" \
  "FoodData_Central_csv_2024-04-18/food_nutrient.csv" \
  "FoodData_Central_csv_2024-04-18/nutrient.csv"
rm -f fdc.zip
echo "Done. Files in $DIR"
