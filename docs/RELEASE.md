# Bolha 0.3.3

Bolha 0.3.3 para Windows x64 reúne irritação vermelha e efeitos presos ao corpo,
reação física do brinquedo à aproximação do cursor, pega firme e arremesso com
o impulso recente do mouse. GIFs e imagens online são opcionais e permanecem
em RAM durante a exibição.

## Validação

- CI Windows: **363 testes** e **10 cenários nativos**; o pacote inclui
  `qgif.dll`.
- Notebook Windows: instalação limpa e atualização real **0.3.2 → 0.3.3**;
  **10 cenários** do controlador nativo passaram.
- Quatro probes de gesto passaram: arremesso da personagem, soltura após pausa,
  segurada contínua e arremesso do amendoim. A tentativa de perda forçada de
  captura ficou **inconclusiva** e não conta como aprovação desse caso.
- Uso prolongado, GIFs com rede real no notebook e validação com dois monitores
  físicos seguem pendentes.

## Pacote

- Fonte: `37a8fcabb98919314e1259c9720493d261dff238`
- CI: [run 41872434530](https://github.com/kuky13/bolha/actions/runs/41872434530)
- Instalador `Bolha-Setup-0.3.3-x64.exe`: 34.821.370 bytes
- SHA-256: `4d79acc0542ae92ce8a29fd1cf0449a76d978a5e24fbbe53004a3606ef7bb94d`
- O instalador **não possui assinatura digital**.

Consulte [o relatório detalhado de validação](https://github.com/kuky13/bolha/blob/main/docs/VALIDATION-0.3.3.md).
