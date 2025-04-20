#  https://occultation.trgozlemevleri.gov.tr,
#  https://astro.troja.mff.cuni.cz/projects/damit/,
#  https://alcdef.org/,
#  https://sodis.iota-es.de.

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3

def get_data_from_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

