import pandas as pd
import os

 
df = pd.read_csv('raw_data/lfsa_eisn2__custom_19083881_linear_2_0.csv', sep=',')

# Let's check the columns and shape to make sure it split correctly
print(f"Shape: {df.shape}")
print(df.head())

# Check data types of all columns
print(df.info())

# Specifically look at the observation values
print(df['OBS_VALUE'].head())
# Select relevant columns
cols_to_keep = ['nace_r2', 'isco08', 'TIME_PERIOD', 'OBS_VALUE','geo']

df_filtered = df[cols_to_keep].copy()

print(df_filtered.head())
print(df_filtered.info())

# Show me the first 5 rows where OBS_VALUE is NOT empty
print(df_filtered[df_filtered['OBS_VALUE'].notna()].head())


df_2 = pd.read_csv('raw_data/isco_soc_crosswalk_T.csv', skiprows=6, sep=';')

print(df_2.head())

missing_counts = df_2.isnull().sum()
print(missing_counts)

cols_to_drop = ['part', 'Comment 8/17/11']

df_cross_walk = df_2.drop(columns=cols_to_drop)
print(df_cross_walk.head())

df_scores = pd.read_csv('raw_data/AIOE_data.csv', sep=';')

print(df_scores.head())
df_scores['Language Modeling AIOE'] = df_scores['Language Modeling AIOE'].astype(str).str.replace(',', '.').astype(float)
print(df_scores.head())

