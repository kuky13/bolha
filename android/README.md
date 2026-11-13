# Bolha no Android

A interface Android usa o cérebro local e a física da Bolha em Python via Chaquopy.
O app roda em Android 7.0 ou posterior em ARM64 e x86_64. O APK desta rodada usa a
assinatura de teste do Android. Versões futuras precisam manter a mesma chave
para atualizar esse APK sem desinstalar.

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
Configure `ANDROID_HOME` e execute `gradle -p android :app:assembleDebug` na raiz.
O APK fica em `android/app/build/outputs/apk/debug/app-debug.apk`.

O workflow Android executa o teste de cadência de vibração em Java, instala
o APK em um emulador Android 15 e testa sobreposição, encerramento e persistência.
O emulador verifica o controle e a lógica de vibração. A intensidade do pulso
depende do aparelho.

Código e artes próprios sob GPL-3.0-or-later. Veja [NOTICE.md](../NOTICE.md)
para autoria e licenças. A interface Android tem controles por toque e não
inclui a bandeja, sensores de janelas, painel neural, atualizador silencioso
ou todos os efeitos e atividades da interface Qt.
