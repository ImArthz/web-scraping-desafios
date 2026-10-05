"""
Robô de Coleta de Dados (Web Scraping) - Fundação Bradesco (Escola Virtual)
Autor: Desenvolvedor (Projeto de Extração de Dados)
Descrição:
    Acessa o catálogo de cursos da Fundação Bradesco (https://www.ev.org.br/cursos),
    percorre todas as páginas disponíveis, extrai os metadados dos cards e entra na página
    específica de cada curso para coletar a ementa completa (conteúdo programático) e
    detalhes adicionais (pré-requisitos, idade mínima e prazo de conclusão).
    Os dados finais são exportados de forma estruturada em formato JSON.
"""

import argparse
import html
import json
import logging
import re
import sys
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Configuração de Logging para acompanhamento claro no terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

BASE_URL = "https://www.ev.org.br"
CATALOG_URL = "https://www.ev.org.br/cursos"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def clean_text(text: Optional[str]) -> Optional[str]:
    """Limpa quebras de linha excessivas e decodifica entidades HTML."""
    if not text:
        return None
    unescaped = html.unescape(text)
    normalized = re.sub(r"\s+", " ", unescaped).strip()
    return normalized if normalized else None


def fetch_soup(session: requests.Session, url: str) -> Optional[BeautifulSoup]:
    """Executa requisição GET com tratamento de exceções e retorna objeto BeautifulSoup."""
    try:
        response = session.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as exc:
        logging.error("Erro ao acessar %s: %s", url, exc)
        return None


def extract_course_details(session: requests.Session, course_url: str) -> Dict[str, Any]:
    """
    Acessa a página interna do curso para coletar o conteúdo (ementa de módulos)
    e detalhes estruturados (pré-requisitos, idade mínima, prazo).
    """
    soup = fetch_soup(session, course_url)
    if not soup:
        return {"conteudo": [], "detalhes": {}}

    # Extração dos módulos / ementa do curso
    modules: List[str] = []
    content_container = (
        soup.find("div", id="eenie")
        or soup.find("div", class_=lambda c: c and "o-tabs_content" in c)
        or soup.find("section", class_=lambda c: c and "conteudo" in c)
    )

    if content_container:
        for li in content_container.find_all("li"):
            text = clean_text(li.get_text())
            if text:
                modules.append(text)

    # Caso a ementa não esteja em <li>, buscar parágrafos ou títulos de módulos
    if not modules and content_container:
        for p in content_container.find_all(["p", "h3", "h4"]):
            text = clean_text(p.get_text())
            if text and ("módulo" in text.lower() or "aula" in text.lower()):
                modules.append(text)

    # Extração de detalhes (Pré-requisitos, Idade mínima, Prazo)
    details: Dict[str, Any] = {}
    for heading in soup.find_all(["h3", "h4", "strong"]):
        head_text = clean_text(heading.get_text())
        if not head_text:
            continue
        lower_head = head_text.lower()
        if any(key in lower_head for key in ["pré-requisito", "idade mínima", "prazo", "modalidade"]):
            sibling = heading.find_next_sibling()
            if sibling:
                details[head_text] = clean_text(sibling.get_text())
            else:
                parent_text = clean_text(heading.parent.get_text()) if heading.parent else None
                details[head_text] = parent_text

    return {
        "conteudo": modules,
        "detalhes": details,
    }


