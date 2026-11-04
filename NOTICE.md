# Autoria e componentes

Bolha: André Ribeiro Lima (KukySolutions), 2026.

O motor em `brain/pestinha/` deriva de **Pestinha**, de mille-okws e seus
contribuidores, sob GPL-3.0-or-later. Base: commit
`ca03a48136d2f97b9b58bbc7ae4e307bb408048d`.

Fonte: https://github.com/mille-okws/pestinha

Foram preservados o cérebro LIF, aprendizado, memória, necessidades, física
e controladores. A versão 0.3 usa janelas Qt nativas e um único processo;
acrescenta objetivos persistentes, rotina, desenho circular e controles locais.
Imagens, memes e pacotes de conteúdo do Pestinha não foram copiados.

O avatar animado foi extraído do aplicativo desktop original, com autorização do
titular neste projeto; foram removidas as integrações remotas e a geometria
visual foi separada da lógica. Os memes e recados desta distribuição são novos.

Código próprio: GPL-3.0-only. Código derivado do Pestinha mantém seus avisos
GPL-3.0-or-later. Artes: consulte `licenses/BOLHA-ASSETS.md`.

Qt, PySide6, Shiboken6, CPython, NumPy, psutil, pywin32, PyInstaller e NSIS
mantêm suas próprias licenças. Consulte `packaging/THIRD-PARTY-NOTICES.txt`.
O pacote leva o texto GPLv3, as licenças das artes e os avisos coletados das
distribuições Python. Qt/PySide6 são usados sob a opção GPLv3 compatível com
este programa, com bibliotecas compartilhadas separadas.
