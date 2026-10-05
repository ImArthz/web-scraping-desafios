"""
Mini Atividade 1 - Extração de Dados da Plataforma Sucupira (CAPES)
Autor: Desenvolvedor (Projeto de Extração de Dados)
Descrição:
    Realiza a extração de dados de programas/cursos de pós-graduação da CAPES/Sucupira.
    
    Atende aos itens 1 e 2 da atividade:
    1. Extração estruturada dos 16 campos solicitados:
       código, areaBasica, areaAvaliacao, situação, cidade, mestrado, nota,
       situacaoMestrado, doutorado, codigoMestrado, situacaoDoutorado, notaMestrado,
       codigoDoutorado, cep, início e universidade.
    2. Suporte a extração a partir de 2 URLs distintas (ou IDs de detalhamento),
       gerando como saída 2 arquivos CSV com os dados extraídos.
    3. Suporte opcional à extração em lote de 500 cursos a partir da listagem oficial
       do Observatório da CAPES.
"""

import argparse
import csv
import logging
import re
import sys
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Gateway oficial de APIs públicas do Observatório da Sucupira / CAPES
API_BASE_URL = "https://apigw-proxy.capes.gov.br/observatorio/data/observatorio/ppg"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://sucupira.capes.gov.br/",
}

CSV_FIELDNAMES = [
    "código",
    "areaBasica",
    "areaAvaliacao",
    "situação",
    "cidade",
    "mestrado",
    "nota",
    "situacaoMestrado",
    "doutorado",
    "codigoMestrado",
    "situacaoDoutorado",
    "notaMestrado",
    "codigoDoutorado",
    "cep",
    "início",
    "universidade",
]


def extract_id_from_url(url: str) -> Optional[int]:
    """Extrai o ID numérico do programa a partir de uma URL ou string numérica."""
    url = url.strip()
    if url.isdigit():
        return int(url)

    match = re.search(r"/(?:detalhamento|programa|ppg)/(\d+)", url)
    if match:
        return int(match.group(1))

    # Tenta achar qualquer sequência final de dígitos
    match_any = re.search(r"(\d+)/?$", url)
    if match_any:
        return int(match_any.group(1))

    return None


