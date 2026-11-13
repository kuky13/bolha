# Validação da Bolha 0.5.0

## Escopo

Android com expressões compartilhadas, central, painel neural real, arrasto em
coordenadas lógicas, sensores opcionais e mídia em RAM. PC com boca expressiva
e brincadeira do ponteiro escolhida pela política neural, com feedback e memória.

## Verificado localmente

- Linux, Python 3.11, Qt/PySide6 6.11.3: suíte completa com 700 testes aprovados
  e 11 verificações exclusivas de Windows ignoradas. Ajustes posteriores de
  interface neural e ciclo de vida também passaram nos testes focados.
- Sete testes do bridge Android: preferências e escala após rotação/reabertura,
  arremesso em dp, sensor opcional sem soltar o objeto segurado, 470 neurônios
  e pesos reais, prévias sem alterar a emoção, falha de mídia sem penalizar
  aprendizado e soltura segura ao suspender.
- Python 3.13 com NumPy 2.3.2: bridge, rede, persistência e movimento executados
  com bloqueio explícito a importações Qt. Não há Qt no runtime Android.
- Testes Java de cadência de vibração, coordenadas/velocidade do dedo e
  detecção de chacoalhar aprovados. Compilação integrada do APK concluída.
- Prévia PNG e GIF produzidas pelo renderer Qt real, sem geração ilustrativa.

## Validação dos pacotes

O [workflow Windows 43413057303](https://github.com/kuky13/bolha/actions/runs/43413057303)
terminou com sucesso: suíte, assistente de pasta, reinstalação, atualização,
recuperação, métricas e migrações da versão nativa anterior e das versões
Electron 0.1.0 e 0.2.1. O aplicativo Windows foi compilado no commit `67aa708`;
as correções posteriores até esta revisão afetam somente o Android e este relatório.

A primeira execução do emulador encontrou o pacote `bolha` ausente: o Gradle
não havia executado o produtor dos fontes compartilhados em um ambiente limpo.
A dependência foi corrigida e uma compilação limpa executou as 47 tarefas com
sucesso. Uma nova guarda verifica os oito módulos necessários e as bibliotecas
ELF antes de iniciar o emulador. Os 88 ELF ARM64, incluindo CPython e NumPy,
atendem ao alinhamento de 16 KiB. Cinco casos sintéticos da guarda passaram.

O novo teste do emulador continua pendente. A candidata ainda não é uma release
estável publicada.

O pipeline Windows verifica instalador, atualização, adiamento, recuperação,
migração da versão nativa anterior e das versões Electron 0.1.0 e 0.2.1.
O Android verifica a chave preservada, atualização de APK sem apagar os dados,
central, rede neural, toque, sobreposição, rotação e reabertura do processo.

## Limites da evidência

O kukybook26 estava offline na consulta ao Remote Desktop Commander. Não foi
possível realizar validação física nele. Emulador não comprova intensidade
da vibração, sensores de um aparelho real, comportamento de cada fabricante
ou execução ARM64 com páginas de 16 KiB. Testes Qt offscreen não comprovam
por si só o comportamento do cursor e de monitores físicos no Windows.

Código, arte e animações próprios continuam sob GPL-3.0-or-later, com créditos
ao Pestinha. Guias privados de referência da Drippy ficam fora do repositório
e dos pacotes.
