# Validação da Bolha 0.4.1

O instalador Windows x64 foi gerado a partir do commit `ddbe8d47da6aadde9b16efe1b3c2ecd44b1d86c1`.
O arquivo publicado tem 34.876.901 bytes e SHA-256
`f5fa8b5bbbd0d66190bb6199d956f9878d6bac0e0148b136faf18766e5fd7cad`. A publicação reutilizou o arquivo validado.
[Execução do CI Windows](https://github.com/kuky13/bolha/actions/runs/42099076575).

- O CI Windows aprovou 392 testes e 10 cenários do instalador,
  incluindo recuperação e atualização da 0.4.1 para a fixture 0.4.2.
- No kukybook26, o mesmo instalador passou em 10 cenários de atualização
  da 0.4.0 para a 0.4.1, em perfil isolado. Preferências, aprendizado e registro
  foram verificados. A versão nova abriu com os 470 neurônios ativos.
- No mesmo notebook, a aplicação executada a partir do código final mostrou
  duas reações do ReactionGIFs em cantos diferentes. A primeira exibiu
  12 quadros e fechou após cerca de 15 segundos. O título e a
  origem apareceram no menu de botão direito e a mídia permaneceu em RAM.
- As animações de raiva também foram verificadas em 1.024 quadros renderizados,
  com rotação e deformação no tamanho máximo.
- As migrações do Electron foram verificadas na 0.4.0. A atualização da
  0.4.1 revalidou o caminho a partir da 0.4.0. A interação com o brinquedo
  foi exercitada por entradas simuladas, incluindo 5 testes focados no kukybook26.

O instalador está sem assinatura digital. [Arquivos da versão](https://github.com/kuky13/bolha/releases/tag/v0.4.1).
