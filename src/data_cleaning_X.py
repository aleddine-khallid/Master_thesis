import pandas as pd
import os

# EUROSTAT DATA
df = pd.read_csv('raw_data/lfsa_eisn2__custom_19083881_linear_2_0.csv', sep=',')

# force string for job mames columns
df['nace_r2'] = df['nace_r2'].astype(str)
df['isco08'] = df['isco08'].astype(str)

# make OBS_VALUE value as numeric 
df['OBS_VALUE'] = pd.to_numeric(df['OBS_VALUE'], errors='coerce')

# apply filter for  2022 and clean rows without industry or occupation codes
df_filtered = df[
    (df['TIME_PERIOD'] == 2022) & 
    (df['nace_r2'].notna()) &     
    (df['isco08'].notna())        
].copy()

# filter needed columns
cols_to_keep = ['nace_r2', 'isco08', 'TIME_PERIOD', 'OBS_VALUE', 'geo']
df_filtered = df_filtered[cols_to_keep]

print("Eurostat Data (Filtered 2022) Head:")
print(df_filtered.head())
print("-" * 30)


# CROSSWALK DATA 
df_2 = pd.read_csv('raw_data/isco_soc_crosswalk_T.csv', skiprows=6, sep=';')
cols_to_drop = ['part', 'Comment 8/17/11']
df_cross_walk = df_2.drop(columns=cols_to_drop)

# renaming coluns needed for merging later 
df_cross_walk = df_cross_walk.rename(columns={
    '2010 SOC Code': 'soc_code',
    'ISCO-08 Code': 'isco08_code'
})

# force string for job names columns
df_cross_walk['soc_code'] = df_cross_walk['soc_code'].astype(str)
df_cross_walk['isco08_code'] = df_cross_walk['isco08_code'].astype(str)

print("Crosswalk Head:")
print(df_cross_walk.head())
print("-" * 30)


# AI SCORES DATA 
df_scores = pd.read_csv('raw_data/AIOE_data.csv', sep=';')

#  score column into float 
df_scores['Language Modeling AIOE'] = df_scores['Language Modeling AIOE'].astype(str).str.replace(',', '.').astype(float)

# renaming colums for merging later 
if 'SOC Code' in df_scores.columns:
    df_scores = df_scores.rename(columns={'SOC Code': 'soc_code'})

# codes into string
df_scores['soc_code'] = df_scores['soc_code'].astype(str)

print("AI Scores Head:")
print(df_scores.head())
print(df_scores.shape)

# Normalzied AI scores between 0 and 1
df_scores['Language Modeling AIOE'] = df_scores['Language Modeling AIOE'].astype(str).str.replace(',', '.').astype(float)

# defining min and max for normalization
min_score = df_scores['Language Modeling AIOE'].min()
max_score = df_scores['Language Modeling AIOE'].max()

df_scores['Language Modeling AIOE'] = (df_scores['Language Modeling AIOE'] - min_score) / (max_score - min_score)

print(min_score, max_score)
print(f"Scores Normalized. New Range: {df_scores['Language Modeling AIOE'].min()} - {df_scores['Language Modeling AIOE'].max()}")

#  merging connecting US Scores to the Crosswalk
merged_df = pd.merge(
    df_cross_walk,
    df_scores,
    on='soc_code',
    how='inner'
)

print(f"Merged rows (US Jobs mapped to ISCO): {len(merged_df)}")

# extract the 1-Digit ISCO Major Group
# ensuring ISCO codes to be 4 digis to prevent inner jobs confution
merged_df['isco08_code'] = merged_df['isco08_code'].astype(str).str.zfill(4)

# Create the new column by taking the first character
merged_df['isco_major_group'] = merged_df['isco08_code'].str[0]

# Filtering out 0 to exlud armed work forces
merged_df = merged_df[merged_df['isco_major_group'] != '0']

# AGGREGATION: Calculate Mean Score per Major Group
# grouoing by 1 digitcode and averaging the ai scores 
isco_group_scores = merged_df.groupby('isco_major_group')['Language Modeling AIOE'].mean().reset_index()

# Renaming AIOE into isco_ai_score 
isco_group_scores = isco_group_scores.rename(columns={'Language Modeling AIOE': 'isco_ai_score'})

print("\n--- Calculated AI Scores for ISCO Major Groups ---")
print(isco_group_scores)

# ===================================================================

# striping eurostats ISCO codes to match our major group codes
df_filtered['isco_clean'] = df_filtered['isco08'].astype(str).str.replace(r'\D+', '', regex=True)

# merging ai scores with eurostat data
df_weighted = pd.merge(
    df_filtered,
    isco_group_scores,
    left_on='isco_clean',      # Eurostat
    right_on='isco_major_group', # AI score
    how='inner'           
)

print(f"Matched Employment Records: {len(df_weighted)}")


# weighted average calculation per industry and country
#(Employment * Score) / Total Employment in that Industry

# Exposure Mass for each specific row 
df_weighted['exposure_mass'] = df_weighted['OBS_VALUE'] * df_weighted['isco_ai_score']

# group by country and industry to sum up the mass and total workers 'geo' for country, 'nace_r2' for industry
industry_summary = df_weighted.groupby(['geo', 'nace_r2'])[['exposure_mass', 'OBS_VALUE']].sum()

# divide to get the Weighted Average
industry_summary['AIIE_Index'] = industry_summary['exposure_mass'] / industry_summary['OBS_VALUE']

# reset index to turn 'geo' and 'nace_r2' back into columns
final_df = industry_summary.reset_index()

# removing calculation columns 
final_df = final_df[['geo', 'nace_r2', 'AIIE_Index', 'OBS_VALUE']]
final_df = final_df.rename(columns={'OBS_VALUE': 'Total_Employment'})

print("\n--- Final AI Industry Exposure Index (AIIE) ---")
print(final_df.head(10))
'''
#output folder
output_folder = 'processed_data'
os.makedirs(output_folder, exist_ok=True)
final_clean = final_df.dropna(subset=['AIIE_Index'])

# Save to CSV
final_path = os.path.join(output_folder, 'final_industry_ai_exposure.csv')
final_clean.to_csv(final_path, index=False)

# Save the ISCO Group Scores 
isco_path = os.path.join(output_folder, 'isco_major_group_scores.csv')
isco_group_scores.to_csv(isco_path, index=False)

# Save the Detailed Crosswalk 
crosswalk_path = os.path.join(output_folder, 'detailed_crosswalk_audit.csv')
merged_df.to_csv(crosswalk_path, index=False)
'''

isco_names = {
    '1': 'Managers',
    '2': 'Professionals',
    '3': 'Technicians',
    '4': 'Clerical Support',
    '5': 'Service & Sales',
    '6': 'Skilled Ag/Fishery',
    '7': 'Craft & Trades',
    '8': 'Operators & Assemblers',
    '9': 'Elementary Occupations',
    '0': 'Armed Forces'
}

isco_group_scores['occupation_name'] = isco_group_scores['isco_major_group'].astype(str).map(isco_names)
print(isco_group_scores)
