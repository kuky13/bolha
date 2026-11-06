# Validação das expressões Qt 0.3.1

As **24 cenas de prévia e o amendoim** receberam aprovação para compilar e
testar a versão Windows. São 24 cenas de apresentação;
a contagem não significa 24 animações distintas nem uma gravação do pet decidindo
cada atividade. O instalador de teste foi compilado e validado no CI Windows.
Esta etapa não publica uma release.

## Comportamento aprovado

- A personagem continua esférica e sem boca. Corpo, olhos e orelhas compartilham
  a transformação; a deformação é visual e a região física de pega continua circular.
- Segurar irrita aos poucos; as reações ao soltar respondem aos motores neurais
  e ao condicionamento. Carinho tem prioridade sobre a reação de soltura.
- O sono fecha os olhos gradualmente, respira e apresenta “zzz”. Carinho,
  tontura e irritação têm efeitos visuais próprios.
- Espreguiçada, espirro, soluço, cochilo, piscadela e movimentos de orelhas
  aparecem ocasionalmente, com pausas e sem repetir a mesma mania em sequência.
  As manias não interrompem a pega, o sono nem os painéis.
- Preparação e erro do bote, susto com o brinquedo, comemoração, distração no
  notebook, birra e sacudida acompanham o estado neural e os eventos do jogo.
- O amendoim é o brinquedo padrão; o seletor permite a bolinha original sem
  trocar o corpo físico nem apagar aprendizado.
- Pressionar segura e soltar libera a gravidade na personagem e no brinquedo,
  sem impulso ou velocidade herdada do mouse, mesmo com arrasto rápido.
- Proximidade do ponteiro alimenta atenção e motores respeitando o sensor
  desligado e o intervalo entre estímulos. O mouse não chuta automaticamente;
  o pet continua podendo brincar por decisão própria.

O cérebro conserva os **470 neurônios**, a semente e os formatos de memória e
condicionamento. Não foram adicionadas dependências nem um novo temporizador
para as expressões. O Game continua sendo a única autoridade para a física.

## Fonte e testes automatizados

