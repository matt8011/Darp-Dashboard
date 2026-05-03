import pandas as pd
import sys
import os

os.chdir(r"C:\Users\mkyle\OneDrive\Desktop\darp dashboard")

yoy_data = pd.read_excel("data files/YoY Data Sheet (1).xlsx", sheet_name=None)
yoy_master = pd.read_excel("data files/YoY Master Sheet (1).xlsx", sheet_name=None)

print("="*100)
print("YoY DATA SHEET (1).xlsx")
print("="*100)
print(f"Sheets: {list(yoy_data.keys())}\n")

for sheet_name in yoy_data.keys():
    df = yoy_data[sheet_name]
    print(f"\n### {sheet_name} ###")
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"Columns ({len(df.columns)}):", end=" ")
    cols = [f"Col_{i}" if pd.isna(c) else str(c)[:40] for i, c in enumerate(df.columns)]
    print(cols)
    
    if len(df) > 0:
        print(f"Sample data (first 2 rows):")
        for i in range(min(2, len(df))):
            vals = [str(v)[:25] for v in df.iloc[i].values]
            print(f"  Row {i}: {vals}")
    
    # Check for unique values in key columns that might indicate data structure
    if len(df) > 0 and df.shape[1] > 0:
        print(f"Unique values in first column (sample): {df.iloc[:5, 0].unique()}")

print("\n" + "="*100)
print("YoY MASTER SHEET (1).xlsx")
print("="*100)
print(f"Sheets: {list(yoy_master.keys())}\n")

for sheet_name in yoy_master.keys():
    df = yoy_master[sheet_name]
    print(f"\n### {sheet_name} ###")
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"Columns ({len(df.columns)}):", end=" ")
    cols = [f"Col_{i}" if pd.isna(c) else str(c)[:40] for i, c in enumerate(df.columns)]
    print(cols)
    
    if len(df) > 0:
        print(f"Sample data (first 2 rows):")
        for i in range(min(2, len(df))):
            vals = [str(v)[:25] for v in df.iloc[i].values]
            print(f"  Row {i}: {vals}")
    
    if len(df) > 0 and df.shape[1] > 0:
        print(f"Unique values in first column (sample): {df.iloc[:5, 0].unique()}")

