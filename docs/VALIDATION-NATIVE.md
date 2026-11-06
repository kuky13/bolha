# Validação da migração Qt 0.3.0

A [Bolha 0.3.0](https://github.com/kuky13/bolha/releases/tag/v0.3.0) foi publicada
após a compilação, a auditoria do pacote e os testes de instalação e migração
passarem no Windows. O código compilado corresponde ao commit
`dba6e185a562eebf13226b0d618b54017b29c88d`, validado na
[execução 41755479097](https://github.com/kuky13/bolha/actions/runs/41755479097).
Os resultados em `VALIDATION.md` pertencem às versões Electron e não substituem
esta validação. A distribuição continua experimental e sem assinatura digital.

## Testes automatizados da fonte atual

A suíte completa do commit publicado passou com **166 testes em 31,09 segundos
no Windows**, incluindo os 11 casos de simulação do workflow em PowerShell.
A suíte local anterior passou com 154 testes e 11 pulados por dependerem de
PowerShell/Windows; o caso adicional dos drivers também foi verificado antes
da execução final do CI. A suíte cobre migração com backup e
idempotência, sensores preservados, falhas de gravação, manifesto, URL e
redirect, checksum, download incompleto, cache alterado, adiamento persistente,
retomada offline, recuperação e limpeza limitada aos arquivos próprios. As
regressões finais também verificam a preservação do caminho de aprendizado da
0.1.0 e a recusa de confirmação saudável quando um erro interrompe o desenho.

Os testes Qt verificam rosto sem boca, máscaras, gestos, diálogos e os desenhos
GPL do notebook e da bolinha. Uma comparação pontual de dez renderizações
canônicas conferiu os dois renderizadores com o código upstream do Pestinha,
pixel a pixel. Não foram incorporadas fotografias PNG dos objetos.

## Pacote final e migrações no Windows do CI

O pacote final usa Python 3.11 e Qt/PySide6 6.11.3. A auditoria confirmou a
ausência de Electron, interface web, plugin TUIO e `Qt6Network.dll`. A fixture
0.3.1 foi criada somente para testar a atualização; ela não foi publicada.

Os dez cenários do driver NSIS passaram com o instalador final: instalação em
diretório vazio, preservação de diretório alheio, checksum inválido, download
interrompido, adiamento persistente de uma hora, retomada offline, cache
alterado, recuperação após falha de abertura, contagem real de 30 segundos e
limpeza após abertura saudável. Preferências, semente, aprendizado e registro
monitorado foram preservados. O workspace temporário foi removido ao final.

As duas migrações reais do Electron também passaram no runner descartável:

| Origem | Destino | Verificações |
|---|---|---|
| 0.1.0 | 0.3.0 nativa | 470 neurônios, preferências e sensores desligados preservados, aprendizado no caminho original, backup conferido e instalador limpo |
| 0.2.1 | 0.3.0 nativa | 470 neurônios, preferências e sensores desligados preservados, aprendizado e backup conferidos, instalador limpo |

Depois de cada migração, o driver confirmou o encerramento do processo Qt,
arquivou os dados sintéticos como evidência e removeu somente a instalação,
o perfil e o registro cuja identidade havia sido comprovada. Assim o segundo
caso começou sem herdar o perfil do primeiro. Nenhuma migração legada foi
executada no computador de uso diário.

O instalador publicado tem **34.757.375 bytes**. Seu SHA-256,
`ec875b94f1c750028b7c221307930acc1b4f3bd83445442ca203a37948e3d96c`,
confere com o manifesto e o digest da API do GitHub. O SHA-512 do `latest.yml`
também foi conferido, e o instalador baixado da release é idêntico ao artefato
do CI. Esses checks demonstram integridade entre os arquivos publicados;
não substituem uma assinatura digital.

O [resumo sanitizado](windows-native-0.3.0-summary.json) registra os resultados
sem caminhos pessoais ou do runner. As métricas coletadas na VM do GitHub são
evidência funcional dessa execução, não um benchmark do notebook do usuário.

## Fonte final no Windows real: snapshot `dba6e18`

A fonte publicada abriu no kukybook26 por **30,36 segundos**, usando perfil
novo, quatro sensores desligados e um feed de teste local sem download.
O processo terminou com código zero, saúde e relatório corresponderam ao mesmo
PID e o cérebro confirmou **470 neurônios**, sem erros. Os hashes e horários
de modificação dos arquivos reais monitorados e o registro da Bolha ficaram
inalterados. Não houve instalação ou compilação nessa verificação.

Essa amostra inclui a inicialização, sem descarte de aquecimento:

| Medida | Resultado |
|---|---|
| Memória residente total do aplicativo | 88,41 MiB |
| Intervalo entre quadros, p95 | 31,0 ms |
| Ciclo do cérebro, p95 | 41,71 ms |
| Arrays principais da rede | 4,651 MiB |

Não foi medida CPU nesse smoke. Ele não equivale a uma medição prolongada do
instalador final nem permite atribuir uma diferença de desempenho ao código:
configuração, aquecimento e carga da máquina diferem da amostra anterior.

## Evidência em Windows real: snapshot `8f752da`

Python 3.11.9 x64, Qt/PySide6 6.11.3, PyInstaller e NSIS. A compilação e a
auditoria do pacote passaram: Electron, interface web, plugin TUIO e
`Qt6Network.dll` ficaram fora do pacote. O executável confirmou interface
saudável e cérebro de **470 neurônios**, sem erros no relatório.

Após descartar os primeiros 22 segundos, a amostra de 19,59 segundos mediu:

| Medida | Resultado |
|---|---|
| Memória residente total do aplicativo | 85,26–85,35 MiB na amostra |
| Intervalo entre quadros, p95 | 16,0 ms |
| Ciclo do cérebro, p95 | 9,36 ms |
| CPU da máquina com 12 processadores lógicos | 2,01% |
| CPU equivalente a um núcleo | 24,09% |

O uso de CPU depende do contexto, da atividade neural e da carga da máquina.
Essa amostra não isola o ganho causado pelo cache de desenho. Os arrays
principais da rede usam aproximadamente 4,65 MiB; isso não representa uma
medição de RSS do cérebro isolado, pois a versão Qt usa um único processo.
As janelas observadas tinham os estilos de ferramenta e de não ativação;
nenhuma tomou o foco durante a amostra. Os hashes e horários de modificação
dos arquivos reais monitorados permaneceram iguais.

O driver NSIS em **modo isolado `/TEST`**, da versão nativa 0.3.0 para a fixture
0.3.1, passou pelos dez cenários em **111,61 segundos**:

- Diretório alheio preservado e instalação limpa em diretório vazio existente.
- Checksum inválido e download interrompido recusados, mantendo o aplicativo utilizável.
- Adiamento de uma hora persistido e retomada offline de atualização pendente já verificada.
- Instalador em cache alterado recusado.
- Falha na abertura da versão alvo recuperando a instalação anterior.
- Atualização automática após a contagem real de 30 segundos, abertura saudável e limpeza posterior do instalador/cache.
- Preferências, semente, aprendizado e registro monitorado preservados.

O diretório temporário de validação foi removido e essa limpeza foi conferida.
A instalação e os dados reais do usuário não foram substituídos pelo teste.
Um [resumo sem caminhos pessoais](windows-native-8f752d-summary.json) registra
as métricas e os dez resultados. Os relatórios completos ficam nas saídas da
sessão: `windows-steady-8f752d.json` e `windows-native-8f752d/report.json`.

Essas medições e o teste NSIS correspondem ao snapshot `8f752da`, **anterior**
aos desenhos GPL atuais dos objetos e ao ajuste de foco do aviso automático de
atualização. A imagem do README já mostra a execução Qt da fonte atual em
Linux offscreen, com três janelas reais sobre um fundo composto; ela não é
uma captura de um desktop Windows nem prova os testes de instalação.

## Validações ainda pendentes

- Validar monitores físicos com escalas diferentes, coordenadas negativas e conexão/desconexão de telas.
- Completar a revisão visual prolongada, cliques atravessando o fundo, foco e suspensão/retomada com outros aplicativos reais.
- Medir CPU, memória e tempos de quadro do instalador final em uma sessão prolongada no Windows físico, sob condições controladas.

As migrações Electron e a atualização nativa foram testadas antes da publicação.
Esses testes automatizados não comprovam a qualidade visual ou o comportamento
em múltiplas telas físicas.
