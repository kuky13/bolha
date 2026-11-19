# Revisão da Bolha 0.5.4

Estado: implementação local em validação, sem publicação. A aplicação é usada por
uma pessoa por perfil. A revisão partiu da árvore da versão 0.5.3.

## Bugs confirmados e corrigidos

| Prioridade | Caso que falhava | Correção e verificação |
| --- | --- | --- |
| Alta | Na foto enviada, a placa pequena mostrava apenas parte de “OLHA A BOLINHA QUE ACHEI”. | Medição e desenho usam a mesma fonte e quebra de linhas. Placas e bilhetes ganham altura antes do desenho; textos maiores que a tela são paginados por linhas inteiras. Testes em 100%, 125%, 150% e 200%. |
| Alta | A raiva desaparecia no primeiro quadro de voo após soltar a personagem. | Irritação acompanha os motores neurais e a reação aprendida. Olhos, orelhas, pálpebras, boca e rubor interpolam durante queda e pouso. O carinho acelera a recuperação. Testes em −90°, 0° e 180°. |
| Alta | O ponteiro parado podia deixar a mastigação repetindo indefinidamente. | Duas mastigadas em 0,8 segundo e cuspe automático. Mover, clicar, cancelar ou esconder continua restaurando o ponteiro. Olhos abertos, simétricos e sem sorriso enviesado. |
| Alta | A revolução podia lançar com a Central aberta, sem controles próprios, e acumular até 40 objetos por 10 segundos. | Interruptor próprio, pausa durante painel, arrasto, sono, estouro, pingue-pongue e emergência. Até seis projéteis, cinco segundos de vida e intervalo mínimo de 0,6 segundo; a política neural continua escolhendo os lançamentos. |
| Alta | O Android recebia projéteis no estado, mas não os desenhava. | Renderização vetorial nas duas interfaces, com passagem dos toques/cliques. Os projéteis são separados do brinquedo principal. |
| Média | O cartaz da revolução era desenhado como um balão e não acompanhava a rotação do corpo. | Placa com haste, presa ao corpo, trocando de lado quando falta espaço. Limites incluem a placa girada e a haste. |
| Média | Algumas atividades só podiam ser escondidas; não tinham um controle persistente para interrompê-las. | Dez interruptores individuais, agrupados em seções recolhíveis. Desativar interrompe a atividade atual e preserva a memória. Sensores desligados permanecem desligados. |
| Média | A área de testes mostrava poses isoladas, sem executar o comportamento completo. | Dezoito ensaios na Bolha real, com instruções e passos. O jogo original é pausado e o teste usa uma cópia descartável do perfil, sem enviar gravações para a fila real. |
| Média | A integração dos ensaios podia restaurar o painel Android como aberto ou recuperar limites antigos após girar o celular. | Estado de painel propagado ao jogo pausado e limites atualizados na restauração. Confirmação por identificador de pedido evita tratar uma resposta antiga como início do novo teste. |

Durante a revisão foi detectada e corrigida uma regressão da nova placa: uma
placa avulsa era anexada ao controlador errado, produzindo uma janela muito
larga. O teste existente de monitor com coordenadas negativas cobre esse caso.

## Código removido

Busca em código, testes, scripts, documentação e referências dinâmicas confirmou
a ausência de consumidores para estes elementos:

- `Play.paper_due`, `next_paper`, `PAPER_EVERY` e `INTERVALO_PAPEL`: temporizador antigo, substituído pela decisão neural da revolução.
- Argumento `sprite` de `Ball` e do controlador da revolução: recebido sem uso pelo desenho vetorial.
- `PERMISSION_GROUPS`, `permissoes_validas`, `load_permissions` e `save_permissions`: metadados e persistência da antiga tela inicial, substituídos pelas preferências da Bolha.
- `config.random_photo`: helper sem chamadas.
- Segundo ramo `bravo` em `animation_pose`: inalcançável porque o mesmo caso já era atendido antes.

Permanecem os adaptadores `Item.update` e `Item.raise_`, o tipo `FlagThing`, as
constantes de permissões usadas pelo motor, os formatos de memória e as duas
entradas de execução. O `pass` desses adaptadores não provava código morto.
Nenhuma dependência foi adicionada ou removida nesta revisão.

