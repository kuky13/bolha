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
com cache desativado), são descartados ao fechar ou ocultar a janela e nunca são
gravados em disco. A opção pode ser desligada nas configurações e falhas de rede
descartam a reação sem penalizar o cérebro.

O cérebro local continua com 470 neurônios. Memória, condicionamento, semente,
preferências e sensores desligados são preservados. Não há novas dependências.

Na árvore de código congelada da 0.3.3, passaram **352 testes locais** em Qt
offscreen (com **11 testes específicos de Windows pulados** no Linux), as
prévias Qt offscreen de raiva vermelha e reação dos brinquedos ao cursor, os
testes reais sem chave dos dois provedores e o ensaio em `ObjectWindow` real
observando 14 quadros animados em RAM com zero arquivos de mídia em disco. A
compilação do instalador `Bolha-Setup-0.3.3-x64.exe` (com auditoria de
`PySide6/plugins/imageformats/qgif.dll`), a suíte completa de 363 testes no CI
Windows e a validação em Windows físico correspondem à próxima etapa de
execução. Consulte [a validação da 0.3.3](VALIDATION-0.3.3.md),
[a validação da pega 0.3.2](VALIDATION-GRAB.md) e o
[histórico da 0.3.1](VALIDATION-EXPRESSIONS.md). Esta candidata é preparada para
teste, sem publicação de tag ou release. A distribuição experimental continua
sem assinatura digital.
