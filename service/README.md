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

O caminho público é `https://api.kuky.solutions/bolha/v1/reports`, encaminhado
internamente para `/v1/reports`. O Caddy encaminha somente `POST` e `OPTIONS`,
limita o corpo a 21 MiB e pula o log de acesso dessa rota. O navegador pode
enviar a partir de `https://bolha.kuky.solutions`; os apps nativos enviam sem
cabeçalho `Origin`. A chave do projeto permanece no gateway.

Na VPS, use `compose.proxy.yml` junto de `compose.yml` para conectar o gateway
à rede Docker externa `bolha-relatos-proxy` e configure
`FORWARDED_ALLOW_IPS` com o endereço do Caddy nessa rede. O painel do BugPin
permanece acessível apenas por loopback ou túnel administrativo. Para suspender
o recebimento, desative somente a rota no Caddy e preserve o volume do BugPin.

Mantenha o volume restrito ao BugPin e os backups cifrados com expiração
máxima de 30 dias. Ao atender um pedido recebido pelo canal de suporte, confirme
o protocolo, apague o relato e seus anexos no painel e registre a exclusão
sem o conteúdo. Se restaurar um backup, reaplique exclusões pendentes antes
de disponibilizá-lo. Só copie para o GitHub resumos revisados para divulgação.

Referências: [API do widget](https://docs.bugpin.io/api/widget-api),
[configuração de retenção](https://docs.bugpin.io/configuration/server).
