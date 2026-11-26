# Inventário de Procedência, Artes, Fontes e Auditoria Drippy

Este inventário registra **arquivo a arquivo** a procedência, autoria, licença, dimensão e hash SHA-256 dos ativos visuais, fontes tipográficas, textos e desenhos vetoriais em código de `kuky13/bolha`, `bolha-site` e da base original `mille-okws/pestinha`, preservando os créditos devidos a **@mille-okws e colaboradores** e a **André Ribeiro Lima (KukySolutions)**.

---

## 1. Artes e Conteúdo em `assets/bolha/` (`kuky13/bolha`)

Todos os arquivos abaixo pertencem à criação própria da Bolha (André Ribeiro Lima / KukySolutions) e estão sob **`GPL-3.0-or-later`** conforme `licenses/BOLHA-ASSETS.md` e `assets/bolha/README.md`. Os oito SVGs incluem a licença e a indicação de autoria no comentário do cabeçalho.

| Arquivo | Tipo / Dimensão | Tamanho (bytes) | SHA-256 (prefixo 12 hex) | Autoria / Origem | Licença |
|---|---|---|---|---|---|
| `assets/bolha/README.md` | Markdown | 397 | `b494792b8685` | André Ribeiro Lima (KukySolutions) | `GPL-3.0-or-later` |
| `assets/bolha/icon.ico` | ICO (1 imagem embutida) | 270.398 | `af76c5c4ff59` | André Ribeiro Lima (gerado do renderer Qt da Bolha) | `GPL-3.0-or-later` |
| `assets/bolha/icon.png` | PNG `256x256` | 32.971 | `1c2f264a69ee` | André Ribeiro Lima (gerado do renderer Qt da Bolha) | `GPL-3.0-or-later` |
| `assets/bolha/tray.png` | PNG `256x256` (cópia idêntica de `icon.png`) | 32.971 | `1c2f264a69ee` | André Ribeiro Lima (gerado do renderer Qt da Bolha) | `GPL-3.0-or-later` |
| `assets/bolha/content/cartazes.txt` | Texto UTF-8 | 402 | `28240a20b997` | André Ribeiro Lima (frases próprias da Bolha) | `GPL-3.0-or-later` |
| `assets/bolha/content/recadinhos.txt` | Texto UTF-8 | 289 | `0fd2d421f3bd` | André Ribeiro Lima (frases próprias da Bolha) | `GPL-3.0-or-later` |
| `assets/bolha/content/recadinhos_tristes.txt` | Texto UTF-8 | 151 | `835ced6963ee` | André Ribeiro Lima (frases próprias da Bolha) | `GPL-3.0-or-later` |
| `assets/bolha/content/memes/assustado/arremesso.svg` | SVG `640x640` | 1.435 | `714eeb5ed7c2` | André Ribeiro Lima | `GPL-3.0-or-later` |
| `assets/bolha/content/memes/bravo/greve.svg` | SVG `640x640` | 1.437 | `c7f41b5462e0` | André Ribeiro Lima | `GPL-3.0-or-later` |
| `assets/bolha/content/memes/contente/paz.svg` | SVG `640x640` | 1.438 | `75a8af569bce` | André Ribeiro Lima | `GPL-3.0-or-later` |
| `assets/bolha/content/memes/curioso/bug.svg` | SVG `640x640` | 1.443 | `7ee6334a2ddd` | André Ribeiro Lima | `GPL-3.0-or-later` |
| `assets/bolha/content/memes/dramatico/drama.svg` | SVG `640x640` | 1.444 | `f6c8a5f2efeb` | André Ribeiro Lima | `GPL-3.0-or-later` |
| `assets/bolha/content/memes/feliz/carinho.svg` | SVG `640x640` | 1.430 | `5c0eaa975071` | André Ribeiro Lima | `GPL-3.0-or-later` |
| `assets/bolha/content/memes/observando/cafe.svg` | SVG `640x640` | 1.435 | `59cded354967` | André Ribeiro Lima | `GPL-3.0-or-later` |
| `assets/bolha/content/memes/triste/nuvem.svg` | SVG `640x640` | 1.425 | `cdc62e9a9e43` | André Ribeiro Lima | `GPL-3.0-or-later` |

