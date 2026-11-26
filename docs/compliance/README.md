# Conformidade da Bolha

Auditoria técnica do fork `kuky13/bolha`, do upstream Pestinha e do site oficial. O histórico cobre os 24 tags com releases públicas retornados pela API do GitHub, de v0.1.0 a v0.5.9.2. A inspeção foi estática. Veja no histórico a distinção entre metadados da API, hashes e o conteúdo efetivamente inspecionado. Os resultados se referem às versões e aos arquivos indicados.

## Resultados e prioridades

| Prioridade | Evidência e decisão |
|---|---|
| Alta | Os avisos Windows de v0.5.9.0 e v0.5.9.2 mantêm a identificação “Bolha 0.4.4”. O instalador v0.5.9.2 contém OpenSSL 3.0.13, QtSvg, plugins de imagem, Mesa/LLVM e DLLs Microsoft. Completar avisos, mapear licenças e origem exata dos componentes redistribuídos e validar a entrega de fontes correspondentes nas próximas candidatas. |
| Alta | O Windows v0.5.9.2 incorpora CPython 3.11.9, último binário oficial da série 3.11. As atualizações posteriores dessa série são publicadas em código-fonte. Avaliar runtime mantido em um trabalho separado com regressão de instalação, atualização e compatibilidade das wheels. |
| Alta | Os avisos históricos separam artes CC BY-NC 4.0 do código GPL. Isso exige revisão arquivo a arquivo antes de reutilizar comercialmente um instalador histórico. A mudança de licença das artes próprias a partir de v0.4.4 cobre os arquivos efetivamente licenciados pelo titular. |
| Alta | Os termos do Nekos.best proíbem uso comercial e a auditoria não encontrou concessão por item no ReactionGIFs. A candidata usa um provedor local de reações. A eventual integração externa exige aprovação e evidência dos direitos sobre cada mídia. |
| Alta | A Steam ainda depende de aceitação da categoria e revisão dos contratos da Valve. O plano recomenda edição autônoma sem Steamworks SDK vinculado nem DRM, com a fonte correspondente disponível aos destinatários. |
| Média | Os binários antigos guardam avisos e nomes associados à Drippy. As ocorrências de texto, sozinhas, não demonstram que guias de referência privados foram incluídos. Preservar referências técnicas necessárias à migração e verificar procedência de cada arte. |
| Média | Confirmar quais binários e scripts correspondem a cada tag, incluindo os runtimes dentro dos APKs. A falta de um anexo `*-fonte.zip` não demonstra por si só ausência de fonte correspondente. O acesso via tag pode cumprir parte da obrigação quando contém as fontes exatas e as instruções requeridas. |
| Baixa | A presença de `LicenseRef-Qt-Commercial.txt` nas wheels indica que o fornecedor oferece uma opção comercial. Especificar qual opção foi adotada no pacote. A presença do texto e a ausência de Authenticode não são violações de licença por si sós. |

As divergências de cabeçalhos, licenças declaradas e componentes presentes são achados técnicos confirmáveis. A auditoria não estabeleceu uma violação jurídica por essas divergências isoladamente. Uma aplicação GPL-3.0-only pode incorporar código GPL-3.0-or-later pela opção de GPLv3, respeitados os avisos e as demais obrigações. No caso das artes históricas, é necessário confirmar direitos comerciais e se são obras independentes em uma agregação ou parte de uma obra combinada. [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.html), [FAQ GNU](https://www.gnu.org/licenses/gpl-faq.html), [CPython Windows](https://www.python.org/downloads/release/python-31117/).

## Documentos

- [Matriz de conformidade](MATRIZ-CONFORMIDADE.md) e [inventário de procedência](INVENTARIO-PROCEDENCIA.md)
- [Histórico das releases e inspeção](HISTORICO-RELEASES.md)
- [Reações locais e política para provedores externos](PROJETO-REACOES.md)
- [Procedimento para a próxima distribuição](RELEASE-COMPLIANCE.md) e [validação da candidata](VALIDACAO-CANDIDATA.md)
- [Preparação para a Steam](PREPARACAO-STEAM.md) e [financiamento e INPI](MONETIZACAO-INPI.md)
- [Política de marca](POLITICA-MARCA.md) e [DCO](DCO-E-CONTRIBUICOES.md)

## Decisões externas

O mantenedor precisa aprovar retificações ou alterações em releases existentes. Parecer especializado pode esclarecer autorização de redistribuição de runtimes Windows, licenças históricas de artes, busca de anterioridade no INPI e enquadramento fiscal. A Valve precisa confirmar a categoria e os termos da edição. O registro de marca, o envio a lojas e alterações no GitHub ficam sujeitos à autorização do mantenedor.
