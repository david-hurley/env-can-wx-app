# Import libraries
import pandas as pd
import numpy as np

# Read raw CSV file
df = pd.read_csv('station-metadata-raw.csv',skiprows=3)
df.head()

# Function to process data
def process_data(data):
    data.drop(columns=['WMO ID','TC ID','Latitude','Longitude'],inplace=True)
    data.rename(columns={'Latitude (Decimal Degrees)':'Latitude',
                         'Longitude (Decimal Degrees)':'Longitude',
                         'Elevation (m)':'Elevation'},inplace=True)
    data.replace(np.nan,-999,inplace=True)
    col_float_to_int = ['Elevation', 'First Year', 'Last Year', 'HLY First Year',
                        'HLY Last Year', 'DLY First Year', 'DLY Last Year', 'MLY First Year','MLY Last Year']
    data[col_float_to_int] = data[col_float_to_int].astype(int)
    return data

# Process data
df_proc = process_data(df)
df_proc.head()

# Export data to CSV
df_proc.to_csv('station-metadata-processedtest.csv',index=False)