from pathlib import Path

import pandas as pd

catalog_path = Path(
    "data/raw/product_catalog/translated/product_catalog_en.xlsx"
)

df = pd.read_excel(catalog_path)

print("=" * 50)
print("Shape")
print(df.shape)

print("\nColumns")
print(df.columns.tolist())

print("\nMissing Values")
print(df.isna().sum())

text_columns = [
    "User Manual",
    "Main ingredients",
    "Usage and dosage",
    "Corresponding crops/plants",
]

for col in text_columns:
    lengths = df[col].astype(str).str.len()

    print("\n" + "=" * 50)
    print(col)

    print("Min:", lengths.min())
    print("Avg:", round(lengths.mean()))
    print("Max:", lengths.max())


    print("\nDuplicate English Names:")
    print(df["English name"].duplicated().sum())

    categories_df = pd.read_excel(
    "data/raw/product_catalog/translated/product_categories_en.xlsx"
    )

    print(categories_df.shape)

    print(categories_df.columns.tolist())

    print(
    categories_df.head()
    )
    catalog_names = set(
    df["English name"]
    .astype(str)
    .str.strip()
)

category_names = set(
    categories_df["Product Name"]
    .astype(str)
    .str.strip()
)

print(
    "Matched:",
    len(catalog_names & category_names)
)

print(
    "Catalog:",
    len(catalog_names)
)

print(
    "Categories:",
    len(category_names)
)

duplicates = df[
    df["English name"].duplicated(keep=False)
]

print(
    duplicates[
        ["Product ID", "English name"]
    ]
)

catalog_names = set(
    df["English name"]
    .astype(str)
    .str.strip()
)

category_names = set(
    categories_df["Product Name"]
    .astype(str)
    .str.strip()
)

matched = catalog_names & category_names

print("Matched:", len(matched))
print("Categories:", len(category_names))

print(
    "\nProducts in Categories but NOT in Catalog:"
)

missing = category_names - catalog_names

for name in sorted(list(missing))[:20]:
    print(name)

print('###################################')
print(
    df["Instructions for use (dilute with water)"]
    .str.len()
    .describe()
)