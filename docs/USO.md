# Usar a Bolha

Este guia reúne os passos práticos para a edição de computador. Para o Android,
consulte o [guia próprio](../android/README.md). A página de [versões](https://github.com/kuky13/bolha/releases/latest)
sempre aponta para a publicação mais recente; confira as notas antes de atualizar.

## Abrir pelo código

Com Python 3.11, na pasta do repositório:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

No Linux, use `python3.11` em vez de `py -3.11` e `.venv/bin/python` no lugar
de `.venv\Scripts\python`. O desenho usa Qt/PySide6. Para instalar o app no
Windows, baixe o instalador x64 em [Releases](https://github.com/kuky13/bolha/releases/latest).

## Gestos e menus

| Gesto ou menu | O que acontece |
|---|---|
| Mover o ponteiro de um lado para o outro sobre a Bolha | Faz carinho. |
| Manter pressionado | Segura; ela pode ficar irritada gradualmente. |
| Arrastar e soltar parada | Solta no local; ela cai e quica. |
| Arrastar e soltar em movimento | Arremessa na direção do movimento. |
| Rodinha do mouse | Gira a Bolha ou o objeto. |
| Botão direito | Abre o menu e a Central da Bolha. |
| **Interagir → Dormir um pouco** | Pede uma pausa para dormir. |
| **Brincar → Mostrar / guardar brinquedo** | Mostra ou recolhe o brinquedo selecionado. |
| **Brincar → Jogar pingue-pongue** | Inicia uma partida com o brinquedo. |
| **Central → Bolha → Brinquedo** | Alterna amendoim e bolinha. |
| **Ctrl + Alt + Shift + B** | Pausa ou retoma a Bolha. |

Passar o ponteiro de baixo para cima sobre o brinquedo faz com que ele pule.
Quando o sensor de cursor está ativo, aproximar o ponteiro também pode empurrá-lo.
O pingue-pongue usa o ponteiro para rebater; a partida termina aos cinco pontos.
No computador, a brincadeira opcional de perseguir e mastigar o cursor vem
desligada. Mover ou clicar restaura o cursor imediatamente.

Em **Central → Testar**, as prévias de expressão e os ensaios de atividade usam
uma cópia temporária do perfil. Eles não gravam aprendizado na memória original.

Na seção **Central → App → Integrações do Windows**, use a lista **Mostrar na
bandeja** para escolher os ícones dos periféricos. Aparelhos novos aparecem
automaticamente. Passe o ponteiro sobre um ícone para ver o nome e a carga e
clique para abrir o painel de baterias. O Windows controla quais ícones ficam
visíveis perto do relógio ou na área de ícones ocultos.

No painel de baterias, use **Ocultar** ao lado de um dispositivo para tirá-lo
da lista. Para recuperar o item, abra **Ocultos** e clique em **Mostrar**.
Essa escolha fica salva e é independente da seleção de ícones da bandeja.
Um raio no ícone do dispositivo, no painel ou na bandeja, indica que o
periférico informou que a bateria está carregando.

## Perfil, privacidade e rede

No Windows, configurações e dados ficam em `%APPDATA%\bolha`; no Linux, em
`~/.config/bolha`. O aprendizado fica dentro de `brain`. Atualizar ou reinstalar
preserva o perfil. Os formatos
legados têm migrações específicas; consulte o [histórico de validação](VALIDATION-NATIVE.md)
antes de tentar copiar dados entre instalações. Evite editar ou apagar arquivos
do perfil enquanto a Bolha estiver aberta.

As leituras opcionais do programa ativo, inatividade, cursor e geometria de
janelas podem ser desligadas separadamente. A Bolha não captura a tela, lê
títulos ou conteúdo de janelas, texto digitado, chats ou arquivos, nem envia
memória a servidores. O cérebro e a interface rodam no mesmo processo local.

As reações são GIFs originais, gerados e exibidos em memória. A Central permite
desligá-las. Clique com o botão direito sobre o GIF para consultar os créditos
e a licença. As atualizações usam o GitHub nas edições instaladas.

Na edição instalada, o atualizador verifica tamanho e SHA-256 do arquivo
baixado, salva o aprendizado antes da troca e só limpa arquivos temporários
depois que a nova versão inicia com saúde. Rodar `main.py` pelo código não
consulta atualizações automaticamente. O instalador Windows não tem assinatura digital: a verificação de
hash confirma integridade em relação à publicação consultada, mas não prova a
identidade do publicador. O relatório de [compilação e recuperação](BUILD.md)
descreve o processo e seus limites.

## Recursos e histórico

A Bolha tem expressões, brinquedos, bilhetes, cartazes, fogos, atividades e um
painel do cérebro local com 470 neurônios. O cérebro escolhe ações dentro das
permissões configuradas; o notebook é uma brincadeira e não executa comandos no
computador. A aba **Testar** oferece prévias e ensaios temporários.

Para detalhes de mudanças e evidências, consulte as [notas](RELEASE.md), a
[auditoria da série 0.5.4](AUDITORIA-0.5.4.md) e a [validação nativa](VALIDATION-NATIVE.md).
Os documentos antigos identificam explicitamente a versão e o ambiente a que
seus resultados pertencem; não os trate como validação da versão atual.