def fetch_program_detail(session: requests.Session, program_id: int) -> Optional[Dict[str, Any]]:
    """Consulta o endpoint REST do Observatório da CAPES para obter o detalhamento completo."""
    endpoint = f"{API_BASE_URL}/{program_id}"
    try:
        response = session.get(endpoint, headers=HEADERS, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logging.error("Erro ao consultar detalhes do programa ID %d: %s", program_id, exc)
        return None


def map_program_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapeia o payload bruto da CAPES para o schema exato dos 16 campos
    exigidos na Mini Atividade 1.
    """
    obs = data.get("observatorio", {})
    cursos = obs.get("cursos", [])

    # Localiza sub-cursos de Mestrado e Doutorado
    mestrado = next((c for c in cursos if "mestrado" in c.get("grau", "").lower()), {})
    doutorado = next((c for c in cursos if "doutorado" in c.get("grau", "").lower()), {})

    # Instituição de ensino vinculada
    instituicoes = obs.get("instituicoes", [])
    inst = instituicoes[0] if instituicoes else {}

    codigo = data.get("codigo") or obs.get("codigo")
    area_basica = (
        data.get("nomeGrandeAreaConhecimento")
        or data.get("nomeAreaConhecimento")
        or obs.get("nomeGrandeAreaConhecimento")
    )
    area_avaliacao = data.get("nomeAreaAvaliacao") or obs.get("nomeAreaAvaliacao")
    situacao = data.get("situacao") or obs.get("situacao")
    cidade = obs.get("endMunicipio")

    # Informações de Mestrado
    tem_mestrado = bool(mestrado)
    nome_mestrado = mestrado.get("nome") or ("Sim" if tem_mestrado else "Não")
    nota = data.get("conceito") or obs.get("conceito")
    situacao_mestrado = mestrado.get("situacao") if tem_mestrado else None
    codigo_mestrado = mestrado.get("codigo") if tem_mestrado else None
    nota_mestrado = mestrado.get("conceito") if tem_mestrado else None

    # Informações de Doutorado
    tem_doutorado = bool(doutorado)
    nome_doutorado = doutorado.get("nome") or ("Sim" if tem_doutorado else "Não")
    situacao_doutorado = doutorado.get("situacao") if tem_doutorado else None
    codigo_doutorado = doutorado.get("codigo") if tem_doutorado else None

    cep = obs.get("endCep")
    inicio = obs.get("anoInicio") or mestrado.get("dataInicio") or doutorado.get("dataInicio")
    universidade = inst.get("nomeIes") or data.get("siglaIes") or obs.get("siglaIes")

    return {
        "código": codigo,
        "areaBasica": area_basica,
        "areaAvaliacao": area_avaliacao,
        "situação": situacao,
        "cidade": cidade,
        "mestrado": nome_mestrado,
        "nota": nota,
        "situacaoMestrado": situacao_mestrado,
        "doutorado": nome_doutorado,
        "codigoMestrado": codigo_mestrado,
        "situacaoDoutorado": situacao_doutorado,
        "notaMestrado": nota_mestrado,
        "codigoDoutorado": codigo_doutorado,
        "cep": cep,
        "início": inicio,
        "universidade": universidade,
    }


def save_to_csv(rows: List[Dict[str, Any]], filename: str) -> None:
    """Salva a lista de dicionários em arquivo CSV com codificação UTF-8 BOM."""
    if not rows:
        logging.warning("Nenhum dado para salvar em %s", filename)
        return

    with open(filename, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    logging.info("CSV salvo com sucesso: %s (%d registros)", filename, len(rows))


def scrape_from_url(session: requests.Session, url: str) -> Optional[Dict[str, Any]]:
    """Extrai os dados de um programa a partir de sua URL na Sucupira."""
    prog_id = extract_id_from_url(url)
    if not prog_id:
        logging.error("Não foi possível identificar o ID do programa na URL: %s", url)
        return None

    logging.info("Consultando detalhes para a URL: %s (ID extraído: %d)", url, prog_id)
    raw_data = fetch_program_detail(session, prog_id)
    if not raw_data:
        return None

    return map_program_data(raw_data)


def scrape_batch_courses(session: requests.Session, total: int = 500) -> List[Dict[str, Any]]:
    """
    Coleta uma lista em lote de até N programas/cursos a partir do catálogo do Observatório
    e busca o detalhamento dos 16 campos.
    """
    logging.info("Iniciando extração em lote de %d cursos do Observatório CAPES...", total)
    url_list = f"{API_BASE_URL}?size={total}"
    try:
        resp = session.get(url_list, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        items = payload.get("content", [])
        logging.info("Recebidos %d itens da listagem geral.", len(items))
    except Exception as exc:
        logging.error("Erro ao listar programas em lote: %s", exc)
        return []

    results: List[Dict[str, Any]] = []
    for idx, item in enumerate(items[:total], start=1):
        pid = item.get("idPrograma")
        if not pid:
            continue

        raw = fetch_program_detail(session, pid)
        if raw:
            results.append(map_program_data(raw))
        else:
            # Fallback básico com dados da própria listagem
            results.append({
                "código": item.get("codigo"),
                "areaBasica": item.get("nomeGrandeAreaConhecimento") or item.get("nomeAreaConhecimento"),
                "areaAvaliacao": item.get("nomeAreaAvaliacao"),
                "situação": item.get("situacao"),
                "cidade": None,
                "mestrado": item.get("nome") if "mestrado" in item.get("grau", "").lower() else "Não",
                "nota": item.get("conceito"),
                "situacaoMestrado": item.get("situacao"),
                "doutorado": item.get("nome") if "doutorado" in item.get("grau", "").lower() else "Não",
                "codigoMestrado": None,
                "situacaoDoutorado": None,
                "notaMestrado": item.get("conceito"),
                "codigoDoutorado": None,
                "cep": None,
                "início": None,
                "universidade": item.get("siglaIes"),
            })

        if idx % 25 == 0 or idx == len(items):
            logging.info("Progresso lote: %d/%d cursos processados.", idx, min(total, len(items)))
        time.sleep(0.05)

    return results


def main():
    parser = argparse.ArgumentParser(description="Scraper da Plataforma Sucupira (CAPES)")
    parser.add_argument(
        "--url1",
        default="https://sucupira.capes.gov.br/programas/detalhamento/2099",
        help="Primeira URL para extração (padrão: detalhamento 2099)",
    )
    parser.add_argument(
        "--url2",
        default="https://sucupira.capes.gov.br/programas/detalhamento/4",
        help="Segunda URL para extração (padrão: detalhamento 4)",
    )
    parser.add_argument(
        "--out1",
        default="sucupira_url1.csv",
        help="Nome do arquivo CSV de saída para a URL 1",
    )
    parser.add_argument(
        "--out2",
        default="sucupira_url2.csv",
        help="Nome do arquivo CSV de saída para a URL 2",
    )
    parser.add_argument(
        "--batch-500",
        action="store_true",
        help="Habilita a extração em lote dos 500 cursos de pós-graduação",
    )
    parser.add_argument(
        "--batch-output",
        default="sucupira_500_cursos.csv",
        help="Arquivo de saída para a extração dos 500 cursos",
    )
    args = parser.parse_args()

    session = requests.Session()

    # Requisito 2: Extrair duas URLs diferentes e gerar dois arquivos CSV
    logging.info("=== Processando Requisito 2 (Extração de 2 URLs) ===")
    data1 = scrape_from_url(session, args.url1)
    if data1:
        save_to_csv([data1], args.out1)

    data2 = scrape_from_url(session, args.url2)
    if data2:
        save_to_csv([data2], args.out2)

    # Requisito 1: Extração dos 500 cursos
    if args.batch_500:
        logging.info("=== Processando Requisito 1 (Lote de 500 cursos) ===")
        batch_data = scrape_batch_courses(session, total=500)
        save_to_csv(batch_data, args.batch_output)

    logging.info("Processo Sucupira concluído com êxito!")


if __name__ == "__main__":
    main()
