# Validação 0.3.3

Este relatório reúne evidências de validação **pré-publicação** do instalador
Windows da Bolha 0.3.3, compilado no CI run `41872434530` a partir da fonte
`37a8fcabb98919314e1259c9720493d261dff238`. O binário conferido é
`Bolha-Setup-0.3.3-x64.exe` (34.821.370 bytes, SHA-256
`4d79acc0542ae92ce8a29fd1cf0449a76d978a5e24fbbe53004a3606ef7bb94d`).
Os ensaios abaixo foram feitos antes da publicação. O instalador não possui
assinatura digital.

Uma fixture homônima `0.3.3` existiu anteriormente apenas como pacote reempacotado
de metadados para exercitar a atualização `0.3.2 → fixture 0.3.3` no CI da fonte
`ddcfa90` (sem nunca ter sido publicada). A candidata **0.3.3** atual possui seu
próprio código-fonte, SHA e evidências; o pipeline de CI exercitou dinamicamente
`0.3.3 → fixture 0.3.4`, sendo a fixture `0.3.4` exclusiva do runner de teste e
**nunca entregue** como versão real.

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
    cache em disco; a animação `QMovie` é pausada quando a janela fica oculta e
    os buffers de mídia são liberados ao fechar/remover a janela ou ao desativar
    `onlineReactions` / travessuras nas configurações (requisições ainda em
    andamento sem mídia carregada são canceladas e abortadas se a janela ficar
    oculta ou em modo pânico). Falhas de rede descartam a reação silenciosamente
    sem penalizar o cérebro.
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

## Validação no CI Windows concluída

