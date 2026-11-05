# Bolha 0.4.0: comportamento, tamanhos e GIFs

A candidata 0.4.0 está em validação. A versão 0.3.3 continua sendo a versão
pública enquanto o instalador e o aplicativo da 0.4.0 aguardam validação em
Windows.

## O que mudou

- O motor de 470 neurônios do Pestinha continua a calcular impulsos. O Game
  conecta esses sinais, as necessidades, as emoções e as experiências à
  seleção de objetivos, movimentos, brincadeiras, travessuras e expressões
  ocasionais. Restrições de segurança, ações diretas do usuário, física e
  reflexos continuam tendo prioridade. Desativar o comportamento adaptativo
  remove os objetivos e a influência da memória nessa política; a rede de base
  continua ativa. O aprendizado de rotina tem seu próprio controle.
- O painel desenha os pontos e rastros do cérebro ativo. Ao selecionar um
  grupo, mostra uma amostra das conexões com os maiores pesos relevantes da
  matriz real. O painel registra decisões e seus fatores quando disponíveis.
  As posições dos grupos foram rearranjadas para leitura.
- Cada tipo de objeto pode ser ajustado separadamente em Aparência, com opção
  de ajuste pelo botão direito do próprio objeto. A escala considera o tamanho
  da personagem, com mínimos para manter objetos pequenos usáveis.
- As reações online se ajustam ao espaço mantendo a proporção e aparecem sem
  moldura, rodapé ou texto. Origem e título ficam no menu de contexto. Os 15
  segundos contam enquanto a reação está visível e sem interação. GIFs e
  imagens ficam em RAM; expiração, descarte, falha e desligamento liberam a vaga
  e os buffers. O pedido manual informa se a busca falhou.
- Ao abrir pela primeira vez com dados anteriores, a versão faz um novo
  backup verificado, sem converter a semente da rede ou o formato da memória.

## Validação reproduzível

```bash
QT_QPA_PLATFORM=offscreen OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest -q
```

No Linux, com Qt offscreen, **371 testes passaram e 11 foram ignorados**.
As verificações locais cobrem a política e seus fatores, aprendizado,
preferências e migração, gestos e trajetória do brinquedo, escala e colisão,
diálogos, busca e falhas de mídia, desenho sem moldura e descarte após 15
segundos. Também foi executado um pedido real pelo fluxo Game → Qt com o painel
de configurações aberto: a resposta de ReactionGIFs animou em memória, com
quatro quadros, e a remoção da janela liberou os buffers sem criar arquivos GIF.
Essa é uma verificação em Linux, com Qt offscreen, e depende da resposta do
provedor no momento do teste.

As capturas do painel e das escalas são da própria interface Qt. A captura do
GIF usa um arquivo de demonstração gerado em memória para comparar a janela
normal e o menu do botão direito.

## Antes de publicar

Após aprovação visual, gerar um instalador Windows x64 sem assinatura.
Verificar o conteúdo do pacote, instalação, recuperação e preservação da
memória. No Windows físico, conferir menu e expiração do GIF com rede real,
fluidez dos gestos, escala, foco e atualizações. Registrar o que foi validado
no runner e o que foi validado no computador separadamente.
