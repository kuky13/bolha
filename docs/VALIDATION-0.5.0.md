# Validação da Bolha 0.5.0

## Escopo

Android com expressões compartilhadas, central, painel neural real, arrasto em
coordenadas lógicas, sensores opcionais e mídia em RAM. PC com boca expressiva
e brincadeira do ponteiro escolhida pela política neural, com feedback e memória.

## Verificado localmente

- Linux, Python 3.11, Qt/PySide6 6.11.3: suíte completa com 700 testes aprovados
  e 11 verificações exclusivas de Windows ignoradas. Com corrida e bilhetes,
  a suíte passou a 707 testes aprovados e 11 ignorados.
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
esta execução cobre a candidata antes das correções de corrida e bilhetes.
O [workflow Windows 43427853641](https://github.com/kuky13/bolha/actions/runs/43427853641),
no commit `f2d9964`, validou o instalador com essas correções: 718 testes e
24 cenários de instalação, atualização nativa e recuperação passaram.
SHA-256 e SHA-512 aprovados. O runner mediu 78,54–81,03 MiB de memória
residente, quadros p95 de 16 ms e cérebro p95 de 5,61–6,06 ms.

A primeira execução do emulador encontrou o pacote `bolha` ausente: o Gradle
não havia executado o produtor dos fontes compartilhados em um ambiente limpo.
A dependência foi corrigida e uma compilação limpa executou as 47 tarefas com
sucesso. Uma nova guarda verifica os oito módulos necessários e as bibliotecas
ELF antes de iniciar o emulador. Os 88 ELF ARM64, incluindo CPython e NumPy,
atendem ao alinhamento de 16 KiB. Cinco casos sintéticos da guarda passaram.

O APK recompilado abriu e migrou a preferência de vibração. A verificação
inicial da memória comparava todos os pesos por igualdade depois de a rede
voltar a aprender. O teste atualizado grava uma associação reconhecível no
perfil descartável e tolera os pequenos ajustes dos primeiros ciclos sem
aceitar uma rede zerada. A candidata ainda não é uma release estável publicada.

O [workflow Android 43428971627](https://github.com/kuky13/bolha/actions/runs/43428971627),
no commit `982ba9b`, passou no Android 15 x86_64. Confirmou a atualização
do APK 0.4.10 com a mesma chave, memória e preferências preservadas; Central
e painel neural; arrasto da mascote e do brinquedo sobre outro app; movimento
do brinquedo em resposta à aceleração simulada; encerramento pelo botão
desobstruído e reabertura com o perfil salvo. SHA-256 e assinatura conferidos.
A rotação em paisagem não foi confirmada nessa imagem de emulador.

Esses dois pacotes precedem o ajuste de expressões da boca e tempo de leitura.
A revisão visual mais recente tem testes próprios de fechamento após susto,
alegria, mastigação e cuspida, além de prévia do desenho Qt.

## Limites da evidência

O kukybook26 estava offline na consulta ao Remote Desktop Commander. Não foi
possível realizar validação física nele. Emulador não comprova intensidade
da vibração, sensores de um aparelho real, comportamento de cada fabricante
ou execução ARM64 com páginas de 16 KiB. Testes Qt offscreen não comprovam
por si só o comportamento do cursor e de monitores físicos no Windows.

Código, arte e animações próprios continuam sob GPL-3.0-or-later, com créditos
ao Pestinha. Guias privados de referência da Drippy ficam fora do repositório
e dos pacotes.
