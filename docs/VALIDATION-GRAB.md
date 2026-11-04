# Candidata de teste 0.3.2: correção da pega

A fonte **0.3.2** prepara a correção da pega no
[PR #2](https://github.com/kuky13/bolha/pull/2). A versão pública permanece
**0.3.0**. Esta nota registra a intenção da candidata e as evidências ainda
necessárias para avaliá-la no Windows.

## Comportamento pretendido

- Manter a Bolha presa ao ponteiro enquanto o botão da pega estiver pressionado,
  inclusive ao mover o mouse rapidamente ou para fora da janela do pet.
- Encerrar a pega quando o botão for solto. Parado, liberar a gravidade;
  em movimento, conservar o impulso recente para arremessar a Bolha e o
  amendoim/bolinha, com força semelhante ao Pestinha e velocidade limitada.
  Perda de captura com o botão físico pressionado conserva a pega;
  cancelamentos explícitos devem limpar a interação sem arremesso.
- Reduzir a oscilação visual durante a pega para até **3% de deformação** e
  **1,5° de rotação extra**, sem deslocar o centro visual. Olhos, orelhas e
  risquinhos continuam mostrando irritação gradual modulada pelo cérebro.

Sono, manias e reações após soltar mantêm o comportamento existente. A correção
usa o ciclo atual do aplicativo; não acrescenta um temporizador de animação.

## Versão e histórico

`bolha/__init__.py` e `pyproject.toml` identificam a fonte como **0.3.2**.
O empacotamento existente grava a versão em `bolha-version.json`; o executável
instalado lê esse recurso. O workflow existente calcula **0.3.3** como próxima
fixture de atualização para uma compilação desta candidata.

A **fixture 0.3.2** descrita no
[histórico da 0.3.1](VALIDATION-EXPRESSIONS.md) reutilizou o bundle daquela
versão, alterando a identificação para testar a atualização. Seus resultados
continuam vinculados à fonte e aos artefatos da 0.3.1. Esta candidata 0.3.2
contém código novo e exige resultados próprios.

## Evidência atual e pendências

Os testes locais de pose usam Qt offscreen e verificam limites durante pegadas
longas, progressão da irritação, ausência de offsets de posição e geometria
da personagem sem boca. Eles não comprovam captura nativa, instalação ou uso
real no Windows.

Permanecem pendentes para esta candidata:

- Compilar e auditar o instalador 0.3.2 no Windows, vinculando os artefatos ao
  commit exato testado e conferindo os checksums.
- Validar instalação e atualização com perfis isolados, preservando
  preferências, semente e aprendizado.
- Conferir a pega pela entrada real no Windows: movimento rápido, saída da
  janela, soltura fora dela, cancelamento, perda de captura e botão primário
  invertido. Conferir também foco e passagem de cliques na área transparente.
- Avaliar manualmente a firmeza do gesto, as expressões e as reações ao soltar,
  além dos cenários prolongados e com múltiplos monitores já pendentes.

Não há validação Windows atual registrada para a fonte 0.3.2 nesta nota.
Compilação e publicação dependem de etapas posteriores; esta preparação não
cria tag nem release.
