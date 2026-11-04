# Compilar e validar a Bolha nativa

Requisitos: Windows x64, Python3.11, git e aproximadamente3GB livres. A aplicação
não exige Python instalado no computador de destino. QtCore/QtGui/QtWidgets vêm
de PySide6-Essentials6.11.3; QtWebEngine, QML e a antiga camada web não entram.

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python -m pytest -q
.venv\Scripts\python scripts/build_native.py
```

O compilador NSIS3.11 portátil é baixado do SourceForge e validado pelo SHA-256
publicado pelo projeto. Se já tiver makensis, use `--makensis C:\caminho\makensis.exe`.
O script gera o ícone sem boca a partir do mesmo desenho Qt do aplicativo,
coleta licenças, rejeita bibliotecas web e cria instalador, `latest.yml` e
`SHA256SUMS.txt`. A versão do aplicativo fica em `bolha/__init__.py` e
`pyproject.toml`; uma versão de teste pode ser passada por `--version`.

## Isolamento para testes no Windows

Nunca teste instaladores antigos da Bolha no computador de uso diário: eles
escrevem o GUID real no registro mesmo quando `/D=` aponta para pasta temporária.
Use runner/VM descartável para0.1.0/0.2.1→0.3.0.

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
APPDATA nunca é apagado pelo instalador/desinstalador. A desinstalação também
preserva arquivos não inventariados dentro da pasta do aplicativo.

O aplicativo experimental não possui certificado de assinatura. SHA-256 confirma
integridade em relação à release HTTPS consultada; uma conta mantenedora comprometida
pode publicar uma release maliciosa. Proteja a conta GitHub e revise alterações do pipeline.