> **Observação sobre `scripts/build_native.py`:** em tempo de compilação Windows, `icon(output)` gera dinamicamente `icon.png`, `tray.png` e `icon.ico` a partir de `bolha.character.draw_character(..., emotion='observando')` para garantir paridade com a geometria vetorial vigente.

---

## 2. Capturas e GIFs de Documentação (`docs/images/` e `docs/previews/`)

Todas as capturas e prévias animadas abaixo são renderizações do próprio aplicativo Bolha realizadas por André Ribeiro Lima (KukySolutions), licenciadas sob `GPL-3.0-or-later` (`docs/images/README.md`, `licenses/BOLHA-ASSETS.md`).

| Arquivo | Tipo / Dimensão | Tamanho (bytes) | SHA-256 (prefixo 12 hex) | Origem / Commit de entrada |
|---|---|---|---|---|
| `docs/images/README.md` | Markdown | 227 | `9d6e7f3e60ec` | `630d889ac4` (`License Bolha artwork and animations under GPL`) |
| `docs/images/bolha-qt.png` | PNG `1140x650` | 103.600 | `24866ac41e49` | `1bc7eb9240` (`Import Bolha as a Pestinha community fork`) |
| `docs/images/bolha-states.jpg` | JPEG | 34.597 | `e901f9c8012f` | `1bc7eb9240` (`Import Bolha as a Pestinha community fork`) |
| `docs/images/bolha-qt-050.png` | PNG `768x512` | 87.655 | `120276cb769d` | `95fb9c3c55` (`feat: share Bolha behavior and expressions across Android and desktop`) |
| `docs/images/bolha-050-expressoes.png` | PNG `960x545` | 168.458 | `051c01ec8874` | `5f55aff541` (`Refine Bolha mouth gestures and extend speech reading time`) |
| `docs/images/bolha-054-expressoes.png` | PNG `1440x860` | 134.454 | `a4c6d06576b7` | `f2de7cffc5` (`Prepare Bolha 0.5.4 release notes and approved animation previews`) |
| `docs/images/bolha-brincando.png` | PNG `820x370` | 45.168 | `fc92acbadad3` | `1bab9e1c06` (`Improve notebook and running expressions; simplify community guides`) |
| `docs/previews/visual-polish-045.png` | PNG `1080x670` | 120.009 | `2b6fd5b59cd0` | `e51649adbc` (`Fix toy edge contacts and polish native Bolha expressions and dialogue`) |
| `docs/previews/notebook-045.gif` | GIF `440x280` | 528.239 | `a6bad1b5602b` | `e51649adbc` |
| `docs/previews/bolha-054-animacoes.gif` | GIF `600x358` | 1.541.512 | `802bef1cd585` | `f2de7cffc5` |
| `docs/previews/bolha-corrida.gif` | GIF `820x370` | 1.852.522 | `c81622fb9156` | `1bab9e1c06` |
| `docs/previews/bolha-notebook.gif` | GIF `900x450` | 40.024 | `03d3fac215cb` | `1bab9e1c06` |

---

## 3. Artes Vetoriais em Código (`bolha/objects.py`, `bolha/character.py` e Android)

| Módulo / Elemento | Procedência e Linhagem | Autoria / Créditos | Licença |
|---|---|---|---|
| `bolha/character.py` & `bolha/facial_motion.py` | Desenho vetorial e curvas faciais originais da personagem **Bolha** (esfera, anel gradiente, olhos, orelhas, boca e efeitos) | André Ribeiro Lima (KukySolutions) | `GPL-3.0-or-later` |
| `bolha/objects.py` — `paint_ball()` & `paint_notebook()` | Adaptados de `pestinha/body/bolinha.py` e `pestinha/world/notebook.py` do **Pestinha** (commit `ca03a48136d2f97b9b58bbc7ae4e307bb408048d`); o notebook foi redesenhado para a Bolha (paleta lavanda) | **@mille-okws e colaboradores** (Pestinha original) + adaptação de **André Ribeiro Lima** | `GPL-3.0-or-later` |
| `bolha/objects.py` — `paint_peanut()` / `peanut_shape()` | Casca de amendoim vetorial criada do zero em código Qt (`QPainterPath`), sem imagem externa | André Ribeiro Lima (KukySolutions) | `GPL-3.0-or-later` |
| `android/.../BolhaRenderer.java` | Portado do renderer Qt de `bolha/character.py` e `bolha/facial_motion.py` + linhagem Pestinha | André Ribeiro Lima + créditos a `@mille-okws` no cabeçalho | `GPL-3.0-or-later` |
| `android/.../ObjectRenderer.java` | Portado de `bolha/objects.py` (notebook, bolinha e amendoim), preservando créditos ao Pestinha | `@mille-okws` e colaboradores + André Ribeiro Lima | `GPL-3.0-or-later` |

