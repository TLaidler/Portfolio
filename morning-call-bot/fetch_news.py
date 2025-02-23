# Bibliotecas padrão do Python
import datetime as dt
import hashlib
import json
from multiprocessing.pool import ThreadPool
from dataclasses import dataclass, field
from typing import Dict
import time
import os

# Bibliotecas de terceiros
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import torch
from transformers import pipeline
from email_report import send_news_now

folder_to_save = "/links"

def get_G1_news_links(date):
    """
    Busca as últimas matérias de uma data específica no G1 (https://g1.globo.com/economia/).
    :param date: String da data no formato "yyyy-mm-dd"
    :return: Lista de URLs das notícias publicadas no dia especificado.
    """
    base_url = f"https://g1.globo.com/economia/"
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Transformar a data para o formato "yyyy/mm/dd" para buscar nos links
    formatted_date = date.replace("-", "/")
    articles = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        # Procurar apenas links que contenham a data fornecida no formato "yyyy/mm/dd"
        if formatted_date in href and ("economia" in href or "politica" in href):
            full_link = f"https://g1.globo.com{href}" if href.startswith("/") else href
            articles.append(full_link)

    # Remover duplicatas (caso existam)
    return list(set(articles))


def get_crypto_news_links(date):
    """
    Busca todas as últimas matérias de cripto no yahoo (https://finance.yahoo.com/topic/crypto/)
    e em Coindesk (https://www.coindesk.com/).
    #TODO: Fazer extensão para Bloomberg e Valor Economico
    :param date: String da data no formato "yyyy-mm-dd"
    :return: Duas Listas de URLs das notícias publicadas, a primeira do yahoo e a segunda da Coindesk.
    """
    base_yahoo_url = "https://finance.yahoo.com/topic/crypto/"
    response = requests.get(base_yahoo_url)
    soup = BeautifulSoup(response.text, "html.parser")

    articles_yahoo = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/news/" in href and str(href).endswith("html"):
            full_link = (
                f"https://finance.yahoo.com{href}" if href.startswith("/") else href
            )
            articles_yahoo.append(full_link)

    formatted_date = date.replace("-", "/")
    base_coindesk_url = "https://www.coindesk.com/"
    response = requests.get(base_coindesk_url)
    soup = BeautifulSoup(response.text, "html.parser")

    articles_coindesk = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if formatted_date in href and (
            "market" in href
            or "policy" in href
            or "politics" in href
            or "economy" in href
        ):
            full_link = (
                f"https://www.coindesk.com{href}" if href.startswith("/") else href
            )
            articles_coindesk.append(full_link)

    # Remover duplicatas (caso existam)
    return list(set(articles_yahoo)) + list(set(articles_coindesk))


