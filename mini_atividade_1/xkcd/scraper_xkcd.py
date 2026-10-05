"""
Mini Atividade 1 (Parte 3) - Scraper de Tirinhas do XKCD
Autor: Desenvolvedor (Projeto de Extração de Dados)
Descrição:
    Acessa o site https://xkcd.com/, faz o download da imagem da tirinha
    e navega retroativamente através do botão 'Previous Comic' (<a rel="prev">)
    salvando as imagens no disco rígido com requests e iter_content(), até alcançar
    a primeira tirinha.
"""

import argparse
import logging
import os
import re
import sys
import time
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

BASE_URL = "https://xkcd.com/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/*,*/*;q=0.8",
}


def sanitize_filename(filename: str) -> str:
    """Remove caracteres inválidos para sistemas de arquivos Windows/Linux."""
    return re.sub(r'[\\/*?:"<>|]', "_", filename)


def download_xkcd_comics(output_dir: str = "tirinhas", max_comics: Optional[int] = None) -> int:
    """
    Percorre as páginas do XKCD retroativamente:
    1. Baixa a página atual com requests.
    2. Localiza a URL da imagem usando BeautifulSoup.
    3. Baixa a imagem usando iter_content().
    4. Localiza o link 'Previous Comic' (rel='prev') e repete.
    """
    os.makedirs(output_dir, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)

    current_url = BASE_URL
    downloaded_count = 0

    logging.info("Iniciando download de tirinhas do XKCD a partir de: %s", current_url)
    logging.info("Destino dos arquivos: %s", os.path.abspath(output_dir))

    while current_url:
        logging.info("Carregando página: %s", current_url)

        try:
            res = session.get(current_url, timeout=15)
            res.raise_for_status()
        except requests.RequestException as exc:
            logging.error("Falha ao carregar a página %s: %s", current_url, exc)
            break

        soup = BeautifulSoup(res.text, "html.parser")

        # Localiza o container da tirinha <div id="comic">
        comic_elem = soup.find("div", id="comic")
        image_tag = comic_elem.find("img") if comic_elem else None

        if not image_tag or not image_tag.get("src"):
            logging.warning("Nenhuma imagem de tirinha encontrada em: %s", current_url)
        else:
            image_src = image_tag["src"]
            # Trata links relativos ou de protocolo (ex: '//imgs.xkcd.com/...')
            if image_src.startswith("//"):
                image_url = "https:" + image_src
            else:
                image_url = urljoin(current_url, image_src)

            # Define o nome do arquivo a salvar
            raw_filename = os.path.basename(image_src.split("?")[0])
            alt_title = image_tag.get("alt", "").strip()

            # Extrai o número da tirinha a partir da URL se disponível
            comic_number_match = re.search(r"/(\d+)/?", current_url)
            comic_prefix = f"comic_{comic_number_match.group(1)}_" if comic_number_match else ""

            final_filename = sanitize_filename(f"{comic_prefix}{raw_filename}")
            filepath = os.path.join(output_dir, final_filename)

            # Baixa a imagem da tirinha em blocos com iter_content()
            try:
                logging.info("  Baixando imagem: %s -> %s", image_url, final_filename)
                res_img = session.get(image_url, stream=True, timeout=20)
                res_img.raise_for_status()

                with open(filepath, "wb") as image_file:
                    for chunk in res_img.iter_content(chunk_size=1024):
                        if chunk:
                            image_file.write(chunk)

                downloaded_count += 1
                logging.info("  [OK] Imagem salva com sucesso: %s", final_filename)
            except requests.RequestException as exc:
                logging.error("  Erro ao baixar imagem %s: %s", image_url, exc)

        # Checa limite estipulado pelo usuário
        if max_comics and downloaded_count >= max_comics:
            logging.info("Limite solicitado de %d tirinhas atingido.", max_comics)
            break

        # Localiza o link para a tirinha anterior (Previous Comic)
        prev_link = soup.find("a", rel="prev")
        if not prev_link or not prev_link.get("href"):
            logging.info("Botão de 'Previous' não encontrado. Fim da navegação.")
            break

        prev_href = prev_link["href"]

        # No XKCD, a primeira tirinha aponta para '#' no botão 'prev'
        if prev_href == "#" or prev_href.endswith("#"):
            logging.info("Primeira tirinha da história alcançada! Encerrando.")
            break

        current_url = urljoin(BASE_URL, prev_href)
        time.sleep(0.3)  # Pausa de cortesia entre requisições

    logging.info("Processo finalizado! Total de tirinhas baixadas: %d", downloaded_count)
    return downloaded_count


def main():
    parser = argparse.ArgumentParser(description="Scraper e Downloader de Tirinhas do XKCD")
    parser.add_argument(
        "--output-dir",
        "-o",
        default="tirinhas",
        help="Diretório onde as imagens serão salvas (padrão: tirinhas)",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=5,
        help="Número máximo de tirinhas para baixar (padrão: 5 para testes; use 0 para todas até a #1)",
    )
    args = parser.parse_args()

    limit = None if args.limit <= 0 else args.limit
    download_xkcd_comics(output_dir=args.output_dir, max_comics=limit)


if __name__ == "__main__":
    main()
