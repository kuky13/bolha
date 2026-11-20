# Personalizar sua mascote

Este guia mostra onde fazer mudanças pequenas no código-fonte. Ele pressupõe
que você baixou o repositório e consegue editá-lo; não é preciso mudar o perfil
da Bolha para alterar o desenho ou as falas.

## Antes de editar código

Na Central da Bolha já há controles para tamanho, opacidade, boca, brinquedo,
escala dos objetos, falas, atividades, aprendizado e reações online. No Android,
esses controles ficam na Central do app. Use-os quando só quiser ajustar a
Bolha para você.

Para criar outra aparência ou comportamento, faça uma cópia do repositório e
edite o código. Antes de executar sua cópia, feche a Bolha instalada e faça
backup do perfil: por padrão, o código-fonte e o app instalado usam o mesmo
`%APPDATA%\bolha` no Windows (ou `~/.config/bolha` no Linux), inclusive o
arquivo que impede duas instâncias de usarem o perfil ao mesmo tempo. Não edite
`config.json` enquanto a Bolha estiver aberta: o app pode regravá-lo.

## Onde mudar

| O que personalizar | Arquivo principal | Exemplo simples |
|---|---|---|
| Cor da esfera | [`bolha/character.py`](../bolha/character.py) | Em `_body`, troque as cores da esfera no gradiente `core` para ajustar os tons calmos e irritados. |
| Cor dos olhos e traços dourados | [`bolha/character.py`](../bolha/character.py) | Mude `GOLD = '#ffd364'`. |
| Expressões, boca e piscadas | [`bolha/character.py`](../bolha/character.py) e [`bolha/facial_motion.py`](../bolha/facial_motion.py) | `draw_character` desenha rosto e boca; `feature_profile` e `mouth_state` definem movimento e expressão. |
| Frases e pensamentos | [`bolha/dialogue.py`](../bolha/dialogue.py) | Adicione ou troque uma frase na tupla da categoria, como `'curioso'` ou `'sono'`, dentro de `LINES`. |
| Desenho e cores do notebook | [`bolha/objects.py`](../bolha/objects.py) | `paint_notebook` desenha a tela, o prompt, as teclas e a base; os tons estão em valores `QColor('#...')`. |
| Memes, cartazes e bilhetes próprios | [`assets/bolha/content/`](../assets/bolha/content/) | Veja os formatos aceitos e os créditos em [`assets/bolha/README.md`](../assets/bolha/README.md). |

Exemplo: em `bolha/character.py`, a esfera calma e a irritada são misturadas
nestes pontos do gradiente `core`:

```python
core.setColorAt(0, _mix_color('#25252c', '#961e2e', anger))
core.setColorAt(.55, _mix_color('#151519', '#52111c', anger))
core.setColorAt(1, _mix_color('#0b0b0e', '#26080d', anger))
```

Troque os hexadecimais por valores `#RRGGBB` válidos. Para uma expressão
adormecida mais quieta, `bolha/motion.py` define o balanço das orelhas nessa
linha de `animation_pose`:

```python
ear_raise=-1. - 1.5 * closing + .7 * breath
```

Diminuir `.7` reduz a parte do movimento ligada à respiração. Para trocar uma
fala, edite um item na tupla da categoria correspondente em `LINES`, mantendo
a vírgula entre itens. Salve e reinicie a edição de computador para ver o resultado.

## Mapa curto do código

| Parte | Caminho | Função |
|---|---|---|
| Decisões e integração | [`brain/game.py`](../brain/game.py) | Liga cérebro, ações, estado e física em `Game`. |
| Rede neural, física e comportamento base | [`brain/pestinha/`](../brain/pestinha/) | Núcleo adaptado do Pestinha; consulte `NOTICE.md` para origem. |
| Coreografia visual | [`bolha/motion.py`](../bolha/motion.py) | Traduz gestos e estados em expressões animadas. |
| Desenho da mascote | [`bolha/character.py`](../bolha/character.py) | Desenha corpo, olhos, orelhas e boca no Qt. |
| Preferências e controles | [`bolha/preferences.py`](../bolha/preferences.py), [`bolha/dialogs.py`](../bolha/dialogs.py) | Define opções persistidas e a Central no computador. |
| Janelas e execução | [`bolha/pet.py`](../bolha/pet.py), [`bolha/app.py`](../bolha/app.py) | Apresenta a mascote e inicia o app Qt. |

O notebook atual não carrega um tema ou um arquivo de texto editável: o desenho
é feito com formas e cores no código. Para inserir um símbolo novo na tela,
adicione linhas dentro de `paint_notebook` em `bolha/objects.py`, depois do
retângulo escuro da tela. Por exemplo, duas linhas formam um símbolo de mais:

