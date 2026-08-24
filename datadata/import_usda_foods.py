#!/usr/bin/env python3
"""CLI wrapper for USDA food import."""

import argparse

from app.services.usda_import import import_foods


def main() -> None:
    parser = argparse.ArgumentParser(description="Import USDA/HF food catalog into food_items")
    parser.add_argument("--include-branded", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-replace", action="store_true")
    args = parser.parse_args()
    import_foods(
        include_branded=args.include_branded,
        limit=args.limit,
        replace=not args.no_replace,
    )


if __name__ == "__main__":
    main()
