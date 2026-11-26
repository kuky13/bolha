# Reações locais e provedores opcionais

A candidata usa reações originais geradas localmente. No Windows, `LocalReactionProvider` gera a mídia em memória a partir da expressão e da atividade. `OfflineReactionFetcher` limita trabalhos em paralelo e os resultados ficam em memória. No Android, a reação local é desenhada pela interface nativa. Créditos e licença ficam disponíveis no contexto da reação. O catálogo local funciona sem conexão ou credenciais.

## Provedores históricos

| Serviço | Evidência e decisão |
|---|---|
| Nekos.best | O serviço proíbe uso comercial, coleta em massa, download/caching da mídia e re-hospedagem. A FAQ distingue cache privado de metadados e imagens, recomenda informar créditos e declara que o serviço não detém os direitos sobre as obras exibidas. Os termos exigem preservar créditos existentes. Atribuição na API não concede esses direitos. Não oferecer o serviço como fonte da distribuição da Bolha. [Termos](https://docs.nekos.best/legal/tos), [FAQ oficial](https://docs.nekos.best/getting-started/faq). |
| ReactionGIFs | O catálogo mostra trechos reconhecíveis de filmes, TV, esportes e outras produções. A auditoria não encontrou autorização comercial ou licença por item. Tratar termos de uso, limites, cache, exibição por terceiros e direitos de cada mídia como não verificados. Não integrar o catálogo à distribuição. [Catálogo](https://www.reactiongifs.com/). |

A rede pública ou sem chave informa como acessar um endpoint. A licença do software cliente e os direitos sobre a mídia são analisados individualmente. O provedor local remove a necessidade de depender desses serviços. As releases antigas continuam descritas no [histórico](HISTORICO-RELEASES.md).

## Alternativas para curadoria

| Alternativa | Uso e custo técnico | Evidência exigida |
|---|---|---|
| Arte original procedural | Mantém o tema visual, usa a infraestrutura já incluída e não ocupa armazenamento adicional significativo. A escolha atual. | Registrar autoria e licença do gerador, parâmetros e arquivos-fonte. |
| Wikimedia Commons | Catálogo de mídia com `imageinfo` e `extmetadata`. Consultar na curadoria, com possibilidade de distribuir os itens autorizados offline. | Confirmar página, revisão do arquivo, autor, atribuição, direitos de imagem e marca. [Reuso de conteúdo](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia), [MediaWiki API](https://www.mediawiki.org/wiki/API:Imageinfo). |
| Openverse | Índice útil para descoberta. A origem final do item pode ter termos e limites próprios. | Usar a página do titular como evidência e validar o item antes da inclusão. [Openverse](https://docs.openverse.org/). |
| Acervo de domínio público, stickers ou SVG/Lottie | Independente do formato, escolher arquivos com manutenção e tamanho adequados. Uma ferramenta Lottie adicionaria runtime e custo de integração. O Qt já suporta desenho vetorial. | Revisar jurisdição de domínio público, créditos e marca, licenças por arquivo e licença da biblioteca decodificadora se incluída. |

Um provedor adicional pode seguir a interface `ReactionProvider`, sem alterar a lógica da mascote. O contrato já valida origem, autoria, licença e indicação de revisão comercial nos candidatos. A validação de metadados é uma barreira técnica. A aprovação de direitos exige evidência humana. Se houver catálogo externo, incluir página de origem, versão ou hash, licenças verificadas, termos do serviço, mudanças feitas e atribuição. Começar com arte própria, CC0 ou CC BY 4.0 com atribuição cumprida. Rejeitar `NC`, `ND` e direitos desconhecidos. Avaliar o compartilhamento pela mesma licença para itens `BY-SA` e preservar créditos acessíveis no menu da reação.
