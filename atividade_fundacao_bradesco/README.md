# Atividade 1: Robô de Coleta de Dados - Fundação Bradesco (Escola Virtual)

## 📌 Visão Geral do Projeto

Neste projeto, desenvolvi um robô de Web Scraping para coletar todos os cursos disponíveis na plataforma da **Fundação Bradesco** ([Escola Virtual](https://www.ev.org.br/cursos)).

O objetivo foi extrair automaticamente dados estruturados de cada curso para alimentar pipelines de análise, comparativos educacionais ou dashboards de visualização.

---

## 🛠️ Decisões Técnicas e Arquitetura

Ao analisar a estrutura do site `ev.org.br/cursos`, tomei as seguintes decisões de engenharia:

1. **Abordagem de Requisições HTTP (`requests` + `BeautifulSoup`) em vez de Selenium/Playwright**:
   - Inspecionei o tráfego de rede e identifiquei que a listagem de cursos é renderizada via paginação tradicional com parâmetro de query string (`https://www.ev.org.br/cursos?pagina={n}`).
   - Optar por `requests` com parser `BeautifulSoup` (`html.parser`) reduziu o tempo total de extração para menos de 30 segundos, sem a necessidade de instalar binários pesados de navegadores ou consumir centenas de megabytes de memória RAM.

2. **Extração em Dois Níveis (Cards + Detalhe do Curso)**:
   - **Nível 1 (Listagem)**: Extraí metadados rápidos como título, resumo introdutório, carga horária e nível de dificuldade diretamente dos componentes `.m-card`.
   - **Nível 2 (Página Interna)**: O robô acessa o link direto de cada curso (`/cursos/<slug>`) para extrair a ementa detalhada (módulos de conteúdo programático) e as seções de metadados operacionais (pré-requisitos, idade mínima e prazo de conclusão).

3. **Resiliência e Politeness (Boas Práticas de Scraping)**:
   - Utilizei um cabeçalho HTTP completo (`User-Agent`, `Accept-Language`) simulando um navegador moderno para evitar bloqueios ou respostas truncadas.
   - Apliquei `time.sleep(0.3)` entre requisições de páginas internas para garantir respeito à infraestrutura do servidor da instituição.
   - Detecção automática do término da paginação: o robô encerra o loop assim que a página subsequente não apresenta mais cards ou quando o indicador de próxima página não existe.

4. **Tratamento de Dados e Normalização**:
   - Tratamento de caracteres especiais e entidades HTML com `html.unescape`.
   - Remoção de quebras de linha excessivas e espaçamentos redundantes via expressões regulares.
   - Exportação em formato `JSON` com indentação de 2 espaços e suporte a UTF-8 (`ensure_ascii=False`).

---

## 📋 Estrutura dos Dados Extraídos

Cada registro do arquivo `cursos_bradesco.json` obedece rigorosamente ao schema solicitado na atividade:

```json
{
  "titulo": "Administrando Banco de Dados",
  "area_tema": "Administração",
  "descricao_resumo": "Neste curso, você verá uma introdução de como administrar um banco de dados...",
  "carga_horaria": "15h",
  "nivel_dificuldade": "Avançado",
  "link_curso": "https://www.ev.org.br/cursos/administrando-banco-de-dados",
  "conteudo": [
    "Módulo 1 – Administrador de banco de dados",
    "Módulo 2 – Arquitetura de um Sistema Geral de Banco de Dados (SGBD)",
    "Módulo 3 – Gerenciamento e manutenção de sistemas de dados",
    "Módulo 4 – Procedimentos administrativos"
  ],
  "detalhes": {
    "Pré-requisitos": "Não há pré-requisitos para a realização deste curso.",
    "Idade mínima": "16",
    "Prazo": "Você terá 60 dias para concluir este curso."
  }
}
```

---

## 🚀 Como Executar

### 1. Pré-requisitos
Certifique-se de ter instalado as dependências do projeto:
```bash
pip install -r ../requirements.txt
```

### 2. Executando a Coleta Completa
```bash
python scraper_bradesco.py --output cursos_bradesco.json
```

### 3. Executando um Teste Rápido (Ex: 5 cursos)
```bash
python scraper_bradesco.py --limit 5 --output teste_bradesco.json
```