def parse_course_card(session: requests.Session, card: BeautifulSoup, fetch_inner: bool = True) -> Dict[str, Any]:
    """Extrai informações consolidadas a partir do card do curso e sua página interna."""
    # Título do curso
    title_elem = card.find(class_=lambda c: c and "m-card_title" in c) or card.find("h3")
    titulo = clean_text(title_elem.get_text()) if title_elem else "Título não informado"

    # Resumo / Descrição
    desc_elem = card.find(class_=lambda c: c and "m-card_desc" in c) or card.find("p")
    descricao = clean_text(desc_elem.get_text()) if desc_elem else None

    # Link direto para a página do curso
    link_elem = card.find("a", class_=lambda c: c and "m-card_link" in c) or card.find("a", href=True)
    direct_link = urljoin(BASE_URL, link_elem["href"]) if link_elem and link_elem.get("href") else None

    # Duração (Carga horária) e Nível de dificuldade
    carga_horaria = None
    nivel_dificuldade = None

    for info in card.find_all(class_=lambda c: c and "m-card_info" in c):
        text = info.get_text(" ", strip=True)
        strong = info.find("strong")
        val = strong.get_text(strip=True) if strong else text

        if "dura" in text.lower():
            carga_horaria = clean_text(val)
        elif "n" in text.lower() and "vel" in text.lower():
            nivel_dificuldade = clean_text(val)

    # Área / Tema (a partir de classes temáticas ou atributos)
    area_tema = None
    classes = card.get("class", [])
    theme_map = {
        "-adm": "Administração",
        "-ti": "Tecnologia da Informação",
        "-contab": "Contabilidade e Finanças",
        "-desenv": "Desenvolvimento Pessoal",
        "-edu": "Educação",
    }
    for cls in classes:
        if cls in theme_map:
            area_tema = theme_map[cls]
            break

    # Se não identificado por classe, tentar buscar na página interna
    inner_data = {"conteudo": [], "detalhes": {}}
    if fetch_inner and direct_link:
        inner_data = extract_course_details(session, direct_link)
        time.sleep(0.3)  # Intervalo de cortesia para não sobrecarregar o servidor

    return {
        "titulo": titulo,
        "area_tema": area_tema,
        "descricao_resumo": descricao,
        "carga_horaria": carga_horaria,
        "nivel_dificuldade": nivel_dificuldade,
        "link_curso": direct_link,
        "conteudo": inner_data["conteudo"],
        "detalhes": inner_data["detalhes"],
    }


def scrape_bradesco_courses(max_courses: Optional[int] = None) -> List[Dict[str, Any]]:
    """Percorre as páginas do catálogo de cursos da Fundação Bradesco."""
    session = requests.Session()
    courses: List[Dict[str, Any]] = []
    seen_links = set()
    page = 1

    logging.info("Iniciando coleta de cursos em: %s", CATALOG_URL)

    while True:
        page_url = f"{CATALOG_URL}?pagina={page}"
        logging.info("Processando página %d: %s", page, page_url)
        soup = fetch_soup(session, page_url)
        if not soup:
            logging.warning("Não foi possível carregar a página %d. Encerrando paginação.", page)
            break

        cards = soup.find_all("article", class_=lambda c: c and "m-card" in c)
        if not cards:
            logging.info("Nenhum curso encontrado na página %d. Fim do catálogo.", page)
            break

        logging.info("Encontrados %d cursos na página %d.", len(cards), page)

        for card in cards:
            course_data = parse_course_card(session, card, fetch_inner=True)
            link = course_data.get("link_curso")

            if link and link in seen_links:
                continue
            if link:
                seen_links.add(link)

            courses.append(course_data)
            logging.info("  [OK] Coletado: %s (%s)", course_data["titulo"], course_data["carga_horaria"])

            if max_courses and len(courses) >= max_courses:
                logging.info("Limite de %d cursos atingido.", max_courses)
                return courses

        # Verifica se há indicador de próxima página
        has_next = soup.find("a", href=lambda h: h and f"pagina={page + 1}" in h)
        if not has_next:
            logging.info("Última página do catálogo alcançada (%d).", page)
            break

        page += 1
        time.sleep(0.5)

    logging.info("Coleta finalizada! Total de cursos coletados: %d", len(courses))
    return courses


def main():
    parser = argparse.ArgumentParser(description="Scraper de Cursos da Fundação Bradesco (Escola Virtual)")
    parser.add_argument(
        "--output",
        "-o",
        default="cursos_bradesco.json",
        help="Caminho do arquivo JSON de saída (padrão: cursos_bradesco.json)",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=None,
        help="Limite de cursos para extração (opcional, para testes rápidos)",
    )
    args = parser.parse_args()

    courses = scrape_bradesco_courses(max_courses=args.limit)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)

    logging.info("Arquivo salvo com sucesso em: %s (Total: %d registros)", args.output, len(courses))


if __name__ == "__main__":
    main()