A execução manual (`workflow_dispatch`) do workflow `windows.yml` na fonte
`37a8fcabb98919314e1259c9720493d261dff238`
([run `41872434530`](https://github.com/kuky13/bolha/actions/runs/41872434530),
com `publish_release=false` e `legacy_validation=false`) foi concluída com
sucesso:

- **Etapas opcionais e compilação única**: as etapas de migração Electron
  e publicação de release permaneceram `skipped`, realizando uma única compilação PyInstaller real para a candidata
  `0.3.3` e reempacotando apenas metadados para a fixture `0.3.4`.
- **Suíte automatizada completa no Windows**: **363 testes passaram em 67,19 s**
  (incluindo os 11 testes específicos de Windows/PowerShell).
- **Auditoria do pacote e decodificador GIF (`qgif.dll`)**: o log do CI confirmou
  `gifDecoderPresent: true` para `PySide6/plugins/imageformats/qgif.dll` tanto
  na compilação `0.3.3` quanto no reempacotamento da fixture `0.3.4` (o arquivo
  final `validation/package-audit.json` do artefato registra a última execução,
  referente à fixture `0.3.4`, com `executable: "Bolha.exe"`,
  `gifDecoder: "PySide6/plugins/imageformats/qgif.dll"` e
  `gifDecoderPresent: true`).
- **Artefatos de release gerados (candidata de teste, não publicados como release)**:
  - `Bolha-Setup-0.3.3-x64.exe`: `34.821.370` bytes, SHA-256
    `4d79acc0542ae92ce8a29fd1cf0449a76d978a5e24fbbe53004a3606ef7bb94d`
  - `latest.yml`: SHA-256
    `490b80497d21d7c754efe8b8c1b47c8ff77cabfcc362ff7d580b15766f5ba18c`
  - `THIRD-PARTY-NOTICES.txt`: SHA-256
    `7925a0bb5df9b59347a4c753af020f037465854ff474659f181c36cfb69de166`
- **10 cenários nativos isolados (`scripts/test_windows_native.py`)**: todos os
  **10 cenários passaram** (`passed: true`), exercitando a atualização real
  `0.3.3 → fixture 0.3.4` (sendo a fixture `0.3.4` exclusiva de teste e nunca
  entregue):
  1. `foreign_directory_preserved` (`returncode: 2`)
  2. `clean_install_existing_empty_directory`
  3. `checksum_rejected_app_continues`
  4. `interrupted_rejected_app_continues`
  5. `one_hour_deferral_persistent`
  6. `restart_offline_uses_verified_pending`
  7. `tampered_cached_installer_rejected`
  8. `failed_target_start_restores_previous_installation` (`returncode: 2`)
  9. `automatic_30_second_update_and_cleanup` (atualizado para a fixture `0.3.4`
     com `ready: true` e `neurons: 470`)
  10. `preferences_seed_learning_and_registry_preserved` (preferências com
      sensores desligados, semente, aprendizado, contagem de 470 neurônios e registro do
      Windows intactos: `registryUnchanged: true`, `workspaceRetained: false`)
- **Métricas observadas na execução curta do CI (sem extrapolar como benchmark prolongado)**:
  no cenário `clean_install_existing_empty_directory` da `0.3.3` (janela de
  inicialização de `1,59 s`, `94` quadros e `14` ciclos neurais), o relatório
  registrou `78,4 MiB` de RSS total (`4,651 MiB` nos arrays principais do
  cérebro), intervalo de quadros `p95` de `16,0 ms` (`max 31,0 ms`), ciclo do
  cérebro `p95` de `4,74 ms` (`max 4,86 ms`) e amostra pontual de CPU de
  `28,12%` de um núcleo em apenas `1,0 s` de coleta pós-inicialização. Após a
  atualização automática para a fixture `0.3.4` (`31,06 s` de execução, `1.800`
  quadros e `283` ciclos neurais), observaram-se `81,02 MiB` de RSS total,
  quadros `p95` de `16,0 ms` e ciclo neural `p95` de `5,39 ms`. Esses números
  descrevem apenas as janelas curtas de inicialização/atualização do runner CI
  (e a amostra de CPU de 1 segundo reflete somente esse instante), não devendo
  ser apresentados como meta de economia, pico de sessão longa ou benchmark
  prolongado. Os relatórios JSON brutos do artefato de CI contêm caminhos
  temporários e PIDs do runner; por higiene e privacidade, a documentação do
  repositório registra apenas versões, contagens, hashes, URLs públicas e as
  métricas resumidas acima.

## Validação no notebook Windows físico

O mesmo instalador 0.3.3 teve tamanho e SHA-256 conferidos no notebook via
Remote Desktop Commander. Uma instalação limpa em pasta temporária exclusiva
retornou código `0`. O controlador nativo, preservado fora da aplicação,
aprovou seus **dez cenários** na atualização real **0.3.2 → 0.3.3** em
119,97 s. O teste físico usou as duas versões reais; o CI usou a fixture 0.3.4.
As instalações e dados reais do usuário foram preservados. O pacote instalado
confirmou `solutions.kuky.bolha`, versão `0.3.3`, abertura saudável e 470
neurônios, com `qgif.dll` presente (47.928 bytes, SHA-256
`dedc821fb5c443542ebf99cb3e33811d03d57fae07ed4af3ab4d254734427c06`).
Perfil, registro e foco do aplicativo anterior foram preservados; os processos
criados pelos probes encerraram pelo canal de parada isolado.

No executável empacotado, quatro ensaios de entrada nativa foram aprovados:
arremesso da personagem, soltura após parar o ponteiro, segurada contínua e
arremesso do amendoim. O ensaio de perda forçada de captura acompanhou o
ponteiro e soltou normalmente, mas não observou a condição de captura externa
que pretendia induzir; fica **inconclusivo**, sem contá-lo como aprovação desse
caso e sem repetir a entrada automaticamente.

A primeira tentativa com a 0.3.2 retornou código `2` antes de abrir o aplicativo
num fixture de caminho longo. O caminho efetivo de staging tinha 181 caracteres;
somado ao caminho relativo de licença de 116 caracteres observado no inventário
local equivalente e ao separador, chegaria a 298. O mesmo instalador 0.3.2
passou ao usar um fixture curto (estimativa equivalente de 232 caracteres).
Isso sustenta a hipótese de limite de caminho, mas sem erro Win32 específico a
causa exata permanece não comprovada. Nenhuma proteção do instalador foi
removida; apenas os diretórios do controlador externo foram encurtados.

## Limites restantes

- Perda forçada de captura no executável empacotado: ensaio inconclusivo.
- Uso manual prolongado, GIFs com rede real no Windows físico e dois monitores
  físicos continuam pendentes. As APIs e a reprodução real em RAM foram
  verificadas em Linux/Qt offscreen; o decoder GIF foi auditado no pacote Windows.
- A distribuição experimental continua sem assinatura digital.

Os históricos da [0.3.2](VALIDATION-GRAB.md) e da
[0.3.1](VALIDATION-EXPRESSIONS.md) permanecem separados.
