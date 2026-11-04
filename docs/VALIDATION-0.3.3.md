# Validação da candidata 0.3.3

A fonte **0.3.3** no branch `expressive/qt-animations` ([PR #2](https://github.com/kuky13/bolha/pull/2))
reúne todas as funcionalidades aprovadas após a base `37db6e5dd2233378e199e934e8481e2a47af3fac`:
raiva neural vermelha legível, efeitos de expressão que giram e se achatam junto
com o corpo, reação física do amendoim e da bolinha à aproximação do cursor,
pega firme com arremesso por impulso recente do mouse e reações online reais de
GIFs/imagens em memória RAM. A versão pública permanece **0.3.0**; esta etapa
prepara a candidata de teste, sem criar tag ou publicar release.

Uma fixture homônima `0.3.3` existiu anteriormente apenas como pacote reempacotado
de metadados para exercitar a atualização `0.3.2 → fixture 0.3.3` no CI da fonte
`ddcfa90` (sem nunca ter sido publicada). A candidata **0.3.3** atual possui seu
próprio código-fonte, SHA e evidências; o pipeline de CI testará dinamicamente
`0.3.3 → fixture 0.3.4`, sendo a fixture `0.3.4` exclusiva do runner de teste e
nunca entregue como versão real.

## Comportamento implementado na 0.3.3

- **Raiva neural vermelha e efeitos ancorados ao corpo**: quando a Bolha fica
  irritada (pelo tempo segurada, estado neural `ANGRY` ou reação ao soltar), a
  esfera escura sem boca e seu halo assumem um tom vermelho intenso, com
  pálpebras cerradas, orelhas rebaixadas e leve tremor local, sem deslocar o
  ponto de pega. Risquinhos de raiva, corações, estrelas e “zzz” recebem a mesma
  rotação (`angle + angle_offset`) e deformação (`squash`) do corpo em todos os
  ângulos (0°, 45°, 90°, 180° e 270°).
- **Reação física do amendoim e da bolinha ao cursor**: quando o sensor de
  cursor (`senseCursor`) está ativo, aproximar o ponteiro do amendoim ou da
  bolinha original aciona a física `push_from_cursor` do Pestinha no `Game.tick`,
  deslocando o brinquedo para o lado oposto com cooldown, limites de velocidade
  e respeito às bordas da tela, além de alimentar `NOVELTY`/`TOY_NEAR` e o olhar
  do cérebro. Sensores desligados, brinquedo guardado ou sendo arrastado,
  painéis abertos e modo oculto suprimem o chute.
- **Pega firme e impulso recente preservados**: mantém a pega pelo botão físico
  primário e o arremesso por velocidade recente (janela de 120 ms, filtro de
  4 DIP, teto de ±2500 DIP/s e giro `vx * 0,35`) da 0.3.2, com oscilação máxima
  de 3% de deformação e 1,5° de rotação enquanto segurada.
- **Reações online reais sem chave e 100% em RAM**:
  - **ReactionGIFs (fonte principal)**: consulta pública HTTPS na API WordPress
    (`https://www.reactiongifs.com/wp-json/wp/v2/posts`) com verificação de
    relevância do termo de humor em título, conteúdo ou URL de origem e allowlist
    estrita de host (`reactiongifs.com` / `www.reactiongifs.com`).
  - **Nekos.best (fallback anime)**: API pública HTTPS sem chave
    (`https://nekos.best/api/v2/<category>`) com `User-Agent: Bolha (https://github.com/kuky13/bolha)`,
    mapeada para a categoria emocional correspondente.
  - **Privacidade, memória e desligamento**: somente palavras genéricas de humor
    em inglês são enviadas. Os bytes de mídia permanecem exclusivamente em RAM
    (`bytes` → `QByteArray` → `QBuffer` → `QMovie` com `CacheNone` ou `QImage`
    com `KeepAspectRatio` e `SmoothTransformation`), nunca gravam arquivos ou
    cache em disco e são liberados ao fechar, ocultar, entrar em pânico ou
    desativar `onlineReactions` nas configurações. Falhas de rede descartam a
    reação silenciosamente sem penalizar o cérebro.
- **Cérebro e empacotamento**: o cérebro local mantém 470 neurônios, semente,
  memória e preferências, sem novas dependências. O script `scripts/audit_native.py`
  passou a exigir explicitamente a presença do decodificador
  `_internal/PySide6/plugins/imageformats/qgif.dll` no bundle Windows (coletado
  pelo hook padrão de `PySide6.QtGui`) e a registrar `gifDecoderPresent: true`
  no relatório JSON da auditoria.

## Validação local e em tempo real concluída (Linux / Qt offscreen)

Após o congelamento do código de aplicação e testes sobre a base `37db6e5`:

- **Suíte automatizada completa (Qt offscreen)**: **352 testes passaram** e
  **11 verificações específicas de Windows foram puladas** em 96,94 s (após a
  rodada inicial de 350 testes e os 2 testes adicionais de relevância do
  ReactionGIFs, escala `KeepAspectRatio` 2:1 e limite de tombstones de
  cancelamento). Os 12 testes focados em `tests/native/test_online_reactions.py`
  passaram em 8,07 s.
- **Testes de versão, metadados, auditoria `qgif.dll` e workflow**: verificados
  localmente após atualizar a versão para `0.3.3` e incluir a checagem de
  `PySide6/plugins/imageformats/qgif.dll` em `scripts/audit_native.py`.
- **Smoke em tempo real das APIs (sem arquivos em disco)**:
  - **ReactionGIFs (`angry`)**: retornou `"Fuming Angry"`
    (`https://www.reactiongifs.com/fuming-angry/`, `1.739.098` bytes, SHA-256
    `fed34c05a0f4d1b164166c8ca197a4ec6d9f17922d038ee645b84e5e49a67ce4`,
    `500×480`, 20 quadros animados em RAM).
  - **Nekos.best (`angry`)**: retornou `"Ansatsu Kyoushitsu: Second Season"`
    (`723.976` bytes, SHA-256
    `cde5c673629919784a17fc881be5e6c54d8ad9ea3add4b38605a61d4faf6d586`,
    `498×278`, 21 quadros animados em RAM).
  - **`ObjectWindow` real em Qt offscreen (`live-window.json`)**: buscou e
    exibiu `"Internal Rage"` (`https://www.reactiongifs.com/internal-rage/`,
    provedor `reactiongifs`, `1.261.670` bytes em memória), observou **14 quadros
    distintos**, confirmou a liberação dos buffers ao fechar (`released: true`)
    e verificou **0 arquivos de mídia gravados em disco** (`mediaFilesWritten: 0`).
- **Prévias Qt offscreen de raiva vermelha e brinquedos**: geradas com `Game.tick`
  a 60 Hz e `LIFBrain` ativo, comprovando a progressão de raiva (`maxAnger: 0,986`),
  o alinhamento dos efeitos nos ângulos `0°, 45°, 90°, 180°, 270°` e o
  deslocamento do amendoim e da bolinha para esquerda e direita quando o cursor
  passa próximo.

## Etapas Windows pendentes (próxima execução)

Nenhum resultado de compilação ou execução Windows da **0.3.3** é inventado ou
antecipado neste documento. As validações anteriores da 0.3.2 permanecem em
[VALIDATION-GRAB.md](VALIDATION-GRAB.md) e as da 0.3.1 em
[VALIDATION-EXPRESSIONS.md](VALIDATION-EXPRESSIONS.md). Permanecem pendentes para
a execução no CI Windows e no equipamento Windows:

1. **Compilação e auditoria no CI Windows (`windows.yml`)**: gerar o instalador
   `Bolha-Setup-0.3.3-x64.exe`, `latest.yml`, `SHA256SUMS.txt` e
   `THIRD-PARTY-NOTICES.txt` com `publish_release=false` e
   `legacy_validation=false`, confirmando na auditoria do bundle a presença de
   `_internal/PySide6/plugins/imageformats/qgif.dll`.
2. **Suíte completa de testes no Windows CI**: executar todos os testes
   automatizados no runner Windows (incluindo os 11 testes específicos de
   Windows/PowerShell pulados no Linux).
3. **Cenários nativos de instalação, atualização (`0.3.3 → fixture 0.3.4`) e
   recuperação no runner Windows**: validar os 10 cenários isolados de
   `scripts/test_windows_native.py` sem publicar a fixture `0.3.4`.
4. **Validação em Windows físico / RDC**: testar o instalador e o executável
   empacotado `Bolha.exe` 0.3.3 (incluindo a investigação/resolução do código de
   saída `2` observado anteriormente no modo `/TEST` isolado da 0.3.2 no
   notebook físico, a atualização sobre a versão instalada, a renderização real
   da raiva vermelha, o empurrão do amendoim/bolinha pelo cursor e a animação
   de GIFs online em RAM na área de trabalho Windows), além do uso manual
   prolongado e validação em dois monitores físicos.
