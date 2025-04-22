#  https://occultation.trgozlemevleri.gov.tr, #Acho que é só para predições
#  https://astro.troja.mff.cuni.cz/projects/damit/, # Apenas curvas de rotação
#  https://alcdef.org/, #Também foco em curvas de rotação
#  https://sodis.iota-es.de. # Mesmo após a criação da conta, não consegui baixar as curvas de luz
# Vizier occ.lightcurves = https://vizier.cds.unistra.fr/viz-bin/VizieR-3?-source=B/occ&-out.max=50&-out.form=HTML%20Table&-out.add=_r&-out.add=_RAJ,_DEJ&-sort=_r&-oc.form=sexa
# Vizier só busca metadados de cada curva de luz, não dá para baixar as curvas de luz em sí

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from astroquery.vizier import Vizier
import astropy.units as u
import astropy.coordinates as coord
# Generico
def get_data_from_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

### script SODIS
def get_data_from_sodis(url, username, password):
    """
    Fetches data from SODIS website with authentication
    
    Args:
        url (str): URL of the light curve data
        username (str): SODIS username
        password (str): SODIS password
    
    Returns:
        BeautifulSoup object with the parsed HTML content
    """
    try:
        # Create a session to maintain cookies
        session = requests.Session()
        
        # SODIS login URL
        login_url = "https://sodis.iota-es.de/login.php"
        
        # Login form data - you might need to adjust field names
        # by inspecting the login form on the website
        login_data = {
            'username': username,
            'password': password,
            'submit': 'Login'
        }
        
        # Perform login
        login_response = session.post(login_url, data=login_data)
        
        if "Login failed" in login_response.text:
            print("Login failed. Please check your credentials.")
            return None
            
        # Now fetch the actual data page using the same session
        response = session.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def extract_light_curve(soup):
    """
    Extracts light curve data from the parsed HTML
    
    Args:
        soup: BeautifulSoup object containing the parsed HTML
    
    Returns:
        pandas.DataFrame with the light curve data
    """
    try:
        # Find the data table - you'll need to inspect the HTML structure
        # to get the correct table identifier
        table = soup.find('table', {'id': 'lightcurve'})  # or whatever ID/class is used
        
        if table is None:
            print("Could not find light curve data table")
            return None
            
        # Extract data
        data = []
        for row in table.find_all('tr')[1:]:  # Skip header row
            cols = row.find_all('td')
            if len(cols) >= 2:
                try:
                    time = float(cols[0].text.strip())
                    flux = float(cols[1].text.strip())
                    data.append([time, flux])
                except ValueError:
                    continue
                    
        # Create DataFrame
        df = pd.DataFrame(data, columns=['time', 'flux'])
        return df
        
    except Exception as e:
        print(f"Error extracting data: {e}")
        return None

# Example usage:
def get_light_curve(url, username, password):
    """
    Complete function to get light curve data from SODIS
    """
    # First get the page content with authentication
    soup = get_data_from_sodis(url, username, password)
    
    if soup is not None:
        # Extract the light curve data
        df = extract_light_curve(soup)
        
        if df is not None:
            # Save to CSV
            output_file = f'light_curve_{url.split("=")[-1]}.csv'
            df.to_csv(output_file, index=False)
            print(f"Data saved to {output_file}")
            
            # Plot the light curve
            plt.figure(figsize=(10, 6))
            plt.plot(df['time'], df['flux'], '.')
            plt.xlabel('Time')
            plt.ylabel('Flux')
            plt.title(f'Light Curve from SODIS (ID: {url.split("=")[-1]})')
            plt.show()
            
            return df
    
    return None

# Store your credentials securely (don't hardcode them!)
username = "TLaidler"
password = "gta12345"

# URL of the light curve you want to download
url = "https://sodis.iota-es.de/view/?u=8361"

# Get the light curve data
light_curve_df = get_light_curve(url, username, password)

### script usando astropy para importar curvas de luz do Vizier

def fetch_vizier_data():
    try:
        # Configure Vizier to get all columns and remove row limits
        v = Vizier(columns=['*'])
        v.ROW_LIMIT = -1  # Remove row limit
        
        # Query the B/occ catalog
        catalog = "B/occ/asteroid"  # Using the specific asteroid occultation table
        
        print("\nQuerying catalog data...")
        # Query the actual data using query_constraints
        result = v.query_constraints(catalog=catalog)
        
        if result is not None and len(result) > 0:
            # Access the first table in the result
            table = result[0]
            
            # See the column names
            print("\nColumns available:")
            print(table.colnames)
            
            # Convert to pandas DataFrame
            df = table.to_pandas()
            
            # Save to a file
            output_file = 'occultation_data.csv'
            table.write(output_file, format='csv', overwrite=True)
            print(f"\nData saved to {output_file}")
            
            # Print first few rows
            print("\nFirst few rows of data:")
            print(df.head())
            
            return df
        else:
            print("No data found in the catalog")
            return None
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

if __name__ == "__main__":
    print("Starting Vizier data fetch...")
    df = fetch_vizier_data()

# Example: To get data after a specific date
# v = Vizier(column_filters={"Date": ">2020-01-01"})
# result = v.query_constraints(catalog=catalog)

