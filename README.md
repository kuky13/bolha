# Bolha

A Bolha passeia, pula e quica pela sua tela, brinca com uma bolinha, senta no
próprio notebook e aprende com suas interações. O desenho da bolha usa
Electron/React; o cérebro é a rede neural local original do
[Pestinha](https://github.com/mille-okws/pestinha), com 470 neurônios.

**Aplicativo experimental, para Windows x64.**

[Baixar o instalador](https://github.com/kuky13/bolha/releases/latest)

## O que acompanha

- Carinho, cutucada, arrasto direto, arremesso, giro e pouso sobre janelas.
- Rosto vetorial com olhos simétricos, brilho suave e flutuação independente.
  Deitar vira somente o rosto; a esfera continua redonda. O chão é físico e invisível.
- Emoções, energia, carência, aprendizado, condicionamento e memória local.
- Bolinha, notebook de brincadeira, fogos, cartazes, protestos e castigo.
- Oito memes novos da Bolha e bilhetes: no máximo uma travessura a cada cinco
  minutos, até três objetos na tela; tudo configurável.
- Se for muito arremessada, a Bolha estoura, some por 30 segundos e volta
  tímida pelo canto. Carinho acelera a recuperação. O limite começa em 12
  arremessos fortes por minuto; os saltos dela não entram nessa conta.
- Controles de música do Windows, com atalhos e dança.
- Painel com atividade neural, humor, necessidades e associações aprendidas.
- Rotina com esquecimento gradual, objetivos persistentes e aprendizado por
  contexto. Carinho reforça preferências; ausência de resposta é neutra.
- Opções para desligar o comportamento adaptativo e apagar todo o aprendizado.

Veja [a implementação da inteligência e seu orçamento](docs/INTELLIGENCE.md).
O alvo de 100 MB se aplica ao cérebro Python; o Electron é medido separadamente.

## Como usar

Instale o `.exe` da página de versões. O instalador já inclui o cérebro Python;
não é necessário instalar Python separadamente.

| Ação | Resultado |
|---|---|
| Clicar | Cutuca a Bolha |
| Passar o mouse de um lado para o outro sobre ela | Faz carinho |
| Arrastar e soltar | Leva junto ou arremessa |
| Rodinha | Gira |
| Configurações → Bolha → Deitar / Levantar | Descansa o rosto e volta a olhar para você |
| Botão direito | Abre configurações e atividades |
| Duplo clique | Abre o painel do cérebro |
| Ícone perto do relógio | Mostrar, esconder, pausar e sair |
| Ctrl + Alt + Shift + B | Pausa ou retoma tudo |

Ela evita monitores em tela cheia e continua nos demais; se todos estiverem
ocupados, fica escondida. Iniciar com o Windows é opcional e vem desligado.

## Dados e contexto

Tudo o que a Bolha aprende fica em `%APPDATA%\bolha\brain`. Aparência e
preferências ficam no diretório próprio `%APPDATA%\bolha`, separado de outros
aplicativos. Reinstalar ou atualizar preserva esses arquivos. A versão 0.2 migra
a pasta de memória anterior automaticamente, sem sobrescrever uma pasta nova existente.

Você pode desligar separadamente a leitura do nome do programa ativo, do
tempo ocioso, da posição do cursor e da geometria das janelas. Não há captura
de tela, leitura de títulos/conteúdo, chat, conta, créditos ou provedor de IA.

A única comunicação de rede do aplicativo é a busca/download de atualizações
no GitHub. O cérebro conversa com a interface por entrada/saída padrão, sem
abrir portas locais ou enviar sua memória para servidores.

## Atualizações

A versão instalada consulta o GitHub ao abrir e a cada seis horas. Uma versão
nova é baixada e verificada. Depois aparece um aviso de 30 segundos, com opção
de adiar por uma hora. Ao instalar, a Bolha salva e fecha o cérebro, atualiza
e reabre. O instalador usado é removido depois que a nova interface e o cérebro
confirmam a inicialização; arquivos ainda bloqueados são limpos depois.

## Compilar pelo código

Use Node.js 22 e Python 3.11. Em um terminal no projeto:

```powershell
npm ci
python -m venv .venv
.venv\Scripts\python -m pip install -r brain/requirements.txt pytest==8.4.2 pyinstaller==6.22.3
$env:BOLHA_PYTHON = (Resolve-Path .venv\Scripts\python.exe).Path
npm run dev
```

Para testar e gerar o instalador, no Windows:

```powershell
npm run typecheck
npm test
.venv\Scripts\python -m pytest brain/tests -q
npm run build
npm run audit:standalone
.venv\Scripts\python scripts/build-brain.py
npx electron-builder --win --publish never
```

O resultado fica em `release/`. Nenhuma credencial, `.env` ou serviço externo
é necessário para compilar. O GitHub Actions gera e testa o instalador; tags
`v<versão>` publicam os arquivos depois dos testes.

## Organização

- `src/`: aplicativo, ponte Electron, interface e renderização da Bolha.
- `brain/`: cérebro original do Pestinha, adaptadores de cena e processo local.
- `assets/bolha/`: geometrias, aparência, ícones e conteúdo da personagem.
- `docs/`: notas e validação; `NOTICE.md`: autoria e origem do código.

Não há dois motores disputando o corpo: Python decide física e comportamento,
e a interface desenha o estado recebido. A rede é uma simulação LIF com
topologia definida pelo projeto original; o notebook do pet é uma brincadeira,
não executa comandos no computador.

## Licenças

Código próprio: **GPL-3.0-only**. O código derivado do Pestinha mantém seus
avisos **GPL-3.0-or-later**. Consulte [LICENSE](LICENSE) e [NOTICE.md](NOTICE.md).

As artes da Bolha são separadas, sob **CC BY-NC 4.0**, com atribuição e uso não
comercial. Consulte [licença das artes](licenses/BOLHA-ASSETS.md). Os memes e
textos do pacote original do Pestinha não foram copiados.

O código é aberto; a restrição não comercial se aplica às artes fornecidas,
e deve ser observada por quem redistribui um pacote contendo essas artes.
