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

A compilação, instalação, atualização e entrada reais no Windows desta
candidata aguardam evidência própria. Os testes locais Qt offscreen verificam
as poses e as regressões automatizadas; a avaliação manual da firmeza, o uso
prolongado e os múltiplos monitores continuam pendentes. Consulte
[a validação da pega 0.3.2](VALIDATION-GRAB.md).

Os resultados anteriores permanecem no
[histórico da 0.3.1](VALIDATION-EXPRESSIONS.md), incluindo a fixture de atualização
que recebeu o número 0.3.2 sem conter esta correção. Esta candidata é preparada
para teste, sem publicação de tag ou release. A distribuição experimental
continua sem assinatura digital.
