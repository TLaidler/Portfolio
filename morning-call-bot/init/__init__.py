# Biblioteca padrão do Python
import logging
from datetime import datetime, timezone
import os
import sys

# Bibliotecas de terceiros
from azure.functions import TimerRequest

# Módulos internos
import fetch_news


def main():#mytimer: TimerRequest) -> None:
    # utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    # if mytimer.past_due:
    #     logging.info('The timer is past due!')

    fetch_news.fetch_and_save()
    
    #logging.info('Python timer trigger function ran at %s', utc_timestamp)
