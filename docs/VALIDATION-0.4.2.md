# Validação da Bolha 0.4.2

O instalador Windows x64 foi gerado a partir do commit
`7890791701d32b0c6c0e19517500758b90b70467`.
O arquivo tem 34.910.449 bytes e SHA-256
`39147b47480f0e0fba6006b359e2c353de07f9b900131341581a937ac6249caf`.
A publicação reutiliza esse binário, com os mesmos metadados SHA-256 e SHA-512.
[Execução do CI Windows](https://github.com/kuky13/bolha/actions/runs/42130764541).

- Passaram 421 testes automatizados no Windows.
- Passaram 10 cenários de instalação e atualização em perfil isolado,
  incluindo instalação limpa, checksum inválido, download interrompido,
  adiamento persistente por uma hora, retomada offline, cache adulterado,
  recuperação após falha de abertura e atualização automática após 30 segundos.
- A atualização nativa foi testada da 0.4.2 para uma fixture 0.4.3.
  Preferências, semente e aprendizado foram preservados. O registro real
  permaneceu intacto e os arquivos temporários foram removidos após abertura saudável.
- A auditoria do pacote aprovou a distribuição Python/Qt e a presença
  do decodificador GIF.
- As prévias das quedas, do estouro e da volta pelos dois cantos foram
  renderizadas pela interface Qt real com entradas simuladas.
- O teste visual no kukybook26 ficou pendente porque o dispositivo estava
  offline. A migração Electron e o teste da 0.4.1 para a 0.4.2 no notebook
  não foram repetidos nesta compilação.

O aplicativo procura a versão estável mais recente publicada no GitHub.
Antes desta publicação, o canal anunciava a 0.4.1 e não oferecia a 0.4.2.
A distribuição do instalador de teste pela conversa não altera esse canal.

O instalador está sem assinatura digital.
