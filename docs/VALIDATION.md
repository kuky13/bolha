# Validação da Bolha 0.1.0

As verificações de lógica, execução em desktop virtual e uso em hardware real
são tratadas separadamente. Não há credenciais ou arquivos privados da OneDrip
na compilação independente.

## Lógica e execução local

Em 3 de novembro de 2026, passaram:

- Verificação TypeScript, sete testes da ponte/preferências/atualizações e
  59 testes Python do núcleo, condicionamento e integração.
- Aprendizado positivo e negativo, silêncio neutro, retenção de episódios,
  rotina por horário, esquecimento, persistência, remoção da memória,
  desligamento da rotina/autonomia e modo de compatibilidade.
- Estouro por arremessos fortes, recuperação, pânico persistente, castigo,
  fuga e perdão.
- Simulações com coordenadas negativas, remoção de monitor, tela cheia em
  monitores com escalas diferentes e passagem entre telas livres quando outra
  está ocupada.
- Compilação de produção e auditoria de dependências/endpoints removidos.
- Electron real em Linux/Xvfb, cérebro Python original em execução, abertura
  das configurações e painel com atividade dos 470 neurônios, sem erro de página.

## Medição curta em Linux/Xvfb

20 amostras, aproximadamente um segundo entre elas, por cenário:

| Cenário | Pico RSS cérebro | Pico soma RSS total | CPU cérebro / um núcleo | CPU total / um núcleo |
|---|---:|---:|---:|---:|
| Ativa | 42,92 MiB | 724,57 MiB | 15,23% | 68,57% |
| Monitor neural | 43,25 MiB | 743,92 MiB | 26,25% | 75,04% |
| Pausada | 43,25 MiB | 738,38 MiB | 0,16% | 3,21% |

O seletor de objetivos/hábitos consumiu aproximadamente 0,002% de um núcleo
nesse ensaio. Isso não representa o custo completo da rede neural ou da
interface. O alvo de 100 MB para o cérebro foi atendido nessa amostra; não é uma
garantia de máximo para sessões prolongadas.

O RSS total soma processos e pode contar páginas compartilhadas mais de uma
vez. Linux/Xvfb e renderização por software não substituem medição no Windows
com GPU. Não interpretar esses valores como benchmark de um computador pessoal.

## Pipeline Windows

O [GitHub Actions](https://github.com/kuky13/bolha/actions/workflows/windows.yml)
parte de um checkout limpo e executa:

1. Tipos, testes e compilação independente.
2. Empacotamento do Python e geração do instalador NSIS.
3. Abertura do `Bolha.exe` empacotado, com cérebro sem Python externo.
4. Medição dos processos em três cenários, publicada como JSON no artefato.
5. Instalação e atualização para uma versão seguinte de teste, por feed local.
6. Checksum inválido, download interrompido, continuidade, prazo de 30 segundos,
   adiamento de uma hora persistido, reabertura, conservação de preferências e
   de uma associação neural conhecida, e limpeza do instalador.

Os arquivos da versão seguinte são exclusivos do teste e não são publicados.
Uma tag só publica o instalador base após sucesso do job completo. Os logs e
artefatos daquela execução constituem a evidência Windows para a versão.

## Validação física ainda necessária

O runner Windows tem um desktop virtual. Ainda é necessária uma sessão com
monitores físicos, escalas e resoluções diferentes, conexão/desconexão de telas,
jogos/vídeos em tela cheia e players reais para validar fluidez, foco, passagem
de cliques, atalhos e controles de música nesses dispositivos.

O instalador é experimental e não possui assinatura comercial. Sessões de
horas/dias em hardware real também permanecem fora do ensaio curto automatizado.
