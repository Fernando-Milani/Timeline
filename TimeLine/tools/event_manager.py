import json
import sys
from pathlib import Path
from datetime import datetime
from InquirerPy import inquirer

# ======================================================
# Configuração
# ======================================================

DATA_FILE = Path(__file__).parent.parent / "data" / "timeline_events.json"
CONTENT_EVENTS_DIR = Path(__file__).parent.parent / "data" / "content" /"events"

# ======================================================
# Utilitários
# ======================================================

def error(msg):
    print(f"[ERRO] {msg}")
    sys.exit(1)

def info(msg):
    print(f"[OK] {msg}")

def load_events():
    if not DATA_FILE.exists():
        error(f"Arquivo não encontrado: {DATA_FILE}")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_events(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def validate_date_ac(date_str):
    parts = date_str.split("-")
    if len(parts) != 4:
        error("Data inválida. Use o formato YYYY-MM-DD ou -AAAA-MM-DD")
    a, year, month, day = parts
    if not (year.lstrip("-").isdigit() and month.isdigit() and day.isdigit()):
        error("Data inválida. Ano, mês ou dia não são números")
    if not (1 <= int(month) <= 12):
        error("Mês inválido")
    if not (1 <= int(day) <= 31):
        error("Dia inválido")

# ======================================================
# Ações CRUD
# ======================================================
# Criar
def create_event(events):
    event_id = input("ID do evento: ").strip()
    if not event_id:
        error("ID é obrigatório")

    if event_id in events:
        error("Evento já existe")

    title = input("Título: ").strip()
    date = input("Data (YYYY-MM-DD): ").strip()
    validate_date_ac(date)

    importance = input("Importância (1–10): ").strip()
    if not importance.isdigit() or not (1 <= int(importance) <= 10):
        error("Importância inválida")

    categories = input("Categorias (separadas por vírgula): ").strip()
    tags = input("Tags (separadas por vírgula): ").strip()

    # Garante que pasta existe
    CONTENT_EVENTS_DIR.mkdir(parents=True, exist_ok=True)

    # Cria HTML base automaticamente
    html_filename = f"{event_id}.html"
    html_path = CONTENT_EVENTS_DIR / html_filename

    html_template = f"""<article>
  <h1>{title}</h1>

  <p>
    Conteúdo inicial do evento {title}.
  </p>

  <p>
    Edite este arquivo para adicionar imagens e texto.
  </p>
</article>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_template)

    # Salva JSON
    events[event_id] = {
        "id": event_id,
        "title": title,
        "date": date,
        "importance": int(importance),
        "categories": [c.strip() for c in categories.split(",") if c.strip()],
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "contentFile": f"events/{html_filename}"
    }

    info(f"Evento '{event_id}' criado com sucesso")
    info(f"Arquivo HTML criado em: {html_path}")

# Listar
def list_events(events):
    if not events:
        print("Nenhum evento cadastrado.")
        return
    print("\nEventos cadastrados:\n")
    for eid, e in events.items():
        print(f"- {eid} | {e['date']} | {e['title']}")
    print()
    main()

# Visualizar
def view_event(events):
    if not events:
        error("Nenhum evento para visualizar")

    event_id = inquirer.select(
        message="Selecione um evento",
        choices=[
            {"name": f"{eid} | {e['date']} | {e['title']}", "value": eid}
            for eid, e in events.items()
        ],
    ).execute()
    print("\nDetalhes do evento:\n")
    print(json.dumps(events[event_id], indent=2, ensure_ascii=False))
    print()
    main()

# Deletar
def delete_events(events):
    if not events:
        error("Nenhum evento para deletar")

    event_ids = inquirer.checkbox(
        message="Selecione eventos para deletar",
        choices=[
            {"name": f"{eid} | {e['title']}", "value": eid}
            for eid, e in events.items()
        ],
    ).execute()

    if not event_ids:
        info("Nenhum evento selecionado")
        return

    confirm = inquirer.confirm(
        message=f"Tem certeza que deseja deletar {len(event_ids)} evento(s)?",
        default=False,
    ).execute()

    if not confirm:
        info("Operação cancelada")
        return

    # Carrega períodos para remover referências
    from pathlib import Path
    import json

    PERIODS_FILE = Path(__file__).parent.parent / "data" / "timeline_periods.json"

    if PERIODS_FILE.exists():
        with open(PERIODS_FILE, "r", encoding="utf-8") as f:
            periods_data = json.load(f)

        periods = periods_data.get("periods", {})

        for pid, period in periods.items():
            if "children" in period:
                period["children"] = [
                    child for child in period["children"]
                    if child not in event_ids
                ]

        with open(PERIODS_FILE, "w", encoding="utf-8") as f:
            json.dump(periods_data, f, indent=2, ensure_ascii=False)

    # Remove eventos
    for eid in event_ids:
        # Remove HTML correspondente
        html_path = CONTENT_EVENTS_DIR / f"{eid}.html"
        if html_path.exists():
            html_path.unlink()
            info(f"Arquivo HTML removido: {html_path}")

        del events[eid]
        info(f"Evento '{eid}' removido")

    print()

# Editar
def edit_event(events):
    if not events:
        error("Nenhum evento para editar")

    event_id = inquirer.select(
        message="Selecione um evento para editar",
        choices=[
            {"name": f"{eid} | {e['date']} | {e['title']}", "value": eid}
            for eid, e in events.items()
        ],
    ).execute()

    event = events[event_id]

    print("\nPressione ENTER para manter o valor atual.\n")

    # ===== Editar título
    new_title = input(f"Título [{event['title']}]: ").strip()
    if new_title:
        event["title"] = new_title

    # ===== Editar data
    new_date = input(f"Data [{event['date']}]: ").strip()
    if new_date:
        validate_date_ac(new_date)
        event["date"] = new_date

    # ===== Editar importance
    new_importance = input(f"Importância [{event['importance']}]: ").strip()
    if new_importance:
        if not new_importance.isdigit() or not (1 <= int(new_importance) <= 10):
            error("Importância inválida")
        event["importance"] = int(new_importance)

    # ===== Editar categorias
    current_categories = ", ".join(event.get("categories", []))
    new_categories = input(f"Categorias [{current_categories}]: ").strip()
    if new_categories:
        event["categories"] = [
            c.strip() for c in new_categories.split(",") if c.strip()
        ]

    # ===== Editar tags
    current_tags = ", ".join(event.get("tags", []))
    new_tags = input(f"Tags [{current_tags}]: ").strip()
    if new_tags:
        event["tags"] = [
            t.strip() for t in new_tags.split(",") if t.strip()
        ]

    # ===== Editar contentRef
    current_content = event.get("contentRef", "")
    new_content = input(f"ContentRef [{current_content}]: ").strip()
    if new_content:
        event["contentRef"] = new_content

    info(f"Evento '{event_id}' atualizado com sucesso")
    print()

# ======================================================
# Menu principal
# ======================================================

def main():
    data = load_events()
    events = data.get("events", {})

    action = inquirer.select(
        message="O que deseja fazer?",
        choices=[
            {"name": "Criar evento", "value": "create"},
            {"name": "Listar eventos", "value": "list"},
            {"name": "Visualizar evento", "value": "view"},
            {"name": "Editar evento", "value": "edit"},
            {"name": "Deletar eventos", "value": "delete"},
            {"name": "Sair", "value": "exit"},
        ],
    ).execute()

    if action == "create":
        create_event(events)
        save_events(data)

    elif action == "list":
        list_events(events)

    elif action == "view":
        view_event(events)

    elif action == "edit":
        edit_event(events)
        save_events(data)


    elif action == "delete":
        delete_events(events)
        save_events(data)

    else:
        sys.exit(0)

# ======================================================
# Entry point
# ======================================================

if __name__ == "__main__":
    main()