```python
p.setPen(QPen(QColor('#ffd16e'), 1.4))
p.drawLine(QPointF(90, 26), QPointF(96, 26))
p.drawLine(QPointF(93, 23), QPointF(93, 29))
```

Essas coordenadas ficam dentro da tela desenhada pelo método. As falas sobre
trabalho são conteúdo separado em `bolha/dialogue.py`.

## Computador e Android

No computador, o app é Python 3.11 com Qt/PySide6. `bolha/character.py` e
`bolha/objects.py` desenham a mascote e objetos da edição Qt.

No Android, o cérebro, a física e a política de falas usam Python em
`android/app/src/main/python/mobile.py` e módulos compartilhados, mas o rosto
e os objetos são desenhados em Java: `android/app/src/main/java/solutions/kuky/bolha/mobile/BolhaRenderer.java`
e `ObjectRenderer.java`. Portanto, uma mudança visual em `bolha/character.py`
ou `bolha/objects.py` não aparece automaticamente no app Android. Para manter
as duas edições parecidas, faça a alteração visual correspondente também nos
arquivos Java. As falas em `bolha/dialogue.py` são compartilhadas.

## Rodar, verificar e compilar sua cópia

Para rodar a edição de computador pelo código, use Python 3.11 na pasta do
projeto:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python main.py
```

Edite e reinicie o app para ver o desenho. Para rodar as verificações antes de
compilar:

```powershell
.venv\Scripts\python -m pytest -q
```

No Windows x64, gere um instalador próprio com:

```powershell
.venv\Scripts\python scripts/build_native.py --output release
```

O resultado fica em `release/`. O processo exige Windows x64 e Python 3.11;
detalhes e limites estão em [Compilar e validar](BUILD.md). Esse comando só
compila localmente. Ele não publica sua mudança nem altera a página de versões.
O instalador produzido continua usando o identificador do produto Bolha e,
quando instalado no Windows, consulta o feed oficial de atualizações. Para
distribuir um produto independente, é preciso configurar de forma coerente o
diretório de dados em `bolha/app.py` e `bolha/installation.py`, o identificador
do produto em `bolha/installation.py`, o repositório do atualizador
(`REPOSITORY` em `bolha/updates.py`) e a identidade do instalador em
`packaging/bolha.nsi`; renomear apenas o app ou este guia não isola dados nem
atualizações. Ao rodar `main.py` pelo código, o atualizador automático fica
desligado fora do modo de teste.

Para o Android, veja os requisitos e o comando de build em
[`android/README.md`](../android/README.md). A edição móvel tem suas próprias
verificações e precisa ser compilada separadamente.

## Perfil, compatibilidade e privacidade

O código-fonte é separado do perfil salvo. No Windows, o perfil fica em
`%APPDATA%\bolha`; no Linux, em `~/.config/bolha`. No Android, os dados ficam
no armazenamento privado do app. Essas pastas não são o local para desenhar ou
alterar código. Não inclua seu perfil, aprendizado, logs, credenciais ou dados
pessoais no repositório.

As preferências usam chaves e validação próprias, e as edições têm controles
específicos de plataforma. Embora parte do código do cérebro e dos formatos
seja compartilhada, não há garantia de que copiar uma pasta de perfil entre
Windows, Linux e Android funcione. Atualizações da edição Android preservam os
dados quando instaladas sobre o app existente com a chave do projeto; desinstalar
pode apagar os dados privados. Faça backup antes de experimentar migrações.

Ao rodar `main.py`, a cópia não consulta atualizações automaticamente; a edição
instalada faz isso. Reações online ainda podem buscar GIFs quando habilitadas.
Desligue **Reações online** na Central se não quiser essa busca. As opções de
leitura local de contexto também podem ser desligadas individualmente. Não
acrescente no código coleta ou envio de perfil sem informar claramente quem usa
sua versão.

## Créditos e redistribuição

O código, as artes e animações próprias da Bolha estão sob **GPL-3.0-or-later**.
O projeto é baseado no Pestinha, de **@mille-okws e colaboradores**. Ao
redistribuir uma versão modificada, preserve os créditos e avisos, inclua a
licença e disponibilize o código-fonte correspondente conforme a GPL. Consulte
[`NOTICE.md`](../NOTICE.md), [`LICENSE`](../LICENSE) e
[`licença das artes`](../licenses/BOLHA-ASSETS.md). Os memes e textos originais
do Pestinha não fazem parte do pacote da Bolha; respeite os avisos do histórico
upstream. Não publique materiais privados de referência.
