Bolha 0.3.3 é uma candidata de teste do [PR #2](https://github.com/kuky13/bolha/pull/2),
reunindo a irritação vermelha legível, efeitos de expressão que giram e se
achatam com o corpo, reação do amendoim e da bolinha à aproximação do cursor,
pega firme com impulso recente do mouse e reações online reais de GIFs e
imagens em memória RAM. A versão pública permanece 0.3.0.

As expressões acompanham o desenho Qt aprovado, com a personagem esférica sem
boca: irritação gradual ao segurar, reações ao soltar, carinho com corações,
sono com fechamento dos olhos, respiração e “zzz”, tontura e pequenas manias
ocasionais. Quando a Bolha fica irritada — ao ser segurada por mais tempo, pelo
estado neural `ANGRY` ou na reação após soltar — a esfera e seu halo assumem um
tom vermelho forte e visível, com pálpebras cerradas, orelhas rebaixadas e leve
tremor local, sem deslocar o centro físico da pega. Risquinhos de raiva,
corações, estrelas e “zzz” acompanham a mesma rotação e deformação (`squash`)
do corpo quando ela rola ou deita.

O amendoim continua como brinquedo padrão e a bolinha original pode ser
escolhida em Configurações → Comportamento → Brinquedo. Ambos reagem à
aproximação do ponteiro com a física do Pestinha (`push_from_cursor`), movendo-se
para o lado oposto dentro dos limites da tela e alimentando a atenção e os
sinais do cérebro quando o sensor de cursor está ligado.

Pressionar segura com oscilação limitada (até 3% de deformação e 1,5° de
rotação extra) e preserva o ponto do clique mesmo se o cursor sair da janela ou
houver perda da captura nativa enquanto o botão físico continuar pressionado.
Soltar parado libera a gravidade; soltar em movimento arremessa a Bolha ou o
brinquedo com a velocidade recente do mouse (janela de 120 ms, filtro de 4 DIP
e limite de ±2500 DIP/s com giro proporcional).

Nas travessuras de reação, o aplicativo busca GIFs e imagens reais sem chave de
API no **ReactionGIFs** (fonte principal, com verificação de relevância do termo
de humor) e usa o **Nekos.best** (categoria de anime correspondente à emoção)
como alternativa. Apenas palavras genéricas de humor em inglês são consultadas;
os bytes baixados ficam exclusivamente em memória RAM (`QBuffer`/`QMovie`/`QImage`
com cache desativado), nunca são gravados em disco, têm a animação pausada
quando a janela fica oculta e são liberados ao fechar/remover a janela ou ao
desativar as reações online nas configurações. Falhas de rede descartam a reação
sem penalizar o cérebro.

O cérebro local continua com 470 neurônios. Memória, condicionamento, semente,
preferências e sensores desligados são preservados. Não há novas dependências.

Na fonte congelada da 0.3.3 (`37a8fcabb98919314e1259c9720493d261dff238`),
passaram **352 testes locais** em Qt offscreen (11 específicos de Windows
pulados no Linux), a validação em RAM da `ObjectWindow` real (14 quadros
animados observados, zero arquivos de mídia em disco) e a execução completa no
[CI Windows (`41872434530`)](https://github.com/kuky13/bolha/actions/runs/41872434530):
**363 testes** em 67,19 s, compilação única do instalador
`Bolha-Setup-0.3.3-x64.exe` (`34.821.370` bytes, SHA-256
`4d79acc0542ae92ce8a29fd1cf0449a76d978a5e24fbbe53004a3606ef7bb94d`) com
presença confirmada de `PySide6/plugins/imageformats/qgif.dll` e aprovação nos
**10 cenários nativos** de instalação, atualização (`0.3.3 → fixture 0.3.4`,
sendo a fixture exclusiva de teste e nunca entregue) e recuperação, preservando
registro, preferências, semente e aprendizado do cérebro de 470 neurônios. No notebook Windows físico, a instalação limpa e os dez cenários do
controlador nativo passaram, incluindo a atualização isolada `0.3.2 → 0.3.3`.
Quatro ensaios de entrada nativa aprovaram a pega e a soltura na personagem e
no amendoim; a perda forçada de captura ficou inconclusiva. Uso prolongado,
GIFs com rede real no notebook e dois monitores físicos continuam pendentes. Consulte
[a validação da 0.3.3](VALIDATION-0.3.3.md),
[a validação da pega 0.3.2](VALIDATION-GRAB.md) e o
[histórico da 0.3.1](VALIDATION-EXPRESSIONS.md). Esta candidata é preparada para
teste (com o [PR #2](https://github.com/kuky13/bolha/pull/2) em rascunho), sem
publicação de tag ou release. A distribuição experimental continua sem
assinatura digital.
