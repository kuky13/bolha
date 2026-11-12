# Bolha 0.4.5: física, olhar e diálogos

Alterações em revisão; o release público continua na versão 0.4.4.

## Resultado

* Bola e amendoim contornam a personagem quando uma parede impede a separação direta. A colisão deixa abertas as passagens reais entre monitores.
* Os dois olhos mantêm tamanho e altura iguais em qualquer direção de olhar. Piscadelas intencionais continuam independentes.
* Fala e pensamento têm silhuetas próprias, transição de opacidade e posição próxima à personagem, limitada à área útil. Há 78 falas locais em 11 categorias; a política do cérebro seleciona o conteúdo e pode preferir silêncio. Histórico recente limita repetições. Desligar travessuras desativa falas espontâneas.
* Notebook redesenhado com materiais, tela, teclas, dobradiças, câmera, trackpad e marcas de uso. Sua atividade visual atualiza somente enquanto está visível e trabalhando.
* O topo visível de janelas de diferentes aplicativos vira superfície. Trechos cobertos por janelas à frente são removidos. A geometria é convertida por monitor e por escala, inclusive em coordenadas negativas. Pequenos deslocamentos verticais mantêm o apoio; fechamento, minimização e grandes deslocamentos soltam o corpo.

A leitura usa somente geometria externa das janelas, sem conteúdo, títulos ou painéis internos. A preferência de leitura de janelas continua obrigatória; quando desligada, não há consulta nativa nem plataformas de aplicativos.

## Prévias reproduzíveis

![Desenho Qt real](previews/visual-polish-045.png)

![Notebook em atividade](previews/notebook-045.gif)

Gerar a prancha com `python scripts/preview_visual_polish.py DIRETORIO`.
Todas as novas artes, falas, animações e prévias seguem GPL-3.0-or-later.

## Validação automatizada

Em Linux com Qt offscreen, Python 3.11 e PySide6 6.11.3:

* Suíte completa: 637 aprovados, 11 ignorados por dependerem de Windows.
* Após acrescentar a integração de leitura Windows e definir a versão 0.4.5: 17 aprovados nos testes de plataformas, metadados e contrato da cena.
* Testes de colisão cobrem empurrões contínuos por 90 quadros, paredes e cantos, objetos segurados, desconexão, costuras físicas com DPI diferente e ausência de sobreposição dos círculos.
* Testes vetoriais cobrem proporção e alinhamento dos olhos em nove direções e 14 expressões; os testes de imagem existentes cobrem rotação, tamanho, deformação, efeitos e recorte no corpo.
* Testes de balões cobrem seleção sem repetição imediata, estado de brincadeira expirado, privacidade, silêncio, posicionamento negativo e transições.
* Testes de notebook cobrem escalas, máscara, preservação da silhueta e diferença entre atividade e repouso.
* `git diff --check` aprovado.

Validação de pacote, instalação e atualização no runner Windows: pendente nesta revisão inicial.
Validação manual em computador Windows com monitores físicos: não realizada nesta etapa. O runner e o Qt offscreen não comprovam o comportamento visual de todos os aplicativos reais.
