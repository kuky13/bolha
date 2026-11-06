> Histórico: este documento descreve a versão Electron 0.2.1. A versão 0.3.0
> preserva o modelo neural e usa Qt+Python no mesmo processo. Consumo do Electron
> e protocolos de worker abaixo são resultados anteriores, não medições nativas.
> Consulte [validação da versão nativa](VALIDATION-NATIVE.md).

# Inteligência comportamental da Bolha

Esta revisão aplica a proposta “Pestinha 2.0” à Bolha. Mantém Electron e o
cérebro Python original, conforme escolhido. Não inclui LLM, modelos para
baixar, serviço residente adicional, chat ou treinamento pesado.

## Arquitetura implementada

```text
Contexto autorizado e gestos
          ↓
Rede LIF original (470 neurônios) → emoções e impulsos
          ↓
Memória episódica e bandit existentes + rotina compacta
          ↓
Objetivo de 12–32 segundos, escolhido entre ações permitidas
          ↓
Comportamento e física originais → desenho da Bolha no Electron
```

O Pestinha já traz memória episódica, bandit contextual, condicionamento e
plasticidade neural. A implementação amplia esses mecanismos, evitando uma
segunda tabela Q ou uma segunda simulação do corpo.

- **Episódios:** até 500 acontecimentos estruturados; preferência contextual
  limitada a 256 contextos. Gravação atômica em lotes, junto do salvamento do
  cérebro, a cada 30 segundos e ao encerrar.
- **Feedback:** carinho reforça o objetivo recente; dispensa e pedido explícito
  de sossego dão sinais negativos. Falta de reação é neutra, sem ser interpretada
  como rejeição ou aprovação. A janela de atribuição é curta.
- **Rotina:** até 256 combinações de dia, hora e categoria de atividade, com
  contadores limitados e meia-vida de 30 dias. Sem lista cronológica de programas,
  títulos, texto digitado ou conteúdo da tela.
- **Motivação:** explorar, brincar, observar, descansar, trabalhar junto e
  procurar carinho. Rede neural, necessidades e experiência influenciam a
  escolha. Há exploração limitada e desincentivo a repetições consecutivas.
- **Prioridades:** arrasto, pausa, tela cheia, sono, castigo, fuga, protesto e
  missões de entrega mantêm prioridade. A preferência aprendida só escolhe entre
  ações permitidas. Ela não pode habilitar uma leitura ou atividade desligada.

A iniciativa de trabalhar junto alimenta a rede, sem simular um pedido feito
pelo usuário nem forçar a Bolha a sentar. O notebook continua sendo um brinquedo.

## Frequências e limites

| Trabalho | Frequência |
|---|---|
| Física enquanto visível | Até 60 Hz |
| Publicação de estados visuais | Até 30 Hz |
| Rede neural original | Até 10 Hz |
| Verificação do objetivo | 1 Hz; escolha ao terminar ou perder permissão |
| Hábitos e memória do processo | A cada 30 segundos |
| Persistência | A cada 30 segundos e ao sair |
| Publicação enquanto pausada/escondida | 1 Hz; simulação congelada |

O painel neural detalhado só publica as posições e os rastros dos neurônios
quando solicitado. Dados e logs permanecem locais.

## Orçamento confirmado com o usuário

**Buscar até 100 MB decimais de RSS para o cérebro Python.** Isso corresponde a
aproximadamente 95,4 MiB. O consumo total do Electron e de seus processos será
medido e apresentado separadamente. Os 70 MB citados no texto inicial para
Pestinha/Qt não são uma linha de base do aplicativo Electron.

Não há promessa de que o aplicativo completo use 100 MB. Uma primeira amostra
Linux/Xvfb, anterior à extensão, registrou 42,4 MiB no cérebro e cerca de 685 MiB
na soma de RSS da árvore. Memória compartilhada pode entrar nessa soma em mais
de um processo; renderização por software e depuração também afetam a comparação.

O próprio cérebro mede seu RSS a cada 30 segundos. Três amostras consecutivas
acima do orçamento suspendem a autonomia adicional naquela sessão e preservam
o comportamento original. Esse recurso não promete reduzir sozinho a memória
da interface ou do NumPy.

## Controle pelo usuário

Em **Vida**, “Comportamento adaptativo” desliga os objetivos novos; a rede e o
comportamento original continuam funcionando. “Ficar quietinha” sinaliza a
preferência e suspende o passeio por 30 segundos.

Em **Contexto**, “Aprender minha rotina” controla separadamente a coleta e a
influência desses padrões. “Apagar aprendizado e memória” pede confirmação e
reinicia sinapses aprendidas, episódios, condicionamento, necessidades,
protestos, castigo e hábitos da Bolha, preservando as configurações do app.

## Validação reproduzível

```powershell
python -m pytest brain/tests -q
npm run build
$env:BOLHA_PYTHON = (Resolve-Path .venv\Scripts\python.exe).Path
node scripts/benchmark.mjs
```

Para medir o aplicativo empacotado, defina `BOLHA_SMOKE_EXE` com o caminho de
`Bolha.exe`. `BOLHA_BENCH_SECONDS` permite sessões maiores (20 segundos por
cenário por padrão). O resultado fica em `validation/performance-win32.json`.

O benchmark acompanha a árvore inteira, separa RSS/CPU do cérebro e observa
três cenários: Bolha ativa, monitor neural e pausa. CPU é apresentada como
porcentagem de um núcleo; a do seletor é medida separadamente. Esses ensaios
curtos não provam consumo máximo em sessões prolongadas ou hardware diferente.

Os testes controlados verificam aprendizado positivo/negativo, ausência de
resposta neutra, hábitos por horário e esquecimento, retenção, reinício,
objetivos persistentes, permissões e modo compatível. Uma simulação de 3.000
escolhas verifica que a alocação incremental fica abaixo de 8 MiB, sem atribuir
esse limite ao aplicativo inteiro.
