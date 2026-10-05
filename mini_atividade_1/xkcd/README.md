# Mini Atividade 1 (Parte 3): Scraper de Webcomic - XKCD

## 📌 Visão Geral do Projeto

Neste módulo, desenvolvi um robô para automação do download das tirinhas clássicas do site [XKCD](https://xkcd.com/).

O XKCD possui uma estrutura sequencial histórica: a página inicial exibe a tirinha mais recente e possui um botão **Previous (Anterior)** (`<a rel="prev">`) que navega para a publicação imediatamente anterior, até alcançar a tirinha número 1.

---

## 🛠️ Decisões Técnicas e Arquitetura

1. **Download em Chunks com `iter_content()`**:
   - Seguindo a boa prática recomendada para download de arquivos binários e mídia, utilizei:
     ```python
     res_img = session.get(image_url, stream=True)
     with open(filepath, "wb") as f:
         for chunk in res_img.iter_content(chunk_size=1024):
             if chunk:
                 f.write(chunk)
     ```
   - **Por que tomei essa decisão?** Baixar imagens via stream em blocos de 1KB (`chunk_size=1024`) evita carregar o arquivo binário inteiro na memória primária antes da gravação, reduzindo drasticamente o consumo de RAM e prevenindo falhas de buffer.

2. **Identificação da Imagem com BeautifulSoup**:
   - O elemento principal da tirinha é isolado no DOM através da tag `<div id="comic">`.
   - A imagem possui fonte que frequentemente utiliza URLs de protocolo relativo (ex: `//imgs.xkcd.com/comics/...`). O script trata isso convertendo automaticamente para URLs absolutas HTTPS com segurança.

3. **Navegação Retroativa e Condição de Parada**:
   - A cada ciclo, o script localiza o elemento `a` com atributo `rel="prev"`.
   - O loop detecta quando o link aponta para `#` ou quando não há link anterior, o que no XKCD sinaliza o alcance da primeira tirinha da história.
   - Para conveniência de testes e demonstração do exercício, adicionei o argumento `--limit` (com padrão de 5 tirinhas para testes rápidos ou `0` para execução total até o início).

4. **Nomenclatura Amigável e Sanitização**:
   - Os arquivos são salvos preservando o identificador da tirinha e o nome original (ex: `comic_3305_ground_effect.png`), garantindo que o explorador de arquivos ordene cronologicamente as tirinhas.

---

## 🚀 Como Executar

### 1. Download de Demonstração (Ex: últimas 10 tirinhas)
```bash
python scraper_xkcd.py --limit 10 --output-dir tirinhas
```

### 2. Download Completo (Até a primeira tirinha #1)
```bash
python scraper_xkcd.py --limit 0 --output-dir tirinhas
```