Há ainda uma rota herdada de fotos no motor de travessuras, desligada por
`fotos=False` no Game. Não foi removida junto dos helpers: ela tem chamadas
internas e exige uma alteração separada do catálogo para ser excluída com segurança.

## Ensaios e preservação de dados

A Central permite testar carinho, segurar/soltar, arremesso, sono, brinquedo,
perseguição, embaixadinhas, pingue-pongue, notebook, protesto, cartaz, revolução,
fogos, fala, bilhete, GIF, estouro e brincadeira do ponteiro. A última é exclusiva
do computador; as instruções dos demais ensaios são adaptadas ao toque no Android.

Função ou sensor desligado produz uma explicação, sem ser ativado pelo teste.
GIFs só podem ser testados se as reações online já estiverem permitidas.
Parar, fechar ou falhar restaura a cena e o gravador originais. Testes comparam os
arquivos de aprendizado antes e depois byte por byte e verificam o descarte do
perfil temporário. A troca de brinquedo no teste da revolução e no menu do brinquedo afeta somente a cópia. Abrir a Central do Android encerra o ensaio antes de permitir alterações persistentes de configurações.

Os controles de instalação, atualização e reinicialização de aprendizado
continuam com suas verificações próprias. Os ensaios de brincadeiras não executam
operações destrutivas nem instalam uma atualização para simular um teste.

## Validação e limites

- Base 0.5.3: 740 testes passaram, 12 ignorados.
- Bateria geral desta implementação: 801 testes passaram, 12 ignorados, em 84,40 segundos.
- Testes focados adicionais cobrem confirmação assíncrona, fechamento do painel e restauração após rotação no Android. As últimas correções de reativação de placa e direção neural dos projéteis passaram em 22 testes focados.
- Desenho real Qt fora da tela: placas pequenas, cantos, rotação, irritação e mastigação; sem substituir por imagens geradas.
- Verificações de atualização, persistência, privacidade, física, GIFs e metadados existentes integram a bateria geral.
- `git diff --check` sem erros.

O kukybook26 estava offline durante a verificação. Não houve teste manual em
monitores físicos, instalação/atualização desta versão no Windows, compilação
Java/APK ou execução desta versão no Android. O ambiente local não tem Android
SDK. Os testes da ponte Python não substituem esses testes nativos. As verificações
ignoradas específicas de plataforma permanecem pendentes.

Nenhum workflow do GitHub foi iniciado. A compilação dos instaladores, os testes
nativos e a publicação dependem da aprovação das prévias, conforme combinado.

## Medição limitada de desempenho

Ensaio sintético em Linux, 900 passos a 60 Hz, NumPy e modelo/expressões Python,
sem desenhar Qt. Mesma máquina e semente, dois processos separados. Na revolução,
a decisão foi forçada para estressar o limite de objetos; não representa a
frequência normal decidida pelo cérebro.

| Cenário | 0.5.3: p95 do passo | 0.5.4: p95 do passo | Máximo de projéteis antes → depois |
| --- | --- | --- | --- |
| Repouso | 6,857 ms | 7,135 ms | 0 → 0 |
| Revolução forçada | 7,714 ms | 6,945 ms | 40 → 6 |

O RSS desses processos ficou entre 40,06 e 45,87 MiB. Isso não é a memória total
da interface nem uma medição no Windows. Uma execução curta não sustenta promessa
de melhoria geral de CPU ou fluidez: o repouso ficou ligeiramente mais lento
neste ensaio. A redução comprovada é o limite de objetos e seu tempo de vida.
CPU, RSS total e tempo dos quadros com desenho devem ser medidos no Windows.

## Licença e publicação

Código, artes e animações continuam GPL-3.0-or-later, com créditos ao Pestinha,
a mille-okws e aos contribuidores em `NOTICE.md`. Esta alteração não contém guias
privados de referência da Drippy. Nenhum serviço da OneDrip foi acrescentado.

As prévias e o diff acompanham a entrega para revisão antes da compilação e da
publicação da versão 0.5.4.
