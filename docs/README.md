# Guias

Comece pelo [README do projeto](../README.md) para baixar ou rodar a Bolha.
Este índice aponta para os detalhes de cada tarefa.

## Usar e personalizar

- [Usar a Bolha](USO.md): gestos, menus, perfil, privacidade e rede.
- [Personalizar sua mascote](PERSONALIZAR.md): cores, expressões, falas,
  notebook, diferenças entre PC e Android e como compilar uma cópia.
- [Android](../android/README.md): instalar, flutuar, configurar e compilar.

## Desenvolver e verificar

- [Contribuir](../CONTRIBUTING.md): ambiente de desenvolvimento e práticas para
  pull requests.
- [Compilar e validar no Windows](BUILD.md): instalador, verificações e
  recuperação de atualização.
- Testes automatizados: `python -m pytest -q` no Windows; no Linux com Qt sem
  janela, `QT_QPA_PLATFORM=offscreen python -m pytest -q`.

## Versões e histórico

- [Notas da versão atual do repositório](RELEASE.md).
- [Validação nativa](VALIDATION-NATIVE.md) e [auditoria 0.5.4](AUDITORIA-0.5.4.md).
- Os demais relatórios `VALIDATION-*` e `INTELLIGENCE.md` registram versões e
  ensaios anteriores. Leia a versão e o ambiente descritos em cada relatório;
  resultados históricos não comprovam a validação da versão atual.

Para relatar um problema ou sugerir uma ideia, use **Issues** no GitHub. Não
anexe perfis, arquivos de aprendizado, logs com dados pessoais, credenciais ou
materiais privados de referência.

- [Roadmap futuro de otimização com Rust](ROADMAP-RUST.md)
