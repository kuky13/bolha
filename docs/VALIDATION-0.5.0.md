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

Os relatórios Windows e Android da candidata serão registrados aqui após a
execução dos workflows. A candidata ainda não é uma release estável publicada.

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
