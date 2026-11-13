# Bolha 0.5.0 no Android

A interface Android usa o cérebro local, a física e o relógio de expressões da
Bolha em Python via Chaquopy, com desenho nativo em Canvas. O projeto é baseado
no [Pestinha, de mille-okws e colaboradores](https://github.com/mille-okws/pestinha).
O app roda em Android 7.0 ou posterior em ARM64 e x86_64. Os APKs publicados
usam uma chave de teste própria do projeto, preservada nas próximas versões
para permitir a atualização com os dados do aplicativo. Essa chave identifica
os pacotes do projeto e não envolve verificação comercial de identidade.

## Usar e configurar

Toque na Bolha para dar carinho. Mantenha o dedo pressionado para segurá-la;
arraste e solte em movimento para arremessar a mascote ou o brinquedo. O ponto
de pega é preservado. O arrasto usa o deslocamento bruto do toque convertido
para dp, inclusive quando a própria janela flutuante se move. Cancelar o gesto
ou retirar o dedo acompanhado em um toque múltiplo encerra a captura sem impulso.

A **Central** reúne seis seções, com navegação horizontal em celulares e lateral
em telas largas:

- **Aparência:** tamanho e opacidade da Bolha, boca opcional, bola ou amendoim e
  escala individual de brinquedo, notebook, reações, bilhetes, cartazes,
  cantinho e efeitos.
- **Comportamento:** passeio, objetivos, aprendizado, hábitos, falas,
  travessuras, GIFs online, estouro, vibração e reação ao chacoalhar.
- **Cérebro:** atividade real dos 470 neurônios, emoções, necessidades,
  decisões e aprendizado. Toque em um neurônio para ver seu tipo, sua atividade
  e até 70 das conexões mais fortes que entram ou saem dele.
- **Atividades:** carinho, sono, brinquedo, bicuda, lançamento para cima,
  pingue-pongue por toque, notebook, trabalho, comemoração, castigo, sossego e
  pedido de reação online. Há uma prévia de expressões que usa as poses reais
  sem criar uma experiência de aprendizado.
- **Privacidade:** controles independentes para posição do toque, inatividade
  nas interações com a Bolha e aplicativo ativo.
- **App:** sobreposição, versões no GitHub, diagnóstico copiável, reinício do
  aprendizado com backup e créditos.

Corpo, olhos, orelhas e boca compartilham centro, rotação e deformação. As poses
incluem irritação ao segurar, sono com pequenos zzz, carinho, piscadas, corrida,
quedas e pousos, rebatidas, estouro e retorno tímido pelo canto. Os pedidos de
atividades usam o mesmo modelo de comportamento da edição para computador;
humor, energia e experiências influenciam as respostas.

Para flutuar, toque em **Flutuar** e permita a sobreposição nas configurações
do Android. Use **Parar** na notificação ou **Parar de flutuar** no app.
O serviço em primeiro plano mantém uma notificação enquanto as janelas estão
ativas. Áreas pequenas recebem os toques da mascote e dos objetos; os desenhos,
efeitos e balões usam uma superfície sem captura de toque. No Android 12 ou
posterior, a transparência dessa superfície respeita o limite do sistema para
permitir que os toques atravessem até o aplicativo abaixo.

**Reagir ao chacoalhar** começa desligado. Quando ativado, usa o sensor de
aceleração disponível e a sensibilidade escolhida para aplicar movimento à
Bolha e ao brinquedo soltos; o objeto segurado continua no dedo. A opção fica
indisponível se o aparelho não tiver sensor compatível. **Vibração** controla
os pulsos de carinho, impacto e irritação. A intensidade percebida depende do
aparelho. Sensores e ciclos são suspensos com a tela apagada ou sem sessão ativa.

## Dados e rede

Preferências, semente, hábitos e aprendizado ficam no armazenamento privado do
aplicativo. Encerrar e abrir novamente preserva esses dados. O reinício manual
do aprendizado cria backup antes de substituir a memória. Preferências
ilegíveis são preservadas em uma cópia local, com aviso no diagnóstico e as
leituras opcionais desligadas.

O reconhecimento do aplicativo ativo começa desligado e exige também a
autorização **Acesso de uso** do Android. Só o identificador do aplicativo é
consultado; a Bolha não lê conteúdo da tela nem texto digitado. A posição do
toque se limita às interações recebidas pelas próprias janelas da Bolha. O
tempo ocioso é o tempo sem interagir com ela, não uma medição global do celular.

As reações online também começam desligadas. Ao habilitá-las junto das
travessuras, a Bolha pesquisa imagens e GIFs conforme o humor, usando a busca
compartilhada com a edição de computador. Arquivos baixados e decodificados
ficam somente em RAM; não há gravação de GIFs no armazenamento. Cada reação
aparece por tempo limitado, sem borda nem informações. Mantenha o dedo sobre
ela para consultar a origem, abri-la no navegador ou dispensá-la. Falhas de rede
ou de decodificação encerram a reação e produzem um aviso local.

As atualizações Android são instaladas pelo usuário a partir do APK no GitHub,
com a mesma chave e o mesmo identificador de aplicativo para preservar os
dados. Não há instalação silenciosa de atualizações.

## Compilar

Instale o Android SDK Platform 35, Build Tools 35.0.0, JDK 21 e Gradle 8.14.3.
Instale Python 3.13 e deixe `python3.13` acessível no terminal da compilação.
Configure `ANDROID_HOME` e execute `gradle -p android :app:assembleDebug` na raiz.
O APK fica em `android/app/build/outputs/apk/debug/app-debug.apk`.
Compilações locais usam a chave de depuração do Android. O pipeline de publicação
recebe a chave do projeto por `BOLHA_ANDROID_KEYSTORE` e sua senha por
`BOLHA_ANDROID_KEYSTORE_PASSWORD`.

O APK usa Chaquopy 17.2.0, CPython 3.13 e os wheels NumPy 2.3.2 do
[índice mantido pelo Chaquopy](https://chaquo.com/pypi-upstream/numpy/).
As bibliotecas ARM64 atendem ao alinhamento ELF de 16 KiB. Essa verificação
estática ainda precisa ser complementada por execução em um aparelho ARM64
com páginas de 16 KiB. O binário x86_64 é destinado aos emuladores de 4 KiB.

O workflow Android está configurado para testar cadência de vibração, arrasto e
detecção de chacoalhar em Java, instalar o APK em um emulador Android 15 e
exercitar interface, sobreposição, encerramento e persistência. Os registros e
capturas dessa execução devem ser consultados para saber o que passou em cada
build. Um teste em emulador não confirma vibração, desempenho ou sensores em
um aparelho físico.

Código e artes próprios sob GPL-3.0-or-later. Veja [NOTICE.md](../NOTICE.md)
para autoria e licenças de terceiros. A interface Android tem controles por
toque e não inclui bandeja, leitura de bordas ou geometria das janelas de outros
apps, travessura de esconder o ponteiro do sistema nem o atualizador silencioso
da edição Qt. A autorização de sobreposição e as restrições de segundo plano
dependem do Android e do fabricante. A correspondência visual usa as mesmas
poses e regras de comportamento, com desenho e entrada próprios do celular;
validação em diferentes aparelhos físicos continua necessária.
