# Bolha 0.5.5

- Aprendizado sináptico da rede neural (`LIFBrain`) atualizado de forma incremental nas fatias plásticas, eliminando cópias de matriz completa a cada passo com recompensa.
- Distribuição dinâmica dos neurônios sensoriais e motores no Monitor Neural para evitar sobreposição visual no canto inferior.
- Memória episódica (`EpisodicMemory`) agora respeita os limites de contextos e ações na consolidação do sono e isola episódios de metas dos eventos de travessura.
- Recuperação automática da autonomia quando o consumo de memória volta abaixo de 85% do orçamento (histerese), ajuste completo dos relógios de condicionamento e inteligência ao retomar de pausas, e generalização hierárquica por atividade e emoção.

No Windows, use **Central da Bolha → App → Verificar atualizações** ou baixe o instalador x64 sem assinatura digital. No Android, instale o APK sobre a versão anterior para preservar os dados.

Projeto aberto à comunidade sob GPL-3.0-or-later, incluindo artes e animações, baseado no [Pestinha](https://github.com/mille-okws/pestinha), de [mille-okws](https://github.com/mille-okws) e colaboradores. Para rodar pelo código, siga as [instruções de instalação](https://github.com/kuky13/bolha/blob/v0.5.5/README.md#rodar-pelo-código-como-no-pestinha).
