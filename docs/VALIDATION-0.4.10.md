# Validação da Bolha 0.4.10

A edição Windows está publicada na [versão 0.4.10](https://github.com/kuky13/bolha/releases/tag/v0.4.10).
O instalador corresponde ao commit `0f08aedb7ad6ae566b5790c42429234ffb4dfca4`.

## Windows e atualização

A [execução Windows](https://github.com/kuky13/bolha/actions/runs/43356280863)
aprovou 684 testes, a auditoria do pacote e quatro cenários do assistente de
escolha de pasta. A instalação e a atualização passaram por dez cenários,
incluindo download interrompido, checksum incorreto, cache alterado, adiamento
persistente de uma hora, retomada offline, recuperação após falha de abertura,
contagem real de 30 segundos e limpeza após confirmar a nova versão.

A mesma execução verificou a atualização da versão pública 0.4.4 para 0.4.10
e as migrações Electron 0.1.0 e 0.2.1, preservando preferências, semente e
aprendizado. A versão 0.4.11 serviu apenas como alvo descartável para testar a
atualização entre duas versões nativas.

Todos esses testes passaram. A etapa final de publicação recebeu HTTP 403
do GitHub. Os arquivos do artefato dessa execução foram baixados, conferidos
pelo manifesto e publicados pelo cliente GitHub autenticado, no mesmo commit.
A compilação duplicada disparada pela criação da tag foi cancelada.

O atualizador real consultou a versão pública a partir das versões 0.4.4,
0.4.5 e 0.4.9. As três receberam 0.4.10. Um download público completo também
conferiu com o SHA-256 do instalador
`3e2a011fd92f16faee98a914bae9b0018452a13fb7460b5bfaa8e73503c223cc`.

Na amostra curta do runner Windows, o aplicativo novo usou 78,75 MiB RSS,
com intervalo de quadros p95 de 16 ms. Os arrays principais do cérebro somaram
4,651 MiB. Esses valores descrevem essa execução e esse computador virtual.

## Execução pelo código

O ZIP completo abre com Python 3.11, `pip install -r requirements.txt` e
`python main.py`. Uma extração limpa abriu em Linux com Qt offscreen, confirmou
estado saudável, versão 0.4.10 e 470 neurônios, e encerrou normalmente.
A suíte local passou em 673 testes, com 11 dependentes de Windows ignorados.

As preferências seguem em `%APPDATA%\bolha`. A edição por código é atualizada
baixando outra versão ou atualizando o clone. O instalador possui o fluxo de
atualização automática.

## Desenho e mudanças do Pestinha

Os testes dos balões verificam dimensionamento com a mesma fonte e dispositivo
Qt usados no desenho, texto inteiro na parte superior e inferior da tela,
coordenadas negativas e troca de posição quando o brinquedo ocupa o espaço.
Falas curtas usam balões menores e desaparecem mais cedo.

A [revisão do Pestinha](PESTINHA-2026-11.md) registra o balanço de digitação e
os gestos da roda adaptados, além das mudanças de rosto e plataformas que ainda
precisam de integração específica. O upstream foi conferido no commit
`0bb768a2be024221ee1da62cc335362279d912d6`.

## Limites da validação

A validação gráfica Windows ocorreu em runner descartável. Arrasto real,
monitores físicos com escalas diferentes e comportamento com todos os
aplicativos do usuário precisam de verificação no computador de uso.
O instalador Windows é distribuído sem assinatura digital.
