#  https://occultation.trgozlemevleri.gov.tr, #Acho que é só para predições
#  https://astro.troja.mff.cuni.cz/projects/damit/, # Apenas curvas de rotação
#  https://alcdef.org/, #Também foco em curvas de rotação
#  https://sodis.iota-es.de. #aguardando criar conta (admin aceitar)
# Vizier occ.lightcurves = https://vizier.cds.unistra.fr/viz-bin/VizieR-3?-source=B/occ&-out.max=50&-out.form=HTML%20Table&-out.add=_r&-out.add=_RAJ,_DEJ&-sort=_r&-oc.form=sexa
# 

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from astroquery.vizier import Vizier
import astropy.units as u
import astropy.coordinates as coord

def get_data_from_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

### script usando astropy para importar curvas de luz do Vizier

# Configure Vizier to get all columns and remove row limits
Vizier.ROW_LIMIT = -1  # Remove row limit
Vizier.columns = ['*']  # Get all columns

# Query the B/occ catalog
catalog = "B/occ"

# Get metadata about the catalog first
catalog_info = Vizier.get_catalog_metadata(catalog)
print("\nCatalog Information:")
print(catalog_info)

# Now query the actual data
result = Vizier.query_constraints(catalog=catalog)

if result is not None and len(result) > 0:
    # Access the first table in the result
    table = result[0]
    
    # See the column names
    print("\nColumns available:")
    print(table.colnames)
    
    # Convert to pandas DataFrame
    df = table.to_pandas()
    
    # Save to a file
    table.write('occultation_data.csv', format='csv', overwrite=True)
    print("\nData saved to occultation_data.csv")
    
    # Print first few rows
    print("\nFirst few rows of data:")
    print(df.head())
else:
    print("No data found in the catalog")

# Example: To get data after a specific date
# v = Vizier(column_filters={"Date": ">2020-01-01"})
# result = v.query_constraints(catalog=catalog)

