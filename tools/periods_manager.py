import json
import sys
from pathlib import Path
from InquirerPy import inquirer

# ======================================================
# Configuração
# ======================================================

PERIODS_FILE = Path(__file__).parent.parent / "data" / "timeline_periods.json"
EVENTS_FILE = Path(__file__).parent.parent / "data" / "timeline_events.json"
CONTENT_DIR = Path(__file__).parent.parent / "data" / "content" / "periods"


# ======================================================
# Utilitários
# ======================================================

def error(msg):
    print(f"[ERRO] {msg}")
    sys.exit(1)

def info(msg):
    print(f"[OK] {msg}")

def load_json(path):
    if not path.exists():
        error(f"Arquivo não encontrado: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ======================================================
# CRUD de Períodos
# ======================================================

# Criar
def create_period(periods):
    period_id = input("ID do período: ").strip()
    if not period_id:
        error("ID é obrigatório")

    if period_id in periods:
        error("Período já existe")

    title = input("Título: ").strip()
    start = input("Ano inicial: ").strip()
    end = input("Ano final: ").strip()
    importance = input("Importância (1–10): ").strip()

    if not start.lstrip("-").isdigit() or not end.lstrip("-").isdigit():
        error("Anos devem ser números")

    if not importance.isdigit() or not (1 <= int(importance) <= 10):
        error("Importância inválida")

    categories = input("Categorias (separadas por vírgula): ").strip()
    tags = input("Tags (separadas por vírgula): ").strip()

    categories_list = [c.strip() for c in categories.split(",")] if categories else []
    tags_list = [t.strip() for t in tags.split(",")] if tags else []

    content_file = f"periods/{period_id}.html"

    periods[period_id] = {
        "id": period_id,
        "title": title,
        "startYear": int(start),
        "endYear": int(end),
        "children": [],
        "importance": int(importance),
        "categories": categories_list,
        "tags": tags_list,
        "contentFile": content_file
    }

    # 🔥 Criar HTML automaticamente
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    html_path = CONTENT_DIR / f"{period_id}.html"

    html_template = """<article>
  <h1></h1>

  <img src="" alt="">

  <p>
    
  </p>
</article>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_template)

    info(f"Período '{period_id}' criado com sucesso")
    info(f"Arquivo HTML criado em: {html_path}")
    print()


# Listar
def list_periods(periods):
    if not periods:
        print("Nenhum período cadastrado.")
        return

    print("\nPeríodos cadastrados:\n")
    for pid, p in periods.items():
        print(f"- {pid} | {p['startYear']}–{p['endYear']} | {p['title']}")
    print()
    main()

# Visualizar
def view_period(periods):
    if not periods:
        error("Nenhum período para visualizar")

    period_id = inquirer.select(
        message="Selecione um período",
        choices=[
            {"name": f"{pid} | {p['startYear']}–{p['endYear']} | {p['title']}", "value": pid}
            for pid, p in periods.items()
        ],
    ).execute()

    print("\nDetalhes do período:\n")
    print(json.dumps(periods[period_id], indent=2, ensure_ascii=False))
    print()
    main()


# Editar
def edit_period(periods):
    if not periods:
        error("Nenhum período para editar")

    period_id = inquirer.select(
        message="Selecione um período para editar",
        choices=[
            {"name": f"{pid} | {p['startYear']}–{p['endYear']} | {p['title']}", "value": pid}
            for pid, p in periods.items()
        ],
    ).execute()

    period = periods[period_id]

    print("\nPressione ENTER para manter o valor atual.\n")

    new_title = input(f"Título [{period['title']}]: ").strip()
    if new_title:
        period["title"] = new_title

    new_start = input(f"Ano inicial [{period['startYear']}]: ").strip()
    if new_start:
        if not new_start.lstrip("-").isdigit():
            error("Ano inicial inválido")
        period["startYear"] = int(new_start)

    new_end = input(f"Ano final [{period['endYear']}]: ").strip()
    if new_end:
        if not new_end.lstrip("-").isdigit():
            error("Ano final inválido")
        period["endYear"] = int(new_end)

    new_importance = input(f"Importância [{period['importance']}]: ").strip()
    if new_importance:
        if not new_importance.isdigit() or not (1 <= int(new_importance) <= 10):
            error("Importância inválida")
        period["importance"] = int(new_importance)

    new_categories = input(f"Categorias {period.get('categories', [])}: ").strip()
    if new_categories:
        period["categories"] = [c.strip() for c in new_categories.split(",")]

    new_tags = input(f"Tags {period.get('tags', [])}: ").strip()
    if new_tags:
        period["tags"] = [t.strip() for t in new_tags.split(",")]

    info(f"Período '{period_id}' atualizado com sucesso")
    print()


# Deletar
def delete_period(periods):
    if not periods:
        error("Nenhum período para deletar")

    period_ids = inquirer.checkbox(
        message="Selecione períodos para deletar",
        choices=[
            {"name": f"{pid} | {p['title']}", "value": pid}
            for pid, p in periods.items()
        ],
    ).execute()

    if not period_ids:
        info("Nenhum período selecionado")
        return

    confirm = inquirer.confirm(
        message=f"Tem certeza que deseja deletar {len(period_ids)} período(s)?",
        default=False,
    ).execute()

    if not confirm:
        info("Operação cancelada")
        return

    for pid in period_ids:

        # 🔥 Deletar HTML correspondente
        html_path = CONTENT_DIR / f"{pid}.html"
        if html_path.exists():
            html_path.unlink()
            info(f"Arquivo HTML removido: {html_path}")

        # 🔥 Remover do JSON
        del periods[pid]
        info(f"Período '{pid}' removido")

    print()

# ======================================================
# Link Event x Period
# ======================================================

def link_event_to_period(periods, events):
    if not periods:
        error("Nenhum período disponível")

    if not events:
        error("Nenhum evento disponível")

    period_id = inquirer.select(
        message="Selecione o período",
        choices=[
            {"name": f"{pid} | {p['title']}", "value": pid}
            for pid, p in periods.items()
        ],
    ).execute()

    period = periods[period_id]

    available_events = [
        eid for eid in events if eid not in period["children"]
    ]

    if not available_events:
        info("Nenhum evento disponível para vincular")
        return

    event_ids = inquirer.checkbox(
        message="Selecione eventos para vincular",
        choices=[
            {"name": f"{eid} | {events[eid]['title']}", "value": eid}
            for eid in available_events
        ],
    ).execute()

    for eid in event_ids:
        period["children"].append(eid)
        info(f"Evento '{eid}' vinculado ao período '{period_id}'")

    print()


# ======================================================
# Menu principal
# ======================================================

def main():
    periods_data = load_json(PERIODS_FILE)
    events_data = load_json(EVENTS_FILE)

    periods = periods_data.get("periods", {})
    events = events_data.get("events", {})

    action = inquirer.select(
        message="O que deseja fazer?",
        choices=[
            {"name": "Criar período", "value": "create"},
            {"name": "Listar períodos", "value": "list"},
            {"name": "Visualizar período", "value": "view"},
            {"name": "Editar período", "value": "edit"},
            {"name": "Vincular eventos a período", "value": "link"},
            {"name": "Deletar períodos", "value": "delete"},
            {"name": "Sair", "value": "exit"},
        ],
    ).execute()

    if action == "create":
        create_period(periods)
        save_json(PERIODS_FILE, periods_data)

    elif action == "list":
        list_periods(periods)

    elif action == "view":
        view_period(periods)

    elif action == "edit":
        edit_period(periods)
        save_json(PERIODS_FILE, periods_data)

    elif action == "link":
        link_event_to_period(periods, events)
        save_json(PERIODS_FILE, periods_data)

    elif action == "delete":
        delete_period(periods)
        save_json(PERIODS_FILE, periods_data)

    else:
        sys.exit(0)


# ======================================================
# Entry point
# ======================================================

if __name__ == "__main__":
    main()