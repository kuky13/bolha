# Validação das expressões Qt 0.3.1

As **24 cenas de prévia e o amendoim** receberam aprovação para compilar e
testar a versão Windows. São 24 cenas de apresentação;
a contagem não significa 24 animações distintas nem uma gravação do pet decidindo
cada atividade. A compilação e a validação Windows da 0.3.1 ainda estão pendentes.
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

## Evidência local anterior à compilação

A suíte local completa passou com **221 testes e 11 pulados**, estes dependentes
de PowerShell/Windows. Depois foram acrescentadas quatro regressões de olhar,
sem mudança adicional na aplicação; o conjunto direcionado de cérebro e
movimento passou com **53 testes**, incluindo esses quatro novos casos. Isso
totaliza **225 casos únicos locais aprovados**, sem somar novamente os casos
repetidos entre as duas execuções. Não é uma alegação de suíte completa Windows.

Os testes usam Qt offscreen e o Game real. Cobrem pega imóvel, arrasto rápido,
queda pelo ciclo físico completo, desprendimento do notebook, perda de captura,
ocultação, emergência, fechamento, cancelamento e limpeza do hover. Também
cobrem o seletor Qt, gravação e reabertura de preferências, sensores desligados,
preservação dos corpos e do cérebro, sinais neurais, reações de brincadeira e
limites do rosto e da deformação nos casos testados. As regressões de olhar
verificam que olhar bravo e birra acompanham o ponteiro somente com o sensor ligado.

As três folhas aprovadas contêm 24 cenas calculadas pelas funções Qt da
aplicação. Cada GIF tem 72 quadros em seis segundos e menos de 5 MiB; as prévias
foram decodificadas, os hashes conferidos e quadros representativos inspecionados.
Os objetos estão em posições de composição: as folhas demonstram curvas e poses,
sem comprovar a frequência real ou a seleção autônoma das atividades.

A imagem do README permanece a captura Qt offscreen da 0.3.0. Os resultados
Windows em [VALIDATION-NATIVE.md](VALIDATION-NATIVE.md) e seus instaladores
de teste pertencem à 0.3.0; não validam esta fonte 0.3.1.

## Windows ainda pendente

- Executar os 11 casos PowerShell e a suíte completa no commit final da 0.3.1.
- Compilar uma vez o aplicativo padrão, auditar o pacote e gerar o instalador
  de teste; o workflow reutiliza esse bundle na fixture da versão seguinte.
- Validar instalação, atualização, recuperação e preservação de preferências,
  semente e aprendizado com os artefatos da nova execução.
- Conferir gestos, foco, passagem de cliques, pega nas extremidades esticadas,
  suspensão e retomada em Windows real, além de múltiplos monitores físicos.
- Medir fluidez, CPU e memória em sessão prolongada do novo instalador.

A próxima execução de CI deve fornecer artefatos e relatórios de teste com
`publish_release=false`. A aprovação visual autoriza essa validação; uma release
permanece fora desta etapa. As medidas antigas e as prévias não substituem
instalação ou uso real da 0.3.1 no Windows.