---

## 4. Ativos e Fontes de `bolha-site/assets/` (`wt-site`)

| Arquivo | Tipo / Dimensão | Tamanho (bytes) | SHA-256 (prefixo 12 hex) | Origem / Derivação | Licença |
|---|---|---|---|---|---|
| `bolha-site/assets/bolha-mark.svg` | SVG `viewBox 0 0 64 64` | 563 | `dbe69b700c38` | Marca vetorial derivada da Bolha | `GPL-3.0-or-later` (créditos em `wt-site/README.md`) |
| `bolha-site/assets/bolha-corpo.png` | PNG `1200x240` (5 quadros `240x240`) | 233.422 | `8e5b3c0619e6` | Exportado de `bolha/character.py` (v0.5.9.0) via `wt-site/tools/export-native-art.py` | `GPL-3.0-or-later` |
| `bolha-site/assets/bolha-brinquedos.png` | PNG `176x88` (2 quadros `88x88`) | 16.664 | `423ba236131a` | Exportado de `bolha/objects.py` (`paint_ball`, `paint_peanut`) via `export-native-art.py` | `GPL-3.0-or-later` (derivado do Pestinha + próprio) |
| `bolha-site/assets/bolha-notebook.png` | PNG `2400x144` (12 quadros `200x144`) | 15.941 | `f1fbbfd9b0da` | Exportado de `bolha/objects.py` (`paint_notebook`) via `export-native-art.py` | `GPL-3.0-or-later` (derivado do Pestinha + redesenho) |
| `bolha-site/assets/rethink-sans-latin.woff2` | Fonte WOFF2 (subset latin) | 35.676 | `c09b45b96be1` | Projeto Rethink Sans (`https://github.com/hans-thiessen/Rethink-Sans`) | **`OFL-1.1`** (SIL Open Font License 1.1) |
| `bolha-site/assets/OFL-Rethink-Sans.txt` | Texto integral OFL 1.1 | 4.399 | `3a694f4b24dd` | `Copyright 2022 The Rethink Sans Project Authors` | `OFL-1.1` |

---

## 5. Ativos do `pestinha` e Histórico Git dos PNGs Opcionais Excluídos da GPL

No repositório original `mille-okws/pestinha`, o `README.md` declara expressamente:
> *"O código do Pestinha é software livre, sob a GNU GPL v3.0 ou posterior (LICENSE)... **As imagens e os textos de `assets/` não estão cobertos por esta licença**."*

E `pestinha/assets/LEIA-ME.txt` reforça que os arquivos de `pets/<pet>/` e `assets/comum/` são separados. Por essa razão jurídica, ao importar o fork da Bolha no commit **`1bc7eb9240e13b92c4354b5e16e2cdafe73ddbaa`** (*"Import Bolha as a Pestinha community fork"*, 2026-11-06), **todos os arquivos de imagem e texto não-GPL do Pestinha foram removidos da árvore**:

- **Removidos em `1bc7eb9240` (`assets/comum/`):**
  - `assets/comum/bolinha_papel.png` (69.008 bytes → removido)
  - `assets/comum/bolinha_tenis.png` (1.480.696 bytes → removido)
  - `assets/comum/notebook.png` (197.781 bytes → removido)
  - `assets/comum/programas.json` (8 linhas → removido)
  - `assets/LEIA-ME.txt` (27 linhas → removido)
