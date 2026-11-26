# Como contribuir

A Bolha é um projeto open source da comunidade. Relatos de erros, sugestões e
pull requests são bem-vindos.

Para criar uma versão própria, comece pelo [guia de personalização](docs/PERSONALIZAR.md).
Para usar a Bolha sem alterar o código, veja o [guia de uso](docs/USO.md).

## Convivência e manutenção

Discuta ideias e código com respeito. Assédio, discriminação e publicação de
dados pessoais comprometem a colaboração. Encaminhe relatos sensíveis em
particular pelo contato indicado em [SECURITY.md](SECURITY.md).

KukySolutions mantém a distribuição oficial, revisa as contribuições e decide
quando publicar uma versão. Propostas da comunidade podem ser discutidas em
issues ou pull requests. O [histórico Git](https://github.com/kuky13/bolha/graphs/contributors)
registra as contribuições.

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

## Certificado de Origem do Desenvolvedor (DCO)

Para novas contribuições, use `git commit -s` para incluir a linha
`Signed-off-by: Nome <email>` do [Developer Certificate of Origin 1.1](https://developercertificate.org/).
Com essa declaração, você confirma que tem direito de enviar a mudança sob a
licença aplicável. Use um e-mail que possa aparecer no histórico público.

- **Sem exigência retroativa:** o DCO vale apenas para novas contribuições e
  não exige reescrita nem assinatura retroativa do histórico anterior.
- **Sem transferência de direitos:** assinar o DCO não transfere nem cede
  direitos autorais; você mantém a titularidade sobre as suas contribuições.

## Licenças, créditos e privacidade

O código, as artes e as animações próprias da Bolha são distribuídos sob
**GPL-3.0-or-later**. Preserve os créditos ao **Pestinha**
([mille-okws/pestinha](https://github.com/mille-okws/pestinha)), a
[@mille-okws](https://github.com/mille-okws) e colaboradores, bem como a
**André Ribeiro Lima** (**KukySolutions**), conforme descrito em `NOTICE.md`.

Não envie materiais privados de referência não publicados, dados pessoais,
credenciais ou arquivos de aprendizado de usuários em issues, pull requests ou
anexos. Consulte `licenses/BOLHA-ASSETS.md` para a licença dos recursos visuais.
