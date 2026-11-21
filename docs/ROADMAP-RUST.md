# Roadmap técnico da Bolha com Rust

Proposta futura, experimental e condicionada a resultados para Windows e Android. O documento original foi escrito em 21 de novembro de 2026 e analisou a Bolha 0.5.9. [Baixar o original em DOCX](Bolha_Roadmap_Rust_1.0.0.0.docx)

Rust só poderá entrar na versão **1.0.0.0 ou posterior**, após protótipos, medições, testes de compatibilidade e aprovação da publicação. A Bolha permanece local, de código aberto e com o mesmo comportamento e aprendizado. Otimizar gargalos medidos tem prioridade sobre reescrever componentes.

## Objetivos

- Reduzir trabalho repetitivo de CPU, principalmente no ciclo neural e na atualização visual.
- Medir eficiência energética, RAM e tamanho instalado antes de estabelecer metas.
- Preservar expressões, personalidade, interações, preferências, aprendizado, atualizações confiáveis e paridade entre as plataformas.

## Arquitetura examinada

| Componente | Base da 0.5.9 | Avaliação |
| --- | --- | --- |
| Cérebro | Python 3.11 e NumPy | Primeiro candidato a protótipo, com equivalência do comportamento. |
| Física e movimento | Python | Candidato secundário, condicionado a medições. |
| Desenho e janelas | PySide6 e Qt | Manter no início. Boa parte já executa em código nativo. |
| Integrações Windows | PyWin32 e WinRT | Migrar apenas se houver gargalo comprovado. |
| Android | Java e Python compartilhado via Chaquopy | Avaliar à parte, com ponte JNI e build por arquitetura. |
| Empacotamento Windows | PyInstaller e NSIS | Continua viável em uma arquitetura híbrida. |

- [Motor neural](../brain/pestinha/core/nervous_system.py). `step()` e `_substep()` avançam a rede em subpassos de 1 ms. Há operações NumPy eficientes e passagens repetidas pelo interpretador Python.
- [Aplicação](../bolha/app.py). O laço de 16 ms consulta interações, atualiza a simulação e sincroniza o desenho. Ajustes de frequência podem reduzir CPU mesmo em Python.
- [Física](../brain/pestinha/core/physics.py) e [movimento](../bolha/motion.py). Candidatos secundários para cálculos frequentes de pose, movimento e física.
- [Personagem](../bolha/character.py), [janela](../bolha/pet.py) e [cena](../bolha/scene.py). O desenho Qt já é nativo. Reescrever essa área tem risco maior e prioridade menor.

### Medições históricas

| Cenário | Evidência | Limite |
| --- | --- | --- |
| Windows 0.5.0 | RSS de 78,54–81,03 MiB e cérebro p95 de 5,61–6,06 ms. | Runner de CI, fora da versão atual. |
| Windows, snapshot da 0.3.0 | RSS de cerca de 85,26–85,35 MiB e CPU de cerca de 2,01% da máquina. | Ensaio curto, em hardware e configuração diferentes. |

A linha de base do experimento deve usar a mesma versão, equipamento e cenário. O documento não fixa uma economia percentual de RAM.

## Arquitetura híbrida

| Camada | Proposta | Condição |
| --- | --- | --- |
| Interface e eventos | Manter Qt e Python. | Preservar transparência, desenho, menus e integrações. |
| Orquestração | Ajustar a frequência no Python existente. | Separar lógica, desenho e sensores conforme a atividade. |
| Motor neural | Avaliar módulo Rust opcional via PyO3. | Validar a semântica e reduzir transições Python–Rust. |
| Física e animações | Portar funções selecionadas. | Demonstrar benefício no benchmark. |
| Compatibilidade | Manter implementação Python para retorno. | Alternar de forma controlada nos testes. |

