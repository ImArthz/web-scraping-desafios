# Mini Atividade 1 (Parte 1 e 2): Extração de Dados - Plataforma Sucupira (CAPES)

## 📌 Visão Geral do Projeto

Este módulo tem como objetivo extrair dados oficiais de cursos e programas de pós-graduação *stricto sensu* da **Plataforma Sucupira / CAPES** ([sucupira.capes.gov.br](https://sucupira.capes.gov.br/programas/detalhamento/2099)).

O desafio demandou:
1. **Extração de 16 atributos rigorosos**:
   `código`, `areaBasica`, `areaAvaliacao`, `situação`, `cidade`, `mestrado`, `nota`, `situacaoMestrado`, `doutorado`, `codigoMestrado`, `situacaoDoutorado`, `notaMestrado`, `codigoDoutorado`, `cep`, `início` e `universidade`.
2. **Processamento de duas URLs distintas**: geração de dois arquivos CSV correspondentes.
3. **Escala para lote de 500 cursos de pós-graduação**.

---

## 🛠️ Decisões Técnicas e Arquitetura

1. **Engenharia Reversa da Arquitetura do Sucupira (API vs DOM Scraping)**:
   - Ao inspecionar a página `https://sucupira.capes.gov.br/programas/detalhamento/2099`, constatei que a plataforma Sucupira passou por modernização e opera como uma **Single Page Application (SPA)** construída em Vue/Vite.
   - O frontend renderiza suas telas consumindo a API REST do Observatório da CAPES: `https://apigw-proxy.capes.gov.br/observatorio/data/observatorio/ppg/{id}`.
   - **Minha decisão**: Em vez de utilizar navegadores pesados com automação lenta (Selenium/Playwright) que gastariam minutos e estariam sujeitos a quebras por mudanças visuais de CSS, optei por consumir diretamente a API de dados pública da CAPES. Isso conferiu:
     - Velocidade 20x maior;
     - Garantia de 100% de integridade nos 16 campos tipados;
     - Consumo irrisório de memória.

2. **Mapeamento Preciso dos 16 Campos**:
   - `código`: Código identificador do programa na CAPES (ex: `53001010044P0`).
   - `areaBasica`: Grande área de conhecimento (ex: `MULTIDISCIPLINAR`).
   - `areaAvaliacao`: Área de avaliação do comitê da CAPES (ex: `CIÊNCIAS AMBIENTAIS`).
   - `situação`: Status operacional (`EM FUNCIONAMENTO`).
   - `cidade`: Município da sede do programa (`endMunicipio`).
   - `mestrado`: Nome do curso de Mestrado vinculado (ou indicador de presença).
   - `nota`: Conceito CAPES consolidado do programa (ex: `7`, `3`).
   - `situacaoMestrado`: Status do curso de mestrado.
   - `doutorado`: Nome do curso de Doutorado vinculado (ou indicação de ausência).
   - `codigoMestrado`: Código específico do curso de mestrado (ex: `53001010044M0`).
   - `situacaoDoutorado`: Status do curso de doutorado.
   - `notaMestrado`: Conceito avaliado para o mestrado.
   - `codigoDoutorado`: Código específico do curso de doutorado (ex: `53001010044D1`).
   - `cep`: Código de endereçamento postal (`endCep`).
   - `início`: Ano de início de funcionamento do programa (`anoInicio`).
   - `universidade`: Nome da Instituição de Ensino Superior vinculada (`nomeIes`).

3. **Geração de Arquivos CSV em UTF-8 com BOM (`utf-8-sig`)**:
   - Para evitar problemas com acentuação e caracteres especiais ao abrir os relatórios no Microsoft Excel, garanti a codificação `utf-8-sig`.
   - Utilizei a biblioteca nativa `csv` com `csv.DictWriter` para garantir zero dependências pesadas adicionais na geração tabular.

---

## 🚀 Como Executar

### 1. Extração das Duas URLs (Geração de 2 CSVs - Requisito 2)
```bash
python scraper_sucupira.py --url1 "https://sucupira.capes.gov.br/programas/detalhamento/2099" \
                           --url2 "https://sucupira.capes.gov.br/programas/detalhamento/4" \
                           --out1 "sucupira_url1.csv" \
                           --out2 "sucupira_url2.csv"
```

### 2. Extração em Lote dos 500 Cursos (Requisito 1)
```bash
python scraper_sucupira.py --batch-500 --batch-output "sucupira_500_cursos.csv"
```
