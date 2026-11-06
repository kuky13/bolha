# Como contribuir

A Bolha é um projeto open source da comunidade. Relatos de erros, sugestões e
pull requests são bem-vindos.

## Desenvolver e validar

Use Python 3.11 e instale as dependências de desenvolvimento:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python -m pytest -q
```

No Linux, execute os testes Qt em modo sem janela:

```sh
QT_QPA_PLATFORM=offscreen python -m pytest -q
```

## Licenças e privacidade

O código, as artes e as animações próprias da Bolha são distribuídos sob
GPL-3.0-or-later. Preserve os créditos ao Pestinha, a mille-okws e aos
contribuidores, descritos em `NOTICE.md`.

Não envie guias privados de referência da Drippy, dados pessoais, credenciais
ou arquivos de aprendizado de usuários em issues, pull requests ou anexos.
Consulte `licenses/BOLHA-ASSETS.md` para a licença dos recursos visuais.
