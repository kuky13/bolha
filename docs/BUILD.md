# Compilar e validar a Bolha nativa

Requisitos: Windows x64, Python 3.11, git e aproximadamente 3 GB livres. A aplicação
não exige Python instalado no computador de destino. QtCore/QtGui/QtWidgets vêm
de PySide6-Essentials 6.11.3; QtWebEngine, QML e a antiga camada web não entram.

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python -m pytest -q
.venv\Scripts\python scripts/build_native.py
```

O compilador NSIS 3.11 portátil é baixado do SourceForge e validado pelo SHA-256
publicado pelo projeto. Se já tiver makensis, use `--makensis C:\caminho\makensis.exe`.
O script gera o ícone sem boca a partir do mesmo desenho Qt do aplicativo,
coleta licenças, rejeita bibliotecas web e cria instalador, `latest.yml` e
`SHA256SUMS.txt`. A versão do aplicativo fica em `bolha/__init__.py` e
`pyproject.toml`; uma versão de teste pode ser passada por `--version`.

## Isolamento para testes no Windows

Nunca teste instaladores antigos da Bolha no computador de uso diário: eles
escrevem o GUID real no registro mesmo quando `/D=` aponta para pasta temporária.
Use runner/VM descartável para 0.1.0/0.2.1→0.3.0.

O instalador nativo aceita `/TEST` somente com `BOLHA_TEST=1` e caminhos explícitos
em `BOLHA_TEST_USER_DATA` e `BOLHA_TEST_INSTALL_DIR`. Nesse modo não escreve
registro, atalhos ou inicialização. O aplicativo herda esse ambiente por
CreateProcess; o perfil real e o cache real não são usados. `BOLHA_TEST_STATUS=1`
expõe o estado da atualização em JSON local para validação. Um feed alternativo
só é aceito com modo teste e origem `http://127.0.0.1` na mesma porta.

## Atualizações e recuperação

O app consulta Releases de kuky13/bolha, valida tamanho e SHA-256 e confere o
arquivo novamente antes de instalar. O manifesto e o executável ficam na mesma
release. SHA-512 em latest.yml permite a transição das versões Electron.
O instalador não aceita uma pasta existente arbitrária: exige a instalação
registrada do produto ou o marcador nativo. Reparse points/junctions são recusados.
A instalação anterior é renomeada no mesmo volume antes da troca; somente o
processo iniciado pelo instalador pode ser encerrado na recuperação.

Depois do primeiro desenho e ciclo do cérebro saudáveis, arquivos nativos do
backup com hashes conhecidos são removidos. Arquivos alterados/desconhecidos e
a instalação Electron anterior são preservados e registrados localmente.
A pasta original de aprendizado não é renomeada na atualização: perfis da 0.1
continuam no caminho legado, e perfis novos/0.2 usam `brain/bolha`. Assim uma
recuperação da 0.1 lê os mesmos arquivos, incluindo aprendizado salvo depois.
APPDATA nunca é apagado pelo instalador/desinstalador. A desinstalação também
preserva arquivos não inventariados dentro da pasta do aplicativo.

O aplicativo experimental não possui certificado de assinatura. SHA-256 confirma
integridade em relação à release HTTPS consultada; uma conta mantenedora comprometida
pode publicar uma release maliciosa. Proteja a conta GitHub e revise alterações do pipeline.

## Pipeline e consumo de Actions

Há um único workflow Windows: ele roda por tag ou acionamento manual. Commits e
PRs não geram instaladores automaticamente. A fixture da versão seguinte reutiliza
o bundle já compilado, alterando só a versão e o instalador. Artefatos de teste
expiram em sete dias. O controlador Node/Playwright existe somente para validar
versões Electron antigas em runner descartável; não é dependência do aplicativo.
A execução manual pode desmarcar o teste legado; uma tag sempre exige as duas
migrações anteriores antes de publicar. Não há alteração de cobrança ou de
workflows de outros repositórios.

O hook padrão de QtGui também coleta o plugin opcional TUIO (multitoque via rede).
O build remove esse plugin e retira Qt6Network.dll somente depois de varrer os
imports PE, inclusive os carregados com atraso, e confirmar que nenhum componente
restante precisa dela. A auditoria recusa ambos no pacote final. O atualizador
usa HTTPS da biblioteca padrão Python.

### Validar e publicar em uma única execução

A opção manual `publish_release` vem desligada. Para compilar, executar todos os
testes (incluindo as duas migrações Electron) e publicar os mesmos arquivos ao
final, use o branch que contém o código a publicar:

```powershell
gh workflow run windows.yml --repo kuky13/bolha --ref native/qt-0.3 -f legacy_validation=true -f publish_release=true
```

Não crie uma tag antecipadamente nesse fluxo. Somente o último passo, depois de
todos os testes passarem, cria `v<versão>` e a release no SHA exato compilado.
Se algum teste falhar, nenhuma tag ou release será criada. A opção de publicar
força os testes legados mesmo se `legacy_validation` for desmarcada. Para apenas
validar, omita `publish_release` ou use `false`.

A publicação manual recusa uma tag existente; a criação de uma release existente
falha sem sobrescrever arquivos. Não há `--clobber`, retag ou promoção de arquivos
de outro commit. Um erro durante a própria publicação deve ser inspecionado antes
de repetir, pois a API pode ter criado parte do resultado antes de uma falha de rede.
A execução por tag permanece disponível e confere a identidade do commit remoto.

O passo usa somente `github.token` como `GH_TOKEN`. Segundo a [documentação do
GitHub](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow#triggering-a-workflow-from-a-workflow),
um evento de push produzido por `GITHUB_TOKEN` não dispara outra execução do
workflow de tags. Assim a publicação manual não recompila o mesmo aplicativo.
