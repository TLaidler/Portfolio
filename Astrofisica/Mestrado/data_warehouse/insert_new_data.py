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
import io
import numpy as np
import pylab as pl
import matplotlib.pyplot as plt

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
#light_curve_df = get_light_curve(url, username, password)

### script usando astropy para importar curvas de luz do Vizier

def fetch_vizier_data():
    try:
        v = Vizier(catalog='B/occ/asteroid')
        v.ROW_LIMIT = 10000000
        df = v.query_constraints()[0]
        for n in range(len(df)):
            r = requests.get('https://cdsarc.cds.unistra.fr/viz-bin/vizgraph?' +
                 '-s=B/occ&' + '-i=.graph_sql&' + 'sec={}&'.format(str(df['Dur'][n])) + 'date={}&'.format(str(df['Date'][n])) +
                 'num={}&'.format(str(df['Seq'][n])) + '--output=tsv')
            content = io.BytesIO(r.content)
            lines = content.readlines()

            time = np.array([])
            flux = np.array([])

            for i in range(4, len(lines)-2):
                time = np.append(time, float(lines[i].decode("utf-8").rsplit()[0]))
                flux = np.append(flux, float(lines[i].decode("utf-8").rsplit()[1]))
            
            #script para salvar um .dat com uma coluna time e fluxo
            print(f"Curve {n} of {len(df)}")
            print(f'lc_{df["Name"][n]}_obs_by_{df["ObsName"][n]}_{df["Date"][n][:7]}.dat'.replace(" ", "").replace("/", "-")+" being saved")
            np.savetxt('data_warehouse/data/' + f'lc_{df["Name"][n]}_obs_by_{df["ObsName"][n]}_{df['Date'][n][:7]}.dat'.replace(" ", "").replace("/", "-"), np.column_stack((time, flux)), delimiter=' ')

            #script para plotar a curva de luz e salvar em .png
            plt.figure(figsize=(10, 6))
            plt.plot(time, flux, '.')
            plt.xlabel('Time')
            plt.ylabel('Flux')
            plt.title(f'Light Curve from Vizier (ID: {df["Name"][n]})')
            plt.savefig('data_warehouse/plots/' +f'lc_{df["Name"][n]}_obs_by_{df["ObsName"][n]}.png'.replace(" ", "").replace("/", "-"))
            plt.close()

            print("light curve successfully saved!")
            #script para salvar a curva em stellar_occultations.db
            #conn = sqlite3.connect('stellar_occultations.db')
            #cursor = conn.cursor()
            #cursor.execute("INSERT INTO light_curves (name, obs_name, time, flux) VALUES (?, ?, ?, ?)", (df["Name"][n], df["ObsName"][n], time, flux))
            #conn.commit()
            #conn.close()

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

import os
import shutil
import re

def organize_dat_files():
    # Diretório base onde estão os arquivos .dat
    base_dir = "data_warehouse/data"
    
    # Dicionário para mapear meses para símbolos
    month_symbols = {
        '01': 'jan', '02': 'fev', '03': 'mar', '04': 'abr',
        '05': 'mai', '06': 'jun', '07': 'jul', '08': 'ago',
        '09': 'set', '10': 'out', '11': 'nov', '12': 'dez'
    }
    
    # Padrão regex para extrair informações do nome do arquivo
    pattern = r'lc_([A-Za-z0-9]+)_obs_by_([A-Za-z0-9]+)_(\d{4})-(\d{2})\.dat'
    
    # Lista todos os arquivos .dat no diretório
    for filename in os.listdir(base_dir):
        if filename.endswith('.dat'):
            # Tenta fazer match com o padrão do nome do arquivo
            match = re.match(pattern, filename)
            if match:
                body_name, obs_name, year, month = match.groups()
                
                # Cria o nome da pasta no formato "BODYNAME-monthsymbolYY"
                folder_name = f"{body_name}-{month_symbols[month]}{year[2:]}"
                
                # Cria o caminho completo da pasta
                folder_path = os.path.join(base_dir, folder_name)
                
                # Cria a pasta se ela não existir
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                
                # Novo nome do arquivo
                new_filename = f"lc_{obs_name}.dat"
                
                # Caminho completo do arquivo original e destino
                old_file_path = os.path.join(base_dir, filename)
                new_file_path = os.path.join(folder_path, new_filename)
                
                # Move e renomeia o arquivo
                shutil.move(old_file_path, new_file_path)
                print(f"Arquivo {filename} movido para {folder_path}/{new_filename}")

if __name__ == "__main__":
    print("Starting Vizier data fetch...")
    df = fetch_vizier_data()
    organize_dat_files()

# Example: To get data after a specific date
# v = Vizier(column_filters={"Date": ">2020-01-01"})
# result = v.query_constraints(catalog=catalog)

