# Bolha no Android

A interface Android usa o cérebro local e a física da Bolha em Python via Chaquopy.
O app roda em Android 7.0 ou posterior em ARM64 e x86_64. Os APKs publicados
usam uma chave de teste própria do projeto, preservada nas próximas versões
para permitir a atualização com os dados do aplicativo. Essa chave identifica
os pacotes do projeto e não envolve verificação comercial de identidade.

Toque na Bolha para dar carinho. Arraste e solte a mascote ou o brinquedo para
arremessar. Use os botões para dar uma bicuda, jogar para cima, mostrar ou
guardar o brinquedo, trocar bola e amendoim, abrir o notebook e dormir ou acordar.

Para flutuar, toque em **Flutuar** e permita a sobreposição nas configurações
do Android. Use **Parar** na notificação ou **Parar de flutuar** no app.
O modo flutuante usa janelas pequenas para a mascote e o brinquedo e mantém
os outros apps acessíveis ao redor. A opção **Vibração** controla os pulsos
de toque, rebatida e irritação. A memória fica no armazenamento privado do app.

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

O workflow Android executa o teste de cadência de vibração em Java, instala
o APK em um emulador Android 15 e testa sobreposição, encerramento e persistência.
O emulador verifica o controle e a lógica de vibração. A intensidade do pulso
depende do aparelho.

Código e artes próprios sob GPL-3.0-or-later. Veja [NOTICE.md](../NOTICE.md)
para autoria e licenças. A interface Android tem controles por toque e não
inclui a bandeja, sensores de janelas, painel neural, atualizador silencioso
ou todos os efeitos e atividades da interface Qt.