O código compilado corresponde ao commit
`1dd7277d49949bc014e3457569e3540becf50732`, aprovado na
[execução Windows 41763057623](https://github.com/kuky13/bolha/actions/runs/41763057623).
A suíte completa passou com **237 testes no Windows**. No Linux, passaram
**226 testes e 11 foram pulados** por dependerem de PowerShell/Windows; esses
11 casos também passaram no CI. A fonte inclui a correção do hover ao cancelar
a pega da personagem, evitando que o estado antigo mantenha o pet parado.

Os testes usam Qt offscreen e o Game real. Cobrem pega imóvel, arrasto rápido,
queda pelo ciclo físico completo, desprendimento do notebook, perda de captura,
ocultação, emergência, fechamento, cancelamento e limpeza do hover. Também
cobrem o seletor Qt, gravação e reabertura de preferências, sensores desligados,
preservação dos corpos e do cérebro, sinais neurais, reações de brincadeira e
limites do rosto e da deformação nos casos testados. As regressões de olhar
verificam que olhar bravo e birra acompanham o ponteiro somente com o sensor ligado.

## Instalador de teste e CI Windows

O workflow compilou e auditou o aplicativo padrão uma vez e reutilizou seu
bundle para a fixture **0.3.2**, exclusiva dos testes de atualização. Passaram
a instalação nativa e a atualização **0.3.1 → fixture 0.3.2**, além das migrações
reais **Electron 0.1.0 → 0.3.1** e **Electron 0.2.1 → 0.3.1** no runner
descartável. Esses resultados pertencem aos artefatos da execução citada.

O instalador de teste `Bolha-Setup-0.3.1-x64.exe` tem **34.780.199 bytes** e
SHA-256 `8aa32617bc7a1638a25dfab87bc88ae7129918a12af93aae881a4807aa96cd1a`.
O checksum e o SHA-512 de `latest.yml` foram conferidos. O workflow executou com
`publish_release=false`; nenhuma release foi publicada nesta etapa.

## Atualização real 0.3.0 → 0.3.1

O instalador NSIS passou pelos **dez cenários** no Windows físico, em diretórios
e perfil de teste isolados. O relatório do ensaio e seu wrapper passaram:

| Cenário | Resultado |
|---|---|
| Preservação de diretório com arquivos de terceiros | PASS |
| Instalação limpa em diretório vazio existente | PASS |
| Checksum inválido rejeitado, aplicativo continua aberto | PASS |
| Download interrompido rejeitado, aplicativo continua aberto | PASS |
| Adiamento de uma hora persistido | PASS |
| Reinício offline usa atualização pendente verificada | PASS |
| Instalador em cache adulterado rejeitado | PASS |
| Falha ao iniciar a versão nova restaura a instalação anterior | PASS |
| Atualização automática após 30 segundos e limpeza | PASS |
| Preferências, semente, aprendizado e registro preservados | PASS |

A primeira tentativa terminou com `PermissionError: [WinError 5] Acesso negado`
na fase de encerramento da instância-base do cenário de checksum. A causa não
foi estabelecida de forma conclusiva. A segunda tentativa passou nos dez
cenários, sem alteração no aplicativo entre as tentativas.

As comparações antes/depois dos três ensaios — fonte, atualização nativa e
pacote instalado — confirmaram perfil real e registro monitorado inalterados.

## Fonte no Windows real

A mesma fonte passou em **nove grupos de ensaio dirigido**, com perfil de teste
e os sensores desligados: abertura saudável com 470 neurônios, queda da personagem
e do brinquedo no primeiro quadro físico sem impulso do mouse, irritação neural
e carinho, retomada da transição de sono após segurar, “zzz” somente ao dormir,
seletor amendoim/bolinha persistido, limites visuais/máscaras e coleta de métricas.
O perfil real e o registro monitorado permaneceram inalterados.

O driver enviou os gestos por `QApplication.sendEvent` somente aos widgets
do ensaio, sem injeção global de mouse ou teclado. Na fixture final, o driver
registrou e consumiu eventos espontâneos de mouse recebidos por esses widgets.
Em duas tentativas anteriores, eventos GUI recebidos pela fixture interferiram
no teste de sono. A contraprova confirmou que segurar e soltar reinicia a
transição conforme previsto; o ensaio final passou com a entrada isolada, sem
alteração no aplicativo.

A checagem nativa de entrada confirmou que
o corpo recebe a janela da personagem, o fundo transparente recebe a janela
de teste atrás dela, as duas janelas da Bolha têm estilo de não ativação e a
janela visual deixa a entrada passar. O aplicativo não tomou o foco nessa
checagem. São ensaios automatizados em Windows físico, separados da revisão
manual prolongada e do uso com múltiplos monitores.

As sete capturas do próprio aplicativo tiveram seus hashes conferidos; elas
documentam os estados do ensaio, sem comprovar uma sessão manual prolongada.

Uma execução separada pela entrada normal da fonte, com BLAS limitado a uma
thread, mediu **45,23 segundos** com sensores, passeio, travessuras e aprendizado
adaptativo desligados:

| Medida | Resultado |
|---|---|
| RSS total do aplicativo | 86,95–87,91 MiB; média de 87,77 MiB |
| CPU equivalente a um núcleo | 46,46% |
| Intervalo entre quadros, p95 | 31 ms |
| Ciclo do cérebro, p95 | 27,43 ms |
| Arrays principais da rede | 4,651 MiB |

Houve sobreposição com o download do instalador. Os p95 usam janelas móveis do
aplicativo que incluem o final da amostra de CPU/RSS, sem limitar todos os dados
ao mesmo intervalo. Esses números descrevem essa execução da fonte; não são
benchmark controlado, medição do pacote instalado nem sessão prolongada.

## Amostra do pacote instalado

O pacote 0.3.1 instalado passou em uma execução separada pela entrada normal,
com identidade do processo e executável conferidas. O inventário do pacote foi
verificado; o SHA-256 de seu executável é
`4c6db9394a7e162c27dbc2287a10abf00ce15faa1f740ec40f7a2cf8e22c9656`.
O processo do ensaio encerrou, e o perfil real e o registro permaneceram
inalterados nos relatórios.

A amostra durou **45,125 segundos**, em sequência com os outros ensaios, com
BLAS limitado a uma thread, avatar de 136, escala de tela de 1,25 e 470
neurônios. Sensores, passeio, travessuras, comportamento adaptativo e aprendizado
de rotina estavam desligados; o brinquedo escolhido era o amendoim.

| Medida | Resultado |
|---|---|
| RSS total do aplicativo | 79,04–79,45 MiB; média de 79,33 MiB |
| CPU equivalente a um núcleo | 44,43% |
| Intervalo entre quadros, p95 | 31 ms |
| Ciclo do cérebro, p95 | 29,08 ms |
| Arrays principais da rede | 4,651 MiB |

Os p95 vêm das janelas móveis do aplicativo — últimos 1.800 quadros e 600
ciclos do cérebro — e incluem o final do intervalo de CPU/RSS. Esta amostra
curta do pacote e a amostra da fonte têm condições distintas; não constituem
comparação controlada nem validam desempenho prolongado.

O [resumo sanitizado](windows-expressions-0.3.1-summary.json) contém somente
identidade pública do código/artefato, resultados e métricas permitidos.
Relatórios brutos com caminhos pessoais, PIDs e diagnósticos não entram no repositório.

## Prévias e limites

As três folhas aprovadas contêm 24 cenas calculadas pelas funções Qt da
aplicação. Cada GIF tem 72 quadros em seis segundos e menos de 5 MiB; as prévias
foram decodificadas, os hashes conferidos e quadros representativos inspecionados.
Os objetos estão em posições de composição: as folhas demonstram curvas e poses,
sem comprovar a frequência real ou a seleção autônoma das atividades.

A imagem do README permanece a captura Qt offscreen da 0.3.0. Os resultados
Windows em [VALIDATION-NATIVE.md](VALIDATION-NATIVE.md) e seus instaladores
de teste pertencem à 0.3.0; não validam esta fonte 0.3.1.

## Ainda pendente

- Completar a revisão manual prolongada de gestos, foco, passagem de cliques,
  pega nas extremidades esticadas, suspensão e retomada com outros aplicativos.
- Validar múltiplos monitores físicos, escalas diferentes e conexão/desconexão
  de telas, além de medir desempenho em sessões prolongadas controladas.

O CI, os ensaios dirigidos e a amostra do pacote não encerram essas pendências. A versão
permanece um artefato de teste, sem release publicada nesta fase.
