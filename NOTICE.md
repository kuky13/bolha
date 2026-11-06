# Autoria, origem e licenças

## Origem do projeto

A Bolha é um fork comunitário baseado no sistema do **Pestinha**, criado por
[@mille-okws](https://github.com/mille-okws) com contribuições de
[seus colaboradores](https://github.com/mille-okws/pestinha/graphs/contributors).
Repositório original: <https://github.com/mille-okws/pestinha>.

O histórico Git desta cópia parte do Pestinha no commit
`984fb8677093cd868bf4f9712a43f19b44215f75`. O cérebro e partes da física
integrados em `brain/pestinha/` também preservam a linhagem do código que a
Bolha já adaptava desde `ca03a48136d2f97b9b58bbc7ae4e307bb408048d`.
As janelas, a interface e as adaptações da personagem Bolha foram desenvolvidas
neste fork por André Ribeiro Lima (KukySolutions), aproveitando esse sistema.

O código do Pestinha usado pela Bolha inclui rede neural pulsada, emoções,
memória, aprendizado, física, sensores opcionais e comportamentos. Os desenhos
Qt do notebook e dos brinquedos também vêm do Pestinha. Os módulos e pontos de
integração estão identificados nos cabeçalhos dos arquivos Python.

## Licenças

O código da Bolha e o código do Pestinha distribuídos neste projeto estão sob
a **GNU GPL versão 3 ou posterior (`GPL-3.0-or-later`)**, a mesma licença do
Pestinha. Veja o arquivo [LICENSE](LICENSE). Contribuições ao código seguem a
GPL e devem preservar os créditos e avisos de autoria.

As artes próprias da personagem Bolha, seus ícones e memes estão separadas do
código e são licenciadas sob **CC BY-NC 4.0**. A restrição não comercial vale
para essas artes; ela não acrescenta uma restrição não comercial ao código
GPL. Consulte [licenses/BOLHA-ASSETS.md](licenses/BOLHA-ASSETS.md).

Os memes, textos e imagens dos personagens do Pestinha não integram os arquivos
da distribuição da Bolha. Eles permanecem no repositório upstream e no histórico
de origem sob os avisos e direitos definidos por seus autores.

Qt, PySide6, Shiboken6, CPython, NumPy, psutil, pywin32, PyInstaller e NSIS
mantêm suas próprias licenças. Consulte
[packaging/THIRD-PARTY-NOTICES.txt](packaging/THIRD-PARTY-NOTICES.txt).
