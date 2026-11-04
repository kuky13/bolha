# Validação da migração Qt0.3.0

Esta versão está em implementação. Não considere o instalador nativo publicado
ou validado em Windows até que as evidências desta seção sejam atualizadas.
Os resultados anteriores em `VALIDATION.md` pertencem às versões Electron.

Testes automatizados cobrem migração com backup e idempotência, sensores
preservados, falhas de gravação, URL/redirect, manifesto, checksum inválido,
download incompleto, cache alterado, adiamento persistente, retomada offline e
limpeza limitada aos arquivos próprios. Testes Qt verificam desenho e diálogos.

Pendentes: compilação e auditoria do pacote Windows, instalação isolada,
atualização entre duas versões nativas, migração real dos instaladores0.1.0 e
0.2.1 num Windows descartável, falha/recuperação, medições de CPU/RSS e quadros.
Também pendem monitores físicos com escalas diferentes, desconexão de tela,
foco/cliques de outros aplicativos e revisão visual prolongada.

As prévias aprovadas sem boca foram renderizadas pelo desenho Qt. Elas demonstram
o visual, não comprovam os resultados de instalação ou atualização.
