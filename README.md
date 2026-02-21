# Timeline Project

Projeto experimental que propõe uma linha do tempo navegável da história humana, estruturada em períodos e eventos interconectados, permitindo exploração progressiva por zoom temporal, similar ao conceito de navegação espacial aplicado ao tempo.

O foco principal é arquitetura de dados, consistência temporal, escalabilidade e organização estrutural.

---

## Objetivo

Criar uma base histórica estruturada que permita:

- Navegação hierárquica do macro para o micro (eras → períodos → eventos)
- Associação de eventos a múltiplos períodos sem duplicação
- Validação automática de consistência temporal
- Estrutura escalável para grande volume de dados
- Interface web interativa baseada em zoom e nível de detalhe

---

# Arquitetura Geral

O sistema é dividido em dois blocos principais:

1. Camada de Dados e Gerenciamento (Managers em Python)
2. Camada de Visualização Web (HTML, CSS e JavaScript)

---

# Modelagem Conceitual

## Eventos

Entidades atômicas que possuem:

- ID único
- Título
- Data absoluta (ISO YYYY-MM-DD)
- Importância (1–10)
- Categorias
- Tags
- Arquivo HTML de conteúdo associado

Eventos representam pontos fixos no tempo.

---

## Períodos

Agrupadores temporais com:

- ID único
- Título
- Ano inicial
- Ano final
- Importância (1–10)
- Categorias
- Tags
- Lista de filhos (eventos ou sub-períodos)
- Arquivo HTML de conteúdo associado

Períodos podem conter:

- Eventos
- Sub-períodos

Isso transforma a timeline em uma estrutura hierárquica e parcialmente em grafo.

---

# Funcionalidades Internas (Managers)

Localizados na pasta `tools/`.

---

## event_manager.py

Responsável pelo CRUD completo de eventos.

### Funcionalidades

- Criar evento
  - Validação de ID único
  - Validação de data ISO
  - Validação de importance (1–10)
  - Criação automática do HTML base
  - Inserção no JSON principal

- Listar eventos
- Visualizar evento
- Editar evento
  - Atualização opcional de campos
  - Mantém valores anteriores se campo vazio
- Deletar evento
  - Remove evento do JSON
  - Remove arquivo HTML correspondente
  - Remove automaticamente referências em períodos

---

## periods_manager.py

Responsável pelo CRUD completo de períodos.

### Funcionalidades

- Criar período
  - Validação de ID único
  - Validação de intervalo numérico
  - Validação de importance
  - Criação automática de HTML base
  - Inicialização com lista de filhos vazia

- Listar períodos
- Visualizar período
- Editar período
- Deletar período
  - Remove JSON
  - Remove HTML associado
- Vincular eventos a períodos
  - Seleção interativa
  - Atualização da lista children

---

## validate_data.py

Validador estrutural do sistema.

### Validações realizadas

- Existência das chaves "events" e "periods"
- Consistência entre ID do dicionário e campo interno id
- Verificação de duplicidade
- Validação de formato de data ISO
- Verificação de importance dentro do intervalo permitido
- Verificação de intervalo válido (startYear < endYear)
- Verificação de integridade dos children
- Aviso se evento estiver fora do intervalo do período
- Aviso se sub-período extrapolar intervalo do pai

Garante integridade estrutural antes da execução web.

---

# Funcionalidades da Aplicação Web

---

## Renderização da Timeline

- Conversão de data ISO para ano numérico
- Cálculo automático de limites absolutos
- Conversão ano → porcentagem relativa
- Renderização dinâmica de eventos e períodos

---

## Zoom Temporal

- Zoom baseado em scroll do mouse
- Zoom centrado na posição do cursor
- Limite mínimo e máximo de zoom
- Atualização dinâmica da régua

---

## Arraste Horizontal

- Drag com mouse
- Cálculo proporcional ao nível de zoom
- Limite com margem virtual configurável
- Re-renderização suave

---

## Level of Detail (LoD)

Sistema de visibilidade condicional baseado em:

- Nível de zoom
- Importância do evento/período

Eventos de baixa importância aparecem apenas em zoom mais profundo.

---

## Régua Temporal

- Divisões dinâmicas baseadas no range atual
- Exibição formatada:
  - Milhões (Mi)
  - Bilhões (Bi)
  - Conversão automática de anos negativos para a.C.

---

## Busca e Filtro

- Normalização de texto (remoção de acentos)
- Filtro por:
  - Título
  - Data
  - Tags
  - Categorias
- Renderização dinâmica de cards
- Exibição de mensagem de “nenhum resultado”

---

## Cards de Resultado

Cada card exibe:

- Tipo (Evento ou Período)
- Título
- Data formatada
- Imagem extraída automaticamente do HTML do conteúdo

---

## Painel de Conteúdo

- Abertura dinâmica via função centralizada
- Carregamento de HTML externo
- Cabeçalho com título
- Corpo com scroll interno
- Botão de fechamento
- Sistema unificado para eventos e períodos

---

## Transições e Renderização Suave

- Uso de classes `.visible`
- Animações via CSS
- Remoção após `transitionend`
- Atualização incremental de elementos

---

# Funcionalidades Implementadas

- Conversão automática de ano negativo para formato a.C.
- CRUD completo de eventos e períodos
- Remoção automática de referências ao deletar evento
- Validação estrutural completa
- Sistema de LoD
- Régua dinâmica
- Zoom centrado no cursor
- Drag com margem dinâmica
- Painel de conteúdo unificado
- Extração automática de imagem para cards
- Filtro de busca textual
- Estrutura modular de dados

---

# Funcionalidades Planejadas

- Datas parciais (ano somente)
- Datas imprecisas (intervalo ou margem de erro)
- Destaque visual sincronizado Timeline ↔ Card
- Sistema de favoritos
- Ordenação de cards (nome, data, importância)
- Refinamento do validador de datas
- Melhorias de UI e responsividade

1. Implementaria escala logarítmica
2. Mudaria LoD para depender de intervalo visível em anos
3. Criaria sistema de lanes para anti-colisão
4. Faria zoom exponencial