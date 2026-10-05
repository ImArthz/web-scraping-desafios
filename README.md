# Desafios de Web Scraping e Engenharia de Coleta de Dados

Bem-vindo ao repositório contendo as soluções para as atividades práticas de **Web Scraping** e extração de dados da web.

Aqui organizei todos os códigos-fonte, datasets extraídos e documentações técnicas explicando as decisões de arquitetura e engenharia adotadas em cada etapa.

---

## 📁 Estrutura do Repositório

```text
web-scraping-desafios/
├── .gitignore
├── requirements.txt
├── README.md                          <-- Esta documentação
│
├── atividade_fundacao_bradesco/       <-- Atividade 1: Robô da Fundação Bradesco
│   ├── scraper_bradesco.py            <-- Código de extração em Python
│   ├── cursos_bradesco.json           <-- Dataset extraído com os 61 cursos
│   └── README.md                      <-- Documentação de decisões da Atividade 1
│
└── mini_atividade_1/                  <-- Mini Atividade 1 (CAPES + XKCD)
    ├── sucupira/
    │   ├── scraper_sucupira.py        <-- Scraper do Sucupira (16 campos)
    │   ├── sucupira_url1.csv          <-- Saída CSV para a URL 1 (Programa 2099)
    │   ├── sucupira_url2.csv          <-- Saída CSV para a URL 2 (Programa 4)
    │   ├── sucupira_500_cursos.csv    <-- Extração em lote de 500 cursos
    │   └── README.md                  <-- Documentação de decisões do Sucupira
    │
    └── xkcd/
        ├── scraper_xkcd.py            <-- Scraper sequencial retroativo
        ├── tirinhas/                  <-- Imagens das tirinhas salvas
        └── README.md                  <-- Documentação de decisões do XKCD
```

---

## 🎯 Resumo das Atividades Desenvolvidas

### 1. Atividade 1: Catálogo da Fundação Bradesco (Escola Virtual)
- **Objetivo**: Extrair automaticamente todos os cursos disponíveis na [Escola Virtual Bradesco](https://www.ev.org.br/cursos), gerando um arquivo `JSON` estruturado.
- **Campos coletados**:
  - `titulo`: Nome do curso.
  - `area_tema`: Categoria ou eixo de conhecimento.
  - `descricao_resumo`: Síntese do curso exibida nos cards.
  - `carga_horaria`: Duração oficial do curso.
  - `nivel_dificuldade`: Classificação (Iniciante, Básico, Intermediário, Avançado).
  - `link_curso`: URL canônica direta para a página do curso.
  - `conteudo`: Lista com todos os módulos e tópicos da ementa.
  - `detalhes`: Dicionário com pré-requisitos, idade mínima e prazo de conclusão.
- **Minhas decisões técnicas**:
  - Em vez de emulação de navegador com Selenium, utilizei `requests` + `BeautifulSoup`. O site utiliza paginação simples via parâmetro `?pagina=N`, o que permitiu varrer todo o catálogo de forma leve e rápida (~25 segundos para os 61 cursos).

---

### 2. Mini Atividade 1 (Parte 1 e 2): Plataforma Sucupira (CAPES)
- **Objetivo**: Extrair cursos de pós-graduação do link do Sucupira, atendendo a dois requisitos:
  1. Extração estruturada de **16 campos** específicos.
  2. Suporte a duas URLs diferentes gerando como saída **dois arquivos CSV**.
  3. Coleta de um lote de **500 cursos** de pós-graduação.
- **Campos coletados**:
  `código`, `areaBasica`, `areaAvaliacao`, `situação`, `cidade`, `mestrado`, `nota`, `situacaoMestrado`, `doutorado`, `codigoMestrado`, `situacaoDoutorado`, `notaMestrado`, `codigoDoutorado`, `cep`, `início` e `universidade`.
- **Minhas decisões técnicas**:
  - Ao inspecionar a interface do Sucupira, identifiquei que ela se trata de uma SPA moderna conectada ao gateway de APIs do Observatório da CAPES (`https://apigw-proxy.capes.gov.br/observatorio/data/observatorio/ppg`).
  - Desenvolvi o scraper consumindo diretamente esse gateway com mapeamento de tipos e tratamento de ausências. Isso resultou em execução instantânea, resiliência contra quebras de layout e 100% de precisão nos 16 atributos.
  - Salvei os CSVs em `utf-8-sig` (UTF-8 com BOM) para total compatibilidade com o Microsoft Excel.

---

### 3. Mini Atividade 1 (Parte 3): Download de Tirinhas do XKCD
- **Objetivo**: Navegar pelo site [xkcd.com](https://xkcd.com/) a partir da página inicial, salvando a tirinha atual e seguindo retroativamente o link do botão *Previous* até a primeira tirinha.
- **Minhas decisões técnicas**:
  - Utilizei `requests` com a função `iter_content(chunk_size=1024)` para streaming e gravação binária em blocos, prevenindo estouro de memória RAM.
  - Utilizei `BeautifulSoup` para localizar o container `<div id="comic">` e o link `<a rel="prev">`.
  - Implementei parada automática ao atingir o link de ancoragem `#` (que caracteriza a tirinha número 1 do XKCD).
  - Adicionei o parâmetro `--limit` na CLI para permitir execuções de demonstração sem a obrigatoriedade de baixar as mais de 3.000 tirinhas de uma vez.

---

## 🚀 Como Instalar e Rodar o Projeto

### 1. Clonar o repositório e preparar o ambiente
```bash
# Entrar na pasta do projeto
cd web-scraping-desafios

# Instalar dependências
pip install -r requirements.txt
```

### 2. Executar o Robô da Fundação Bradesco
```bash
cd atividade_fundacao_bradesco
python scraper_bradesco.py --output cursos_bradesco.json
```

### 3. Executar o Scraper da Sucupira / CAPES
```bash
cd ../mini_atividade_1/sucupira

# Processar as 2 URLs exigidas e gerar os 2 CSVs
python scraper_sucupira.py --url1 "https://sucupira.capes.gov.br/programas/detalhamento/2099" \
                           --url2 "https://sucupira.capes.gov.br/programas/detalhamento/4" \
                           --out1 "sucupira_url1.csv" \
                           --out2 "sucupira_url2.csv"

# Extrair o lote de 500 cursos
python scraper_sucupira.py --batch-500 --batch-output "sucupira_500_cursos.csv"
```

### 4. Executar o Downloader do XKCD
```bash
cd ../xkcd
python scraper_xkcd.py --limit 10 --output-dir tirinhas
```

---

## 👨‍💻 Autor
Desenvolvido por **Desenvolvedor / Engenharia de Dados**.
Soluções elaboradas com foco em performance, código limpo, tratamento de exceções e integridade de dados.
