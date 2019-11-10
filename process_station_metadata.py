# Import libraries
import pandas as pd
import numpy as np

# Read raw CSV file
df = pd.read_csv('station-metadata-raw.csv',skiprows=3)
df.head()

# Function to process data
def process_data(data):
    data.drop(columns=['WMO ID','TC ID','Latitude','Longitude'],inplace=True)
    data.replace(np.nan,-999,inplace=True)
    data.rename(columns={'Latitude (Decimal Degrees)':'Latitude',
                         'Longitude (Decimal Degrees)':'Longitude',
                         'HLY First Year':'First Year (Hourly)',
                         'HLY Last Year':'Last Year (Hourly)',
                         'DLY First Year':'First Year (Daily)',
                         'DLY Last Year':'Last Year (Daily)',
                         'MLY First Year':'First Year (Monthly)',
                         'MLY Last Year':'Last Year (Monthly)'}, inplace=True)
    col_float_to_int = ['Elevation (m)', 'First Year', 'Last Year', 'First Year (Hourly)',
                        'Last Year (Hourly)', 'First Year (Daily)', 'Last Year (Daily)', 'First Year (Monthly)','Last Year (Monthly)']
    data[col_float_to_int] = data[col_float_to_int].astype(int)
    data = data[data.Longitude < -52.5]
    data = data[data.Longitude > -141.5]
    data.replace(-999,'N/A',inplace=True)
    return data

# Process data
df_proc = process_data(df)
df_proc.head()

# Export data to CSV
df_proc.to_csv('station-metadata-processed.csv',index=False)