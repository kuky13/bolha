# Validação da pega e impulso 0.3.2

A fonte **0.3.2** (`ddcfa901f5be5e0fda5c92c9af1aff39d8eb944c`) corrige a perda
de pega no arrasto e restaura o arremesso com impulso do mouse na personagem e
nos brinquedos no [PR #2](https://github.com/kuky13/bolha/pull/2). A versão
pública permanece **0.3.0**; esta etapa produz e valida artefatos candidatos de
teste, sem criar tag ou publicar release.

## Comportamento implementado

- **Pega firme até a soltura física**: a Bolha e o brinquedo permanecem presos
  no deslocamento exato do clique (`grab_offset`) enquanto o botão primário
  físico do mouse estiver pressionado, mesmo quando o cursor sai rapidamente da
  janela ou ocorre perda da captura nativa Win32. O estado físico do botão é
  verificado no ciclo existente de 16 ms antes da física, sem hooks globais,
  temporizador extra ou ativação da janela.
- **Arremesso em movimento e queda parada**: soltar em movimento arremessa
  tanto a **Bolha** quanto o **amendoim/bolinha** com base nas amostras dos
  últimos **120 ms**, ignorando tremores abaixo de **4 DIP**, limitando a
  velocidade em **±2500 DIP/s** e aplicando giro proporcional (`vx * 0,35`),
  como no Pestinha. Soltar parado — ou após pausa superior à janela de 120 ms —
  libera apenas a gravidade com velocidade zero.
- **Autoridade física e cancelamento limpo**: o `Game` continua sendo a única
  autoridade para a física e aciona o estímulo neural `THROW` nos arremessos. A
  inércia aérea prossegue mesmo com o passeio automático (`roaming`) desligado.
  Cancelamento explícito, ocultação, menu de contexto ou falha ao consultar o
  dispositivo descartam qualquer impulso acumulado e limpam o estado de hover.
- **Pose segura e expressões preservadas**: enquanto a Bolha é segurada, a
  oscilação visual fica limitada a **3% de deformação** e **1,5° de rotação
  extra**, sem deslocar o centro visual. O desenho sem boca aprovado e todas as
  expressões da 0.3.1 permanecem ativos.

## Fonte, testes automatizados e prévias Qt offscreen

No commit `ddcfa901f5be5e0fda5c92c9af1aff39d8eb944c`:

- **Suíte local (Linux, Qt offscreen)**: **329 testes passaram** e **11 foram
  pulados** por dependerem de Windows/PowerShell.
- **Suíte completa no CI Windows
  ([execução 41819941659](https://github.com/kuky13/bolha/actions/runs/41819941659))**:
  **340 testes passaram** em 57,75 s (incluindo os 11 testes específicos de
  Windows/PowerShell).
- **Prévias Qt offscreen da fonte `ddcfa90`**: três GIFs de 252 quadros a 30 fps
  (8,4 s cada) verificaram **9 trajetórias** calculadas pelo `Game.tick` a 60 Hz
  para a Bolha, o amendoim e a bolinha original (soltura parada, arremesso
  rápido e movimento com parada antes de soltar).

Os testes automatizados cobrem preservação do ponto de clique, continuidade da
pega após perda de captura, janela de 120 ms de amostras, filtro de tremor de
4 DIP, teto de ±2500 DIP/s, giro `vx * 0,35`, queda sem impulso após pausa ou
cancelamento, inércia aérea com passeio desligado, estímulo neural `THROW` e
limites da pose enquanto segurada.

## Instalador 0.3.2 e CI Windows

A [execução manual 41819941659](https://github.com/kuky13/bolha/actions/runs/41819941659)
(job `126540233995`) compilou e auditou a fonte `ddcfa901f5be5e0fda5c92c9af1aff39d8eb944c`
com `publish_release=false` e `legacy_validation=false` (as migrações Electron
0.1.0 e 0.2.1 foram validadas na 0.3.1 e não foram repetidas para este ajuste
de física; nenhuma release foi publicada). A execução anterior `41815614806`,
anterior ao ajuste final de impulso, foi cancelada e descartada.

| Artefato 0.3.2 | Tamanho | SHA-256 |
|---|---:|---|
| `Bolha-Setup-0.3.2-x64.exe` | 34.776.704 bytes | `51386c64f8d2f03298a285af607a94cc7848cae11e9d91a3c9529443b5f096d6` |
| `latest.yml` | 362 bytes | `6a995d66b810cf65ccffa613c55aa4d5259aff4dfb7f814020f565c8f92088b6` |
| `THIRD-PARTY-NOTICES.txt` | 1.661 bytes | `7925a0bb5df9b59347a4c753af020f037465854ff474659f181c36cfb69de166` |
| `SHA256SUMS.txt` | 262 bytes | `f6d4b35d723445bc88ed9e2cfdd40747be3cc8a9270546f53ed882ca008ccebf` |

O SHA-512 em `latest.yml`
(`AK8oEe/WxT7fNTFPLxnUf6SKgEI6B0Sz7e63DKeSYrdJheYB4GF9ykltGjY1BOBxNAw6IRo4HEnW++RN1ocxZg==`),
o tamanho (`34776704`) e a versão (`0.3.2`) foram conferidos contra o binário.
O workflow reempacotou a fixture **0.3.3** sem recompilar o aplicativo apenas
para exercitar o atualizador no runner; essa fixture não é entregue como versão.
A fixture homônima `0.3.2` usada anteriormente no
[histórico da 0.3.1](VALIDATION-EXPRESSIONS.md) continha o código `1dd7277` e
permanece separada desta candidata.

No runner Windows descartável (`Windows-10-10.0.26100-SP0`), passaram os **dez
cenários** de instalação e atualização nativa **0.3.2 → fixture 0.3.3** em
ambiente isolado (`registryUnchanged: true`):

| Cenário no CI Windows | Resultado |
|---|---|
| Preservação de diretório com arquivos de terceiros | PASS |
| Instalação limpa em diretório vazio existente (470 neurônios, RSS 77,95 MiB, quadro p95 16,0 ms, cérebro p95 5,94 ms) | PASS |
| Checksum inválido rejeitado, aplicativo continua aberto | PASS |
| Download interrompido rejeitado, aplicativo continua aberto | PASS |
| Adiamento de uma hora persistido | PASS |
| Reinício offline usa atualização pendente verificada | PASS |
| Instalador em cache adulterado rejeitado | PASS |
| Falha ao iniciar a versão nova restaura a instalação anterior | PASS |
| Atualização automática após 30 segundos e limpeza (470 neurônios, RSS 80,12 MiB, quadro p95 16,0 ms, cérebro p95 5,54 ms) | PASS |
| Preferências, semente, aprendizado e registro preservados | PASS |

## Fonte `ddcfa90` no Windows real (`SendInput`)

Em hardware Windows real (um único monitor **1920×1080 a 125%**, equivalente a
**1536×864 DIP** no Qt), a fonte `ddcfa901f5be5e0fda5c92c9af1aff39d8eb944c` foi
validada com injeção nativa `SendInput` do Windows direcionada somente às
janelas Qt temporárias do próprio ensaio, mantendo `NativeApp.tick` real e seu
`QTimer` de 16 ms ativos. **5/5 casos passaram**:

| Caso (`SendInput` real na fonte `ddcfa90`) | Amostras seguradas | Eventos `QtRelease` | Velocidade na soltura (`vx, vy, spin`) | Resultado |
|---|---:|---:|---|---|
| `rapid` — flick rápido na Bolha | 19 | 1 | `1930,275`, `-1431,193`, `675,596` | PASS |
| `quiet-release` — movimento e pausa > 200 ms | 32 | 1 | `0,0`, `0,0`, `0,0` | PASS |
| `hold` — segurar imóvel por 5 s | 324 | 1 | `0,0`, `0,0`, `0,0` | PASS |
| `peanut` — flick rápido no amendoim | 17 | 1 | `1930,275`, `-1431,193`, `675,596` | PASS |
| `outside-release` — perda de captura + subida sem `QtRelease` | 92 | 0 | `0,0`, `0,0`, `0,0` | PASS |

Notas de escopo e integridade desse ensaio:

- **Fault injection declarada**: o caso `outside-release` força `ReleaseCapture`
  de forma controlada e retém `WM_LBUTTONUP` no filtro da fixture enquanto o
  botão físico sobe via `SendInput`; o aplicativo mantém a pega enquanto o botão
  está pressionado e encerra a interação por polling quando o botão sobe, sem
  depender do evento Qt de soltura. Isso comprova o mecanismo de recuperação,
  não uma reprodução espontânea da falha relatada.
- **Fixture da fonte vs. executável instalado**: o ensaio acima executa o código
  real de `Game`, `PetWindow`, cena e `NativeApp.tick` a partir da árvore de
  código, com controlador mínimo (sem `NativeApp.__init__`, atualizador ou
  atalho global) e sensores opcionais desligados. Ele não substitui o teste do
  executável empacotado `Bolha.exe`.
- **Preservação verificada**: o perfil real do usuário, o arquivo de saúde, o
  fingerprint das chaves Bolha no registro, os arquivos versionados e a janela
  em foco permaneceram inalterados; todos os processos de teste encerraram ao
  final e as capturas usaram apenas `QWidget.grab()` dos widgets próprios.
- **Separação histórica**: um ensaio anterior no commit `c1e0f80` testou a
  continuidade após perda de captura ainda sob a regra antiga de velocidade
  zero; seus resultados são mantidos separados e não representam a física final
  de `ddcfa90`.

## Limites e pendências

- **Divergência na instalação `/TEST` e runtime empacotado pendente no notebook físico**:
  após transferir e conferir o arquivo de artefato (`34.780.137` bytes, SHA-256
  `64735d98...`) e o instalador `Bolha-Setup-0.3.2-x64.exe` (`34.776.704` bytes,
  SHA-256 `51386c64f8d2f03298a285af607a94cc7848cae11e9d91a3c9529443b5f096d6`) no
  notebook Windows físico, a tentativa de instalação isolada em modo `/TEST`
  retornou código `2` antes de criar o diretório de destino, sem saída em
  `stdout`/`stderr` e sem executar nenhum probe ou injeção de mouse. Uma segunda
  tentativa isolada via `subprocess` em Python (lista `argv`, `BOLHA_TEST=1` e
  novos diretórios de dados e instalação) também retornou código `2`, embora os
  diretórios ancestrais do caminho de teste tenham sido verificados sem
  `ReparsePoint`. A causa do código `2` no notebook permanece indeterminada e a
  sessão remota foi encerrada porque o usuário precisou sair e desligar o
  equipamento (com a instalação, o perfil e o registro reais preservados). A
  aprovação dos 10 cenários no runner do CI Windows não elimina essa divergência
  local; portanto, **nenhum teste do executável empacotado 0.3.2 (`Bolha.exe`)
  nem da atualização `0.3.1 → 0.3.2` no notebook físico é alegado**.
- **Hardware e múltiplos monitores**: os testes da fonte em Windows físico
  ocorreram em **um único monitor 1920×1080 a 125% de escala**; **dois monitores
  físicos**, escalas diferentes entre telas e transição de monitor durante o
  arrasto continuam pendentes.
- **Uso manual prolongado**: permanecem pendentes a avaliação manual prolongada
  da sensação do arremesso, botão primário invertido no Windows e medição de
  desempenho de longa duração.
