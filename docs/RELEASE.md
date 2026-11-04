Bolha 0.3.2 é uma candidata de teste do [PR #2](https://github.com/kuky13/bolha/pull/2),
com expressões, amendoim e a correção da pega. A versão pública permanece 0.3.0.

As expressões acompanham o desenho Qt aprovado, com a personagem
esférica sem boca: irritação gradual ao segurar, reações ao soltar, carinho com
corações, sono com fechamento dos olhos, respiração e “zzz”, tontura e pequenas
manias ocasionais. Corpo, olhos e orelhas giram juntos. As manias cedem às
interações, ao sono e aos painéis.

O amendoim é o brinquedo padrão; a bolinha original pode ser escolhida em
Configurações → Comportamento → Brinquedo. A escolha preserva a física e o
aprendizado. As reações de brincadeira acompanham o cérebro e os eventos do jogo.

Pressionar segura. Soltar parado libera a gravidade; soltar em movimento
arremessa a Bolha ou o brinquedo com a velocidade recente do mouse, como no
Pestinha. A força tem um limite, e parar antes de soltar elimina o impulso antigo. O clique deixou de
ser cutucada. Aproximar o ponteiro alimenta a atenção quando o sensor está
ligado; o próprio pet decide brincar, sem chute automático do mouse.

A correção da pega mantém a personagem junto do ponteiro durante o arrasto e
reconhece a soltura fora da janela. Uma perda de captura mantém a pega enquanto
o botão físico continua pressionado; cancelamentos explícitos encerram a
interação. Enquanto é segurada, a Bolha tem até 3% de deformação e 1,5° de
rotação extra, sem deslocar seu centro visual. Olhos, orelhas e risquinhos
continuam mostrando irritação gradual modulada pelo cérebro. As outras
animações e as reações após soltar mantêm o comportamento existente.

O cérebro local continua com 470 neurônios. Memória, condicionamento, semente,
preferências e sensores desligados são preservados. Não há novas dependências.

A fonte `ddcfa901f5be5e0fda5c92c9af1aff39d8eb944c` passou em 329 testes locais
Qt offscreen (com 11 específicos de Windows pulados no Linux), nas nove
trajetórias das prévias Qt offscreen e nos cinco casos reais de `SendInput` no
Windows físico (um monitor 1920×1080 a 125%), cobrindo arremesso da Bolha e do
amendoim, soltura após pausa, segurada de 5 segundos e recuperação após perda
controlada de captura sem evento Qt de soltura. No CI Windows
([execução 41819941659](https://github.com/kuky13/bolha/actions/runs/41819941659)),
passaram os 340 testes automatizados, a auditoria do instalador
`Bolha-Setup-0.3.2-x64.exe` e os dez cenários de instalação, atualização nativa
(`0.3.2 → fixture 0.3.3`) e recuperação. O teste de `SendInput` no executável
empacotado e a regressão `0.3.1 → 0.3.2` fora do CI, a avaliação manual
prolongada e a validação em dois monitores físicos continuam pendentes. Consulte
[a validação da pega 0.3.2](VALIDATION-GRAB.md).

Os resultados anteriores permanecem no
[histórico da 0.3.1](VALIDATION-EXPRESSIONS.md), incluindo a fixture de atualização
que recebeu o número 0.3.2 sem conter esta correção. Esta candidata é preparada
para teste, sem publicação de tag ou release. A distribuição experimental
continua sem assinatura digital.
