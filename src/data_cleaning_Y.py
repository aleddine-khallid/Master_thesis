import pandas as pd
import os

# reading GVA data
df_gva = pd.read_csv('raw_data/nama_10_a64.csv', sep=',')

# Filter for: Real Value Added (B1G) in Chain Linked Volumes
gva_clean = df_gva[
    (df_gva['na_item'] == 'B1G') & 
    (df_gva['unit'] == 'CLV10_MEUR')
].copy()
# keep only relevant columns
gva_clean = gva_clean[['geo', 'nace_r2', 'TIME_PERIOD', 'OBS_VALUE']]
gva_clean = gva_clean.rename(columns={'OBS_VALUE': 'GVA_Millions'})

print(f"GVA Data Loaded: {len(gva_clean)} rows")

# reading labor data

df_emp = pd.read_csv('raw_data/nama_10_a64_e.csv', sep=',')

df_emp.columns = df_emp.columns.str.lower()

emp_clean = df_emp[
    (df_emp['na_item'].isin(['ETO', 'EMP', 'EMP_DC'])) & 
    (df_emp['unit'] == 'THS_HW')
].copy()

emp_clean = emp_clean[['geo', 'nace_r2', 'time_period', 'obs_value']]
emp_clean = emp_clean.rename(columns={'obs_value': 'Hours_Thousands'})

print(f"Labor Data Loaded: {len(emp_clean)} rows")

print(emp_clean.head())

#merging GVA and Employment data
#lower case for columns
gva_clean.columns = gva_clean.columns.str.lower()
emp_clean.columns = emp_clean.columns.str.lower()

# we keep rows with both output and input
df_prod = pd.merge(
    gva_clean,
    emp_clean,
    on=['geo', 'nace_r2', 'time_period'],
    how='inner'
)

# Convert columns to numeric (coercing errors to NaN)
df_prod['gva_millions'] = pd.to_numeric(df_prod['gva_millions'], errors='coerce')
df_prod['hours_thousands'] = pd.to_numeric(df_prod['hours_thousands'], errors='coerce')

#drop na values
df_prod = df_prod.dropna(subset=['gva_millions', 'hours_thousands'])

print(f"Matched Rows (GVA + Labor): {len(df_prod)}")

# calculate productivity varaible
df_prod['labor_productivity'] = (df_prod['gva_millions'] / df_prod['hours_thousands']) * 1000

# safety check
df_prod = df_prod[
    (df_prod['hours_thousands'] > 0) & 
    (df_prod['labor_productivity'] > 0)
]

# FILTER NACE we keep only single letters like for ai scores

df_prod = df_prod[df_prod['nace_r2'].str.len() == 1]

print(f"Final Cleaned Rows (Single-Letter Sectors): {len(df_prod)}")
'''
#saving 
output_path = os.path.join('processed_data', 'labor_productivity_panel.csv')
df_prod.to_csv(output_path, index=False)

print("\n--- Sample of Final Productivity Data ---")
# Show 'geo', 'nace_r2', 'time_period', and the final calculation
print(df_prod[['geo', 'nace_r2', 'time_period', 'labor_productivity']].head(10))
'''

# reading AI scores
ai_file_path = os.path.join('processed_data', 'final_industry_ai_exposure.csv')

df_ai = pd.read_csv(ai_file_path)
print(f"Successfully loaded AI Scores from disk: {len(df_ai)} rows")

master_df = pd.merge(
        df_prod, 
        df_ai[['geo', 'nace_r2', 'AIIE_Index']], 
        on=['geo', 'nace_r2'],
        how='left'
    )
# Check how many rows have AI scores matched
master_df = master_df.dropna(subset=['AIIE_Index'])

print(f"Master Panel Size: {len(master_df)} rows")
'''
master_path = os.path.join('processed_data', 'master_dataset_final.csv')

master_df.to_csv(master_path, index=False)

print("\n--- SAMPLE ROW (Check that you have both Y and AI) ---")
print(master_df.head(1))
print(f"\nSUCCESS! Master dataset saved to: {master_path}")
'''