- **Removidos em `1bc7eb9240` (`docs/imagens/` do Pestinha):**
  - `docs/imagens/contente_antes_depois.png` (5.645 bytes → removido)
  - `docs/imagens/dormindo_zzz.png` (7.015 bytes → removido)
  - `docs/imagens/expressoes_bryan_jorge.png` (33.144 bytes → removido)
  - `docs/imagens/protesto_cartazes.png` (13.839 bytes → removido)
  - `docs/imagens/prints_protesto/3_greve.png`, `4_revolucao_1.png`, `4_revolucao_2.png` (removidos)
- **Personagens do Pestinha (`pets/bryan/`, `pets/jorge/`):**
  - Permanecem apenas no repositório upstream `pestinha` (incluindo `pets/jorge/bolinha_papel.png`, `memes/`, `cartazes.txt`, `recadinhos.txt`); **não fazem parte** do repositório `wt-bolha` nem de nenhum pacote da Bolha.
- **Substituição técnica:** a Bolha utiliza os desenhos vetoriais em código (`bolha/objects.py` e `bolha/character.py`) e os SVGs próprios (`assets/bolha/`), identificados nos avisos como `GPL-3.0-or-later`.
- **Nota de higiene do histórico Git:** embora removidos da árvore atual em `1bc7eb9240`, os blobs originais do Pestinha anteriores ao fork permanecem alcançáveis nos commits ancestrais `42f92e1` e `0056fbf` no histórico Git do `kuky13/bolha` (o que é esperado em forks Git do Pestinha público, desde que nenhum binário da Bolha os empacote).

---

## Regeneração e correspondência com os arquivos públicos

A exportação executada com `QT_QPA_PLATFORM=offscreen`, PySide6 6.11.3 e o script `tools/export-native-art.py` do site a partir de `git archive v0.5.9.0` produziu três PNGs byte a byte idênticos aos arquivos do site. Os SHA-256 começam em `8e5b3c0619e6`, `423ba236131a` e `f1fbbfd9b0da`. A tag da Bolha resolve ao commit `82b96f27e98d27f35ce062caaf229718b9b737e2`. [Tag da Bolha](https://github.com/kuky13/bolha/tree/v0.5.9.0), [site](https://github.com/kuky13/bolha-site).

A fonte Latin Rethink Sans 400–800 usada no site tem SHA-256 `c09b45b96be12831873317869fce88361278ba47a9bfc18d5c14bfe6f8a85f01`, igual ao arquivo fornecido pelo Google Fonts. O aviso OFL do site difere do aviso do Google Fonts apenas pelo espaço final de uma linha. [Arquivo WOFF2](https://fonts.gstatic.com/s/rethinksans/v7/AMOWz4SDuXOMCPfdoglY9JQEVFi3.woff2), [OFL](https://github.com/google/fonts/blob/main/ofl/rethinksans/OFL.txt).

## Referências da Drippy e ativos herdados

- O código atual usa objetos Qt desenhados com QPainter a partir dos fallbacks do Pestinha. O notebook e a bolinha correspondem aos caminhos de desenho em código do commit `ca03a48136d2f97b9b58bbc7ae4e307bb408048d` e não carregam as fotos dos objetos do upstream. [Fallback do notebook](https://github.com/mille-okws/pestinha/blob/ca03a48136d2f97b9b58bbc7ae4e307bb408048d/notebook.py#L70), [fallback da bolinha](https://github.com/mille-okws/pestinha/blob/ca03a48136d2f97b9b58bbc7ae4e307bb408048d/bolinha.py#L76).
- Arquivos opcionais excluídos da GPL pelo Pestinha fazem parte da ancestralidade Git do fork. A comparação de procedência deve distinguir essa ancestralidade da árvore atual e dos arquivos do pacote final.
- Os instaladores v0.1.0 e v0.1.1 contêm o aviso `resources/licenses/DRIPPY-ASSETS.md`, publicado com declaração CC BY-NC 4.0, e a busca encontrou ocorrências do termo no ASAR. A árvore atual tem referências nominais para migração e documentação. As ocorrências de nome e licença não evidenciam a publicação de guias privados. Uma conclusão sobre um arquivo individual precisa do caminho, origem e conteúdo. [Histórico](HISTORICO-RELEASES.md).
