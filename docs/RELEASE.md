# Bolha 0.4.0

A Bolha exibe GIFs sem moldura, legenda ou rodapé. A reação desaparece após
15 segundos de exibição sem interação. Título e origem aparecem no botão
direito, e o arquivo fica em RAM.

- O painel neural mostra os 470 neurônios, as conexões do grupo selecionado e
  os fatores da decisão.
- A personagem, o brinquedo, o notebook e os demais tipos de objeto têm
  controles de tamanho separados.
- Os sinais do Pestinha, as necessidades e a memória orientam as ações
  voluntárias. O comando “Vamos brincar” move o brinquedo quando aceito.

## Validação

O CI Windows aprovou **382 testes**, **10 cenários nativos** e as migrações
da 0.1.0 e da 0.2.1. No notebook Windows, a atualização **0.3.3 → 0.4.0**
passou por 10 cenários em um perfil isolado. O teste de GIF nesse notebook
usou a aplicação executada a partir do código, com rede real.
[Execução de validação](https://github.com/kuky13/bolha/actions/runs/42090449128).

O instalador Windows x64 não tem assinatura digital. O SHA-256 do arquivo
`Bolha-Setup-0.4.0-x64.exe` é `784cc68dc40ca22a7e2dfb7f359fb7ec6f8ce56befe48402f8fa8bf6314b3763`.
