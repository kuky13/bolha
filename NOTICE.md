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
Qt da bolinha e do notebook foram adaptados do Pestinha. O amendoim tem desenho
próprio. Os módulos e pontos de integração têm origem identificada nos
cabeçalhos dos arquivos Python.

## Licenças

O código da Bolha e o código do Pestinha distribuídos neste projeto estão sob
a **GNU GPL versão 3 ou posterior (`GPL-3.0-or-later`)**, a mesma licença do
Pestinha. Veja o arquivo [LICENSE](LICENSE) e as declarações por caminho em
[REUSE.toml](REUSE.toml). Contribuições ao código seguem a GPL e devem
preservar os créditos e avisos de autoria.

As artes, ícones, animações, memes e textos próprios da Bolha também estão sob
**GPL-3.0-or-later**, com autoria de André Ribeiro Lima (KukySolutions).
Consulte [licenses/BOLHA-ASSETS.md](licenses/BOLHA-ASSETS.md).

A distribuição atual usa desenhos Qt adaptados do código GPL do Pestinha. As
imagens e os textos da pasta `assets/` do Pestinha têm condições próprias e não
integram o pacote atual da Bolha. Guias privados de referência estão fora da
distribuição. Para versões anteriores, consulte o
[histórico da auditoria](docs/compliance/HISTORICO-RELEASES.md).

## Componentes redistribuídos

Consulte os avisos de [Windows](packaging/THIRD-PARTY-NOTICES.txt),
[Android](android/licenses/NOTICE.md) e a
[matriz de procedência e licenças](docs/compliance/MATRIZ-CONFORMIDADE.md)
para os componentes, versões, licenças e fontes verificadas.

## Integrações do Windows

- [Multi-Monitor-Mouse-Finder](https://github.com/inspiringsource/Multi-Monitor-Mouse-Finder),
  de **inspiringsource**, inspirou o halo e a indicação entre monitores. A Bolha usa
  um desenho e uma implementação próprios em Qt. Referência MIT no commit
  [4043c59](https://github.com/inspiringsource/Multi-Monitor-Mouse-Finder/tree/4043c59ca702cec8f0853fb93fe31eba3d235f6e).
- [Wireless Device Battery Monitor (BatteryHub)](https://github.com/krisgfx9/Wireless-Device-Battery-Monitor),
  de **krisgfx9 e colaboradores**, fornece a leitura nativa de bateria em
  `BatteryHub.exe --json`. O pacote usa a versão portátil não modificada
  [1.1.0](https://github.com/krisgfx9/Wireless-Device-Battery-Monitor/releases/tag/v1.1.0),
  `GPL-3.0-only`. A Bolha interpreta a saída e apresenta a lista e os alertas.
  O pacote original e as fontes estão espelhados em
  [third_party/batteryhub](third_party/batteryhub).
- [HeadsetControl](https://github.com/Sapd/HeadsetControl), de **Sapd e
  colaboradores**, é distribuído com BatteryHub para a leitura de headsets
  compatíveis. A versão
  [4.3.0](https://github.com/Sapd/HeadsetControl/releases/tag/4.3.0) usa
  `GPL-3.0-only`. Os avisos originais acompanham os binários. As fontes com instruções de compilação estão nos arquivos `BatteryHub-1.1.0-source.tar.gz`
  e `headsetcontrol-4.3.0.tar.gz` da mesma publicação Windows.
- [Python/WinRT (PyWinRT)](https://github.com/pywinrt/pywinrt/tree/v3.2.1),
  versão `3.2.1` (`MIT`), dá acesso às sessões locais de mídia do Windows pelos
  pacotes `winrt-runtime`, `winrt-Windows.Foundation`,
  `winrt-Windows.Foundation.Collections`, `winrt-Windows.Storage.Streams` e
  `winrt-Windows.Media.Control`. Veja [a licença](licenses/PYWINRT-MIT.txt).

## Sincronização com o Pestinha

A sincronização com a [main do Pestinha no commit `0bb768a`](https://github.com/mille-okws/pestinha/tree/0bb768a2be024221ee1da62cc335362279d912d6)
incorpora o histórico do fork e adapta a interpolação de expressões a partir
da valência e ativação do cérebro. A Bolha mantém seus próprios desenhos,
comportamentos, instaladores e superfícies Windows e Android. Os executáveis
originais e os testes específicos da interface original seguem no Pestinha.
