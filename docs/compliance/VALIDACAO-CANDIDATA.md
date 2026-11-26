# Validação da candidata de conformidade

A candidata parte do commit `2a51e7f` da Bolha. O site parte de `f5d440b`. O número 0.5.9.2 identifica a base usada nos ensaios. Os artefatos gerados nesta etapa ficam fora das releases públicas. A branch de relatos privados e os arquivos da auditoria original foram preservados.

## Implementação

- `bolha/reactions.py`, `bolha/scene.py` e a ponte Android passam a produzir e mostrar reações próprias em RAM. Os provedores de rede foram retirados. O menu do GIF mostra origem, autoria e licença. Preferências anteriores continuam aceitas e o opt-out permanece ativo.
- `bolha/dialogs.py` e `CentralActivity.java` apresentam a aba Sobre, com leitura local de avisos e política de privacidade. O apoio BotaPix abre no navegador por ação do usuário. O README, o site e o aplicativo Android identificam o APK como alfa, ainda sem teste completo.
- `NOTICE.md`, `AUTHORS.md`, `REUSE.toml`, `LICENSES/` e `docs/compliance/` documentam autoria, atribuições, procedência, histórico, marca, contribuições, doações e Steam.
- Os fluxos Windows, Android e de conformidade verificam componentes e avisos, geram SBOM CycloneDX e conferem hashes. A publicação Windows usa um job separado da compilação. O workflow Android mantém a chave oficial restrita à candidata solicitada manualmente e produz essa variante sem depuração.
- O site conserva os arquivos de download e o formulário de suporte existentes. A reprodução dos PNGs promocionais a partir da tag v0.5.9.0 foi idêntica byte a byte.

## Verificações executadas

| Verificação | Resultado |
|---|---|
| Histórico | 24 releases, 24 instaladores Windows, 8 APKs e 5 ZIPs de fonte listados ou inspecionados estaticamente. 139 arquivos locais conferiram com o digest da API. Em 15 entradas auxiliares sem cópia nessas pastas, consta o digest da API. |
| Windows no kukybook26 | 32 testes de reações e diálogo passaram na segunda compilação. Os 14 casos do PowerShell, com GitHub simulado, também passaram. A compilação NSIS passou em modo estrito e gerou 6 entradas SHA-256. O instalador retornou zero em modo silencioso com pasta e perfil temporários. O executável instalado iniciou com 470 neurônios. Os avisos locais, incluindo a licença LLVM 3.6.2 e a política de privacidade, estavam presentes. |
| Linux | A suíte completa passou com 849 aprovados, 14 ignorados e zero falhas. Os testes adicionados ao final passaram em execuções dirigidas, incluindo a rejeição de licença não aprovada e a leitura local de avisos. O teste de concorrência usa um sinal para confirmar que a interface não aguarda a geração do GIF. |
| Licenças e CI | REUSE 3.3 reconheceu dados de licença e copyright nos 329 arquivos verificados. Actionlint e validadores do repositório Windows e Android passaram. Foram gerados inventários CycloneDX das duas plataformas e um SBOM do instalador testado. |
| Site | Chrome em 390 e 1280 px validou navegação, aviso associado ao botão Android, fonte, brinquedo, notebook e link BotaPix. Foi verificada a prévia HTML offline com os avisos da fonte. |
| Android | Gradle 8.14.3 e SDK 35 compilaram a candidata release sem assinatura, incluindo lintVital (58 tarefas). Os testes Java de movimento e vibração passaram. A inspeção confirmou versão 0.5.9.2, código 5009002, manifesto sem depuração, ARM64 e x86_64, alinhamento ZIP de 16 KiB, 88 ELF por ABI, avisos locais e SBOM de 13 componentes. O ensaio em aparelho físico e a migração com a chave oficial permanecem pendentes. |

SHA-256 da candidata Windows: `2d82d16ec1531df76099eb85072a4448cf739ee8dffcced78e0f4044eaa7530f`.
SHA-256 do APK de auditoria sem assinatura: `06f4bcf5fbe10311d5ee9d88f9ce2b7467868039507e06a37f094a85a59b1c03`.

Na primeira reprodução das falhas herdadas, um teste Android abriu uma sessão temporária porque ainda pressupunha que as reações viessem desligadas. A asserção interrompeu a limpeza e a sessão bloqueou gravações dos testes seguintes. O teste agora configura a preferência que deseja verificar e encerra a sessão no teardown. O teste de mídia decodifica todos os quadros por dois ciclos e confirma a transparência e os créditos.

## Desempenho medido no Windows

Teste curto no kukybook26, Qt offscreen, com dois ensaios por cenário, 2 s de aquecimento e 5 s de coleta em perfil temporário. CPU em porcentagem de um núcleo. RSS cobre o processo inteiro. O p95 de quadro é o intervalo entre ciclos de renderização.

| Cenário | CPU base → candidata | RSS base → candidata | Quadro p95 base → candidata | Cérebro p95 base → candidata |
|---|---:|---:|---:|---:|
| Repouso | 47,97% → 45,61% | 84,02 → 82,74 MiB | 23,5 → 23,5 ms | 18,38 → 24,05 ms |
| Brinquedo e carinho | 50,78% → 48,75% | 83,39 → 82,59 MiB | 23,5 → 24,0 ms | 27,93 → 33,75 ms |

A memória e o intervalo dos quadros ficaram próximos da referência. O tempo do cérebro subiu nessas amostras curtas, sem alteração no código do cérebro. A medição no Linux registrou variação grande em uma VPS compartilhada. Quatro GIFs com cache frio levaram 546 ms no total para serem gerados nesse notebook, com 5,7 a 6,5 kB por arquivo. A geração roda em segundo plano. Estes números merecem confirmação em um ensaio mais longo, com a interface em tela e a animação rodando.

## Pendências para distribuição

- **Crítica, se houver distribuição comercial:** confirmar as permissões efetivas de cada ativo histórico reutilizado e a disponibilidade de fontes correspondentes, inclusive dos componentes GPL redistribuídos. A compatibilidade com as condições da Steam e a elegibilidade da categoria dependem da Valve.
- **Alta:** validar o APK candidato com a chave oficial, migração a partir da versão pública e uso em Android físico. Atualizar os runtimes Windows dentro de uma rodada dedicada de testes de dependências e atualização. O binário público usa CPython 3.11.9 e OpenSSL 3.0.13. Há correções de segurança posteriores, e a inspeção não estabeleceu o alcance de cada falha na Bolha. [CPython](https://www.python.org/downloads/release/python-31117/), [OpenSSL](https://openssl-library.org/news/vulnerabilities/).
- **Média:** concluir a correspondência de todos os binários de terceiros com as fontes e os patches das builds. Preparar possíveis erratas em releases antigas para aprovação.
- **Baixa:** decidir sobre registro de marca e canais adicionais de apoio. O site e os créditos da candidata identificam o projeto original e o mantenedor da Bolha.
