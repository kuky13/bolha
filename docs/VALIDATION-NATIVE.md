# Validação da migração Qt 0.3.0

O aplicativo nativo já compilou e abriu em Windows x64. A publicação da versão
final permanece pendente dos testes de CI descritos abaixo. Os resultados em
`VALIDATION.md` pertencem às versões Electron e não substituem esta validação.

## Testes automatizados da fonte atual

A suíte local passou com **145 testes e 11 pulados**. Os pulados dependem de
PowerShell/Windows; os 11 casos de simulação do workflow em PowerShell foram
executados separadamente no Windows. A suíte cobre migração com backup e
idempotência, sensores preservados, falhas de gravação, manifesto, URL e
redirect, checksum, download incompleto, cache alterado, adiamento persistente,
retomada offline, recuperação e limpeza limitada aos arquivos próprios.

Os testes Qt verificam rosto sem boca, máscaras, gestos, diálogos e os desenhos
GPL do notebook e da bolinha. Uma comparação pontual de dez renderizações
canônicas conferiu os dois renderizadores com o código upstream do Pestinha,
pixel a pixel. Não foram incorporadas fotografias PNG dos objetos.

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

- Compilar e validar o pacote final com os desenhos atuais e o aviso de atualização que preserva o foco.
- Migrar de instalações reais Electron 0.1.0 e 0.2.1 para Qt no Windows isolado do CI.
- Validar monitores físicos com escalas diferentes, coordenadas negativas e conexão/desconexão de telas.
- Completar a revisão visual prolongada, cliques atravessando o fundo e foco com outros aplicativos reais.

O próximo workflow Windows inclui a validação legada antes da publicação.
O teste entre duas versões nativas já executado não comprova, por si, a
migração das versões Electron nem a qualidade visual em múltiplas telas físicas.
