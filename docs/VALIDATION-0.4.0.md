# Bolha 0.4.0: comportamento, tamanhos e GIFs

O instalador Windows x64 da 0.4.0 foi gerado a partir do commit
`fb64b2f4660749a483e84a1952eb1f1f47c6b68f`. O arquivo tem 34.866.758 bytes e SHA-256
`784cc68dc40ca22a7e2dfb7f359fb7ec6f8ce56befe48402f8fa8bf6314b3763`. A publicação usa o mesmo arquivo validado.
[Execução de validação](https://github.com/kuky13/bolha/actions/runs/42090449128).

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

## Windows

- O primeiro pacote não abria porque a janela de cena importava o Pestinha por
  um segundo caminho. A troca para o mesmo import do motor corrigiu a abertura
  no executável. A compilação aprovada é a do commit acima.
- O CI Windows aprovou 382 testes, 10 cenários nativos de instalação,
  atualização e recuperação e as migrações da 0.1.0 e da 0.2.1. A auditoria
  confirmou a presença de `qgif.dll`.
- No notebook Windows, o executável passou por 10 cenários de atualização
  isolada da 0.3.3 para a 0.4.0. Os testes conferiram integridade do download,
  adiamento, recuperação, memória, preferências e registro.
- Com o código final executado em Qt no mesmo notebook, ReactionGIFs devolveu
  um GIF de 17 quadros. O menu mostrou título e origem. A janela
  expirou em 14.95 segundos, liberou os buffers e deixou zero
  arquivos GIF no perfil de teste.
- Uso prolongado, perda forçada de captura e dois monitores físicos não foram
  cobertos nesta validação.

O pacote tem o instalador sem assinatura digital, os metadados dos atualizadores,
checksums e o código compilado. [Arquivos da versão](https://github.com/kuky13/bolha/releases/tag/v0.4.0).
