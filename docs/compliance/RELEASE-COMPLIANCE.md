# Verificação antes de publicar

1. Resolva a tag até o commit e confira consistência com a versão declarada. Registre SHA-256 dos binários finais, da fonte correspondente e dos componentes externos anexos para cada plataforma.
2. Compare o conteúdo real dos instaladores e APKs com a lista de dependências. No Windows, considere DLLs carregadas por CPython, a roda Qt e seus plugins, OpenBLAS, runtime Microsoft, bootstrap do PyInstaller e stub/plugins NSIS. No Android, liste APKs por ABI e abra os arquivos `.imy` como arquivos ZIP, incluindo os requisitos NumPy e bibliotecas nativas.
3. Verifique que o pacote inclui a GPL, créditos de Bolha e Pestinha e avisos exigidos por cada componente. Inclua acesso local a esses avisos pelo menu Sobre. O texto da licença define o alcance dos avisos interativos e as condições da § 5(d).
4. Confirme a fonte correspondente e a forma preferida de edição das artes incluídas. Inclua scripts de compilação e instalação, dependências abrangidas, informação sobre patches e referências duráveis para os binários vindos de terceiros. O link para a branch padrão é insuficiente para identificar a fonte exata de uma release. Um checksum confirma identidade de bytes, sem demonstrar correspondência entre fonte e binário.
5. Rode a auditoria dos pacotes e os testes pertinentes. Registre quais etapas são estáticas, quais foram executadas com binários em ambiente isolado e quais requerem Windows ou Android físico. Compare hashes e inspeção de origem antes de aprovar.
6. Confirme que a build só leva os recursos públicos revisados. Se houver mídia externa, verifique os direitos sobre cada item, termos do serviço e atribuições. Verifique as regras de links de apoio na edição destinada a uma loja.
7. Preserve tags e assets existentes. Com autorização, uma errata ou um suplemento de avisos pode corrigir identificação e melhorar acesso à fonte sem trocar os binários antigos.

O workflow leve pode verificar arquivos, inventário e metadados. Uma divergência pode indicar revisão pendente, e a execução bem-sucedida não substitui a análise de arte, fontes correspondentes e arquivos nativos. [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.html).
