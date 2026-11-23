# Relatos da Bolha

O serviço recebe relatos voluntários de Windows e Android e encaminha ao
projeto privado da Bolha na API de envio do BugPin Community.

## Homologação na VPS

A partir da raiz do repositório, execute `docker compose -p bolha-relatos-hml
-f service/compose.yml up -d --build`. As portas 17300 (BugPin) e 17301
(recebimento) escutam apenas no loopback. Use um túnel SSH autorizado para abrir
o assistente do BugPin e criar a conta administrativa, exigir 2FA e criar um
projeto Bolha. Guarde a chave de envio em arquivo de ambiente privado (modo
0600), fora do Git, e use `--env-file` no Compose ao recriar somente o gateway.
Configure 90 dias em *Settings → General → Data Retention Days* e habilite
anexos de imagem e vídeo no projeto.

O gateway aceita `POST /v1/reports` com o campo multipart `data` (JSON) e até
três partes `media`. O JSON contém título, descrição, passos, plataforma,
versão, autorização afirmativa, ID de envio, e os campos opcionais de
diagnóstico e erros. O protocolo devolvido identifica o relato para o suporte.
Repita o mesmo ID de envio ao tentar novamente.

## Ativação pública

Publique somente o endpoint `/v1/reports` em
`https://relatos.kuky.solutions`, com TLS, limite de corpo de 21 MiB,
timeout, limitação de requisições e sem registrar corpo, endereço IP ou
cabeçalho de autorização no log de acesso. O proxy deve ser o único caminho
para o gateway, e o gateway deve confiar apenas no endereço desse proxy para
o cabeçalho de encaminhamento. O painel do BugPin permanece no loopback ou
em acesso administrativo privado.

Mantenha o volume restrito ao BugPin e os backups cifrados com expiração
máxima de 30 dias. Ao atender um pedido recebido pelo canal de suporte, confirme
o protocolo, apague o relato e seus anexos no painel e registre a exclusão
sem o conteúdo. Se restaurar um backup, reaplique exclusões pendentes antes
de disponibilizá-lo. Só copie para o GitHub resumos revisados para divulgação.

Referências: [API do widget](https://docs.bugpin.io/api/widget-api),
[configuração de retenção](https://docs.bugpin.io/configuration/server).
