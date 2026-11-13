# Validação da Bolha 0.5.1

Os testes locais cobrem lançamentos físicos, sorteio entre 1 e 100, rodadas com
quadros lentos, bola perdida, interrupção ao pegar o brinquedo, posição do balão
ao mudar o número e pose coerente entre toques. O Qt exibiu uma reação real da
rede em RAM e avançou quadros da animação.

A reprodução em aparelhos físicos e a rotação em paisagem não foram conferidas.

O [Windows](https://github.com/kuky13/bolha/actions/runs/43491173765) passou
em 740 testes e 24 cenários de instalação, atualização e recuperação. O
[Android 15](https://github.com/kuky13/bolha/actions/runs/43491174268) passou
em 11 verificações, com memória e preferências preservadas. As duas builds
testaram a atualização da 0.5.0 e foram geradas no commit `69e0019`.
Os hashes dos arquivos e a assinatura do APK foram conferidos.
