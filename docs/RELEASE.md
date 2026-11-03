Bolha 0.1.1 corrige o encerramento do cérebro no Windows ao fazer carinho.

O coração ♡ da frase de carinho causava `UnicodeEncodeError` quando o Python
empacotado usava a codificação cp1252. A comunicação com o cérebro agora usa
UTF-8 explicitamente, inclusive nos logs e na leitura dos canais pelo Electron.

A atualização preserva a memória salva e as configurações. Inclui teste de
regressão com cp1252 e interação de carinho no aplicativo Windows empacotado.

Use **Configurações → App → Verificar atualização** ou instale
`Bolha-Setup-0.1.1-x64.exe`.

O instalador experimental não possui assinatura digital. A validação em
monitores físicos com escalas diferentes e players reais continua pendente.