[Rust Anything](https://github.com/erkamyaman/rust-anything) pode ajudar a registrar comportamentos, organizar unidades de migração e comparar a implementação com casos previamente registrados. A implementação exige engenharia e revisão. O replay complementa os testes visuais, os testes de sistema e os testes probabilísticos.

### Fases

1. **A · Medição.** Registrar CPU, RSS, tempo de quadros p95 e p99, tempo neural p95 e p99, consumo em repouso e tamanho do pacote na mesma máquina.
2. **B · Protótipo isolado.** Em uma branch experimental, portar uma unidade neural com entradas e saídas controladas. Preservar o instalador oficial.
3. **C · Ponte Python e Rust.** Experimentar PyO3 com maturin, ou equivalente. Processar o máximo de subpassos por chamada para reduzir o custo da ponte.
4. **D · Comparação.** Validar saídas, aprendizado, memória persistida, desempenho e estabilidade contra o motor Python.
5. **E · Laço da aplicação.** Testar frequência visual adaptativa em repouso, preservando a frequência neural, os gestos e a fluidez.
6. **F · Expansão condicionada.** Considerar física, expressões e Android somente após obter resultados positivos.

O cérebro tem aleatoriedade e aprendizado. Fixar sementes e entradas para casos determinísticos e complementá-los com tolerâncias numéricas e testes estatísticos e de persistência.

## Benchmarks e aceitação

Medir cenários equivalentes após aquecimento.

| Cenário | Medições |
| --- | --- |
| Repouso visível | CPU, RSS, ativações de timers, tempo de quadro e fluidez. |
| Movimento e perseguição | CPU, p95 e p99 dos quadros e estabilidade física. |
| Carinho, clique, arrasto e arremesso | Latência, eventos, colisões e expressões. |
| Cérebro e aprendizado | Tempo por ciclo, divergências e integridade do aprendizado. |
| Notebook, brinquedos, reações e bateria | Memória, integração, threads e recuperação. |
| Longa duração e atualização | Vazamentos, travamentos, persistência, migração e reversão. |

Aprovar somente com ganho reproduzível em um gargalo real e sem regressão relevante nos outros cenários. Acompanhar CPU média e pico, RSS total e tamanho do executável e da instalação. Preservar os **470 neurônios**, as interações e os dados salvos, ou demonstrar uma migração confiável e reversível. Testar inicialização, suspensão, múltiplos monitores, atualização automática, rollback e erros de execução. Exigir testes de unidade e integração, inspeção visual em Qt, CI Windows x64 e verificações pertinentes para Android.

| Risco | Prevenção |
| --- | --- |
| Ganho insuficiente ou regressão | Medir antes e depois e descartar o porte sem benefício. |
| Mudança neural | Controlar sementes e validar dinâmica, aprendizado e persistência. |
| Custo de FFI | Processar lotes e evitar chamadas por neurônio. |
| Distribuição | Automatizar builds e verificar DLL/PYD, licenças e rollback. |
| Diferenças entre plataformas | Manter builds e testes independentes. |
| Licenciamento | Respeitar a GPL-3.0-or-later e atribuir dependências e ferramentas. |

## Versão e publicação

| Marco | Decisão |
| --- | --- |
| Antes de 1.0.0.0 | Priorizar refatoração estável, testes e perfis de desempenho. |
| Candidata 1.0.0.0 | Considerar Rust híbrido se benchmarks e regressões forem aprovados. |
| Depois | Expandir apenas quando houver justificativa e benefício. |
| Ganho sem comprovação | Manter o motor atual e registrar a decisão técnica. |

A numeração é indicativa, sem data de lançamento ou inclusão garantida. O documento original identificou o formato de três componentes da 0.5.9 como um ponto a adaptar em validadores, atualizador, CI, instaladores, testes, tags e metadados. Veja o [contrato atual do build e da atualização](BUILD.md).

A apresentação pública pode dizer que o projeto estuda otimizar partes do motor com Rust e testes comparativos para reduzir o consumo de recursos, preservando personalidade, aprendizado e funcionalidades. A publicação depende de benefício comprovado.

### Referências do documento original

- [Repositório](https://github.com/kuky13/bolha), [dependências Windows](../requirements.txt) e [build nativo](../scripts/build_native.py).
- [Validação 0.5.0](VALIDATION-0.5.0.md) e [relatório de validação nativa](VALIDATION-NATIVE.md).
- [Documentação do Rust Anything](https://github.com/erkamyaman/rust-anything).

A análise original usou código e documentação públicos. As métricas acima são históricas e não são benchmarks da 0.5.9.
