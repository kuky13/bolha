# Validação dos instaladores Windows

Os drivers **não compilam, baixam ou publicam** instaladores. A execução real
exige Windows e os artefatos previamente compilados. Os testes dos helpers
podem rodar em Linux sem executar arquivos `.exe`.
Use Python 3.11 x64 para reproduzir o ambiente de validação do projeto.

## Fluxo nativo isolado

```powershell
python scripts/test_windows_native.py `
  --installer release/Bolha-Setup-0.3.0-x64.exe `
  --target-installer validation/update-feed/Bolha-Setup-0.3.1-x64.exe `
  --output validation/windows-native
```

Use o mesmo fonte para a fixture 0.3.1; ela existe apenas para testar o caminho
de atualização. A compilação pode reutilizar o bundle 0.3.0, substituindo seus
metadados de versão. A fixture não deve ser publicada como versão do produto.

O driver cria um diretório temporário exclusivo com nonce, instalação `app`
e dados `data`. Todos os instaladores recebem `/S /TEST` e `/D` como último
argumento. Todas as aplicações recebem `BOLHA_TEST=1`, diretórios explícitos de
instalação e dados, relatório, status e watchdog de 120 segundos. Nenhum processo
ou perfil existente da Bolha é utilizado. `/TEST` não escreve registro,
atalhos ou inicialização automática. O driver compara um fingerprint das
chaves específicas antes e depois, sem registrar seus valores no relatório.

Cenários:

1. Pasta estrangeira não vazia é recusada, preservando o arquivo sentinela.
2. Instalação limpa em destino já existente e vazio, abertura saudável,
   470 neurônios, CPU do processo durante uma amostra, RSS e tempos de quadros.
3. SHA 256 incorreto e conexão interrompida: erro, limpeza do parcial e
   continuidade da versão instalada.
4. Adiamento de uma hora persistido em arquivo, download validado e reinício
   offline sem nenhuma requisição ao servidor.
5. Cache alterado após download é recusado antes de executar.
6. Fixture com falha antes da abertura Qt: restauração da instalação anterior,
   inventário original, preferências e aprendizado preservados.
7. Atualização automática aguardando a contagem real de 30 segundos, nova
   versão saudável, limpeza do instalador, parciais e journal de transação.
8. Preservação de tamanho 152, quatro sensores desligados, semente 1313 e peso
   aprendido inserido no perfil sintético.

O servidor aceita somente os metadados e instalador conhecidos em
`127.0.0.1`, na porta efêmera da execução. Não aceita comandos, caminhos
arbitrários ou conexões externas. Cada espera tem timeout, de até três minutos
para instalação/atualização e 90 segundos para limpeza após a abertura saudável.

O encerramento gracioso usa somente o hook de teste:
`BOLHA_TEST_ALLOW_STOP=1` + `BOLHA_TEST_USER_DATA` explícito + arquivo
`data/test-stop.request`. O aplicativo remove esse arquivo e encerra pelo seu
fluxo normal. Não há servidor de controle ou execução de comandos. Relatórios
JSON, métricas e dados sintéticos de verificação ficam em `--output`. Por
padrão, o workspace temporário é removido após sucesso; em erro ele é retido.
`--keep-workspace` preserva uma execução bem sucedida para inspeção.

Cada lançamento remove seu relatório anterior. O relatório de encerramento só
é aceito quando versão e PID coincidem com a abertura saudável observada;
métricas da versão base ou de uma execução anterior não validam o alvo.

## Migração Electron para Qt

**Proibido no kukybook26 e em máquinas pessoais.** Execute somente em um
runner Windows GitHub hospedado e descartável, sem instalação ou perfil prévio.
As proteções exigem `GITHUB_ACTIONS=true`, `RUNNER_ENVIRONMENT=github-hosted`
e `RUNNER_OS=Windows`, além de recusar explicitamente o nome `kukybook26`.

```powershell
npm install --prefix validation/legacy-runner --no-save @playwright/test
python scripts/test_windows_native.py `
  --installer release/Bolha-Setup-0.3.0-x64.exe `
  --legacy-installer validation/legacy/Bolha-Setup-0.2.1-x64.exe `
  --playwright-root validation/legacy-runner `
  --output validation/legacy-0.2.1
```

Repita com 0.1.0 depois da limpeza própria comprovada, ou em outro job novo.
Os hashes SHA 256 dos dois instaladores antigos
estão fixados no helper e precisam conferir antes de sua execução. O perfil
`%APPDATA%/bolha` precisa estar ausente no runner. Esse fluxo reproduz a
instalação antiga real e seu registro no ambiente descartável; nunca usa
`/TEST` com instalador antigo que não conhece essa opção. O atualizador
Electron consulta o feed SHA 512 local e instala Qt pelo caminho real.

O Playwright existe somente nesse ambiente de teste para controlar o Electron
antigo. Depois da transição, o driver verifica Qt por `health.json`, relatório
e arquivos locais: 470 neurônios, backup de migração, semente, aprendizado,
sensores desligados, tamanho e retirada da camada web da instalação ativa.
O cache legado é explicitamente `LOCALAPPDATA/bolha-updater`. Nenhuma dependência
Node/npm/Playwright entra no instalador nativo.

Após sucesso, o driver espera o PID Qt realmente encerrar: o relatório é
gravado antes do fim do processo. Confere o nonce do perfil e do workspace,
recusa links/junctions, verifica o inventário nativo e o GUID/caminho exatos
no registro. Arquiva o perfil sintético como evidência, executa somente o
desinstalador nativo daquela instalação e aguarda a remoção do registro.
Só então remove o perfil criado por esse teste, permitindo executar a outra
versão antiga no mesmo runner. Qualquer falha preserva os arquivos e interrompe
o fluxo; um perfil ou registro já existente é recusado antes da instalação.
O aprendizado da versão 0.1 permanece na sua pasta original, sem renomeação,
para continuar acessível caso a instalação precise recuperar a versão antiga.

## Verificação sem Windows

```sh
python -m py_compile scripts/test_windows_native.py
node --check scripts/test_windows_legacy.mjs
python -m pytest tests/native/test_windows_driver.py -q
```

Esses checks validam sintaxe, feed, integridade, interrupção e guardas de
isolamento. **Não comprovam instalação ou atualização em Windows.** As métricas
do driver são uma amostra da execução correspondente, não validação visual,
de monitores físicos, foco, suspensão ou experiência de uso prolongado.
