# Data Generation (Reference)

This folder contains notebooks and reference files used to generate synthetic datasets for the Investment Banking performance dashboard. The folder has the following files:

- IB_Perf_DataGeneration.ipynb
- RefData.xlsx
- Readme.md

These files are:
- NOT used in production workflows
- NOT executed by GitHub Actions
- Kept for reference, reproducibility, and future enhancements

If you want to generate new synthetic data, the colab note book (IB_Perf_DataGeneration.ipynb) has code to generate the following 9 data files:

df_equity.csv - cash equity data 
df_fixedincome.csv - Fixed income (bonds, ncd, secured notes) data
df_repos.csv - Repos and reverse repos data
df_fxspot.csv - Fx spot data
df_derfx.csv - Fx derivatives data 
df_dereq.csv - Equity derivatives data
df_derint.csv - Interest Rate derivatives data 
df_dercr.csv  - Credit derivatives data 
df_margincalls.csv - Margin calls data

Use the "RefData.xlsx" file as guided in the colab notebook, which supports synthetic data generation with the reference data 