def fetch_news_content(url):
    """
    Extrai o conteúdo principal de uma notícia a partir da URL.
    :param url: URL da notícia
    :return: Texto do conteúdo da notícia
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = soup.find_all("p")
    content = " ".join([p.get_text() for p in paragraphs])
    return content


def summarize_text(text):
    """
    Usa o modelo BART  para gerar um resumo do texto fornecido.
    :param text: Texto completo a ser resumido
    :param max_length: Tamanho máximo do resumo gerado
    :return: Resumo gerado pelo modelo
    """
    import re

    # Remover caracteres especiais desnecessários
    text = re.sub(r"\s+", " ", text).strip()
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    text_chunks = split_text(text)
    list_chunks = []

    for chunck in text_chunks:
        if (
            "clique aqui" in str(chunck).lower()
            or "veja também" in str(chunck).lower()
            or "click here" in str(chunck).lower()
            or "@" in chunck
            or ".com" in chunck
        ):
            continue
        else:
            list_chunks.append(translate_text_pt_to_en(chunck))

    # Resumindo o máximo possível
    full_text = " ".join(list_chunks)
    while len(full_text) >= 4000:
        full_text = split_text(full_text, max_chunk_len=3900)
        full_text = [
            summarizer(
                chunk,
                max_length=500,
                min_length=150,
                do_sample=False,
            )[
                0
            ]["summary_text"]
            for chunk in full_text
        ]
        full_text = " ".join(full_text)

    # TODO: Ideia -> fazer split_text novamente, mas em partes menores, e randomizar as posições dos elementos antes de juntar tudo e reduzir
    full_text = summarizer(full_text, max_length=900, min_length=400, do_sample=False)[
        0
    ]["summary_text"]
    return translate_text_en_to_pt(full_text)


def translate_text_en_to_pt(text):
    tradutor = GoogleTranslator(source="en", target="pt")
    traducao = tradutor.translate(text)
    return traducao


def translate_text_pt_to_en(text):
    tradutor = GoogleTranslator(source="pt", target="en")
    traducao = tradutor.translate(text)
    return traducao


def split_text(text, max_chunk_len=2500):
    """Divide o texto em pedaços menores para evitar sobrecarga de entrada."""
    sentences = text.split(". ")
    chunks = []
    chunk = ""
    for sentence in sentences:
        if len(chunk) + len(sentence) > max_chunk_len:
            chunks.append(chunk)
            chunk = sentence
        else:
            chunk += sentence + ". "
    chunks.append(chunk)
    return chunks


def save_links_as_text(lista_links, blob_name, storage_blob_connection = ""):
    # Converte a lista de links para uma string, com cada link em uma nova linha
    links_content = "\n".join(lista_links)

    # Obtém o cliente para o blob onde queremos salvar
    #blob_client = storage_blob_connection._container_client.get_blob_client(blob_name)

    # Faz o upload do conteúdo de links como blob de texto
    #blob_client.upload_blob(links_content, overwrite=True)

    salvar_txt(nome_arquivo="links.txt", conteudo=links_content)
    print(f"Arquivo '{blob_name}' com links salvo na pasta como texto.")


def compile_all_texts(links: list):
    # ler todos os links da pasta, rodar o codigo inteiro de summarize e depois limpar o blob no final
    all_news_content = ""
    for url in set(links):
        print(f"Processando notícia: {url}")
        news_content = fetch_news_content(url)
        all_news_content += news_content + "\n\n"

    return all_news_content


def salvar_txt(nome_arquivo, conteudo):
    """Salva uma string em um arquivo .txt."""
    with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)
    print(f"Arquivo '{nome_arquivo}' salvo com sucesso!")


def ler_txt(nome_arquivo):
    """Lê um arquivo .txt e retorna uma lista de strings, separadas por quebras de linha."""
    try:
        with open(nome_arquivo, "r", encoding="utf-8") as arquivo:
            linhas = arquivo.read().splitlines()  # Lê e separa as linhas sem incluir '\n'
        return linhas
    except FileNotFoundError:
        print(f"Erro: O arquivo '{nome_arquivo}' não foi encontrado.")
        return []


def deletar_txt(nome_arquivo):
    """Deleta um arquivo .txt se ele existir."""
    if os.path.exists(nome_arquivo):
        os.remove(nome_arquivo)
        print(f"Arquivo '{nome_arquivo}' deletado com sucesso!")
    else:
        print(f"Erro: O arquivo '{nome_arquivo}' não foi encontrado.")

    
def fetch_and_save(
    date=dt.datetime.utcnow().strftime(format="%Y-%m-%d"), today=dt.datetime.now()
):
    """
    Função principal que executa o processo de extração e resumo de notícias.
    :param date: Data das matérias a serem extraídas no formato "yyyy-mm-dd"
    """
    ######### Caso o usuário possua um banco de dados da azure (nesse caso o Blob para salvar os links em .txt e Cosmos para salvar o resumo e manter um histórico) ###########
    # blob = StorageBlobConnection(
    #   , container_name=""
    # )

    # if len(blob.getNameAllBlobs()) == 0:
    #     links_blob = []
    # else:
    #     links_blob = (
    #         blob.getBlobData_xls(blobName=blob.getNameAllBlobs()[0])
    #         .decode("utf-8")
    #         .split("\n")
    #     )

    try:
        news_links = ler_txt(nome_arquivo=f"{folder_to_save}/{"links.txt"}")
    except:
        news_links = []

    if today < dt.datetime(
        today.year, today.month, today.day, 18, 5, 0
    ) and today > dt.datetime(today.year, today.month, today.day, 17, 55, 0):
        ## ler links salvos em .txt

        all_news_content = compile_all_texts(links=news_links)
        print("Gerando resumo...")
        start = time.time()
        summary = summarize_text(all_news_content)
        print("\nResumo das notícias do dia:")
        print(summary)
        end = time.time()
        print(f"it took {round(end - start, 2)} secs to run")
        deletar_txt(nome_arquivo=f"{folder_to_save}/{"links.txt"}")
        # preparando cosmos
        # data_base = cosmosConnection( 
        #     cosmos_url="",
        #     database_name="",
        #     container_name="",
        #     primary_key="",
        # )
        # upload_cosmos(data_base=data_base, info_data=summary)
        # Limpando Blob
        #blob.deleteBlobData(blobName="links.txt")

        ## Enviar e-mail
        send_news_now(message = summary)

    else:
        print(f"Buscando matérias G1 para a data: {date}")
        # busca links, verifica se ja existem no blob
        # adiciona novos links no blob
        brasil_news = get_G1_news_links(date)
        print(f"Buscando matérias Cripto para a data: {date}")
        cripto_news = get_crypto_news_links(date)
        for new in set(brasil_news + cripto_news):
            if new in links_folder:
                continue
            else:
                news_links.append(new)
        save_links_as_text(news_links, "links.txt")
        print("Matérias salvas na pasta devido ao horário")
