import json
import sys
from datetime import datetime
import os
#-------------------------------------------------------------------
# Configurações
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVENTS_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "timeline_events.json"))
PERIODS_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "timeline_periods.json"))
MIN_YEAR = -100000
MAX_YEAR = datetime.now().year + 5

# =========================
# Utilidades
# =========================
def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERRO] Falha ao carregar {path}: {e}")
        sys.exit(1)

def error(msg):
    print(f"[ERRO] {msg}")
    sys.exit(1)

def warning(msg):
    print(f"[AVISO] {msg}")




# =========================
# Validação de Eventos
# =========================

def validate_events(events_data):
    if "events" not in events_data:
        error("Arquivo de eventos não contém a chave 'events'")

    events = events_data["events"]
    event_ids = set()

    for event_id, event in events.items():
        # ID consistente
        if event_id != event.get("id"):
            error(f"ID inconsistente no evento {event_id}")

        if event_id in event_ids:
            error(f"Evento duplicado: {event_id}")
        event_ids.add(event_id)

        # Data válida (ISO 8601)
        date_str = event.get("date")
        if not isinstance(date_str, str):
            error(f"Evento {event_id} deve possuir 'date' como string ISO")

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            error(
                f"Evento {event_id} possui 'date' inválida. Use YYYY-MM-DD"
            )

        year = date_obj.year
        if year < MIN_YEAR or year > MAX_YEAR:
            warning(
                f"Evento {event_id} possui data fora do intervalo esperado"
            )

        # Importance
        importance = event.get("importance")
        if not isinstance(importance, int) or not (1 <= importance <= 10):
            error(f"Evento {event_id} possui 'importance' inválida (1–10)")

        # Categories e tags
        if "categories" in event and not isinstance(event["categories"], list):
            error(f"Evento {event_id} possui 'categories' inválido")

        if "tags" in event and not isinstance(event["tags"], list):
            error(f"Evento {event_id} possui 'tags' inválido")

    return event_ids



# =========================
# Validação de Períodos
# =========================

def validate_periods(periods_data, valid_event_ids):
    if "periods" not in periods_data:
        error("Arquivo de períodos não contém a chave 'periods'")

    periods = periods_data["periods"]

    if "root" not in periods_data:
        error("Arquivo de períodos não define 'root'")

    if periods_data["root"] not in periods:
        error("Período raiz não existe no dicionário")

    period_ids = set()

    for period_id, period in periods.items():
        # ID consistente
        if period_id != period.get("id"):
            error(f"ID inconsistente no período {period_id}")

        if period_id in period_ids:
            error(f"Período duplicado: {period_id}")
        period_ids.add(period_id)

        start = period.get("startYear")
        end = period.get("endYear")

        if not isinstance(start, int) or not isinstance(end, int):
            error(f"Período {period_id} possui datas inválidas")

        if start >= end:
            error(f"Período {period_id} possui startYear >= endYear")

        children = period.get("children", [])
        if not isinstance(children, list):
            error(f"Período {period_id} possui 'children' inválido")

        for child_id in children:
            # Child pode ser evento ou período
            if child_id in valid_event_ids:
                event = events_data["events"].get(child_id)

                date_str = event.get("date")
                if not isinstance(date_str, str):
                    error(f"Evento {child_id} não possui 'date' válida")
                    continue

                try:
                    event_year = datetime.fromisoformat(date_str).year
                except ValueError:
                    error(
                        f"Evento {child_id} possui 'date' em formato inválido: {date_str}"
                    )
                    continue

                if not (start <= event_year <= end):
                    warning(
                        f"Evento {child_id} ({event_year}) fora do intervalo "
                        f"do período {period_id} ({start}–{end})"
                    )

            elif child_id in periods:
                child_period = periods[child_id]

                if not (
                    start <= child_period["startYear"]
                    and child_period["endYear"] <= end
                ):
                    warning(
                        f"Sub-período {child_id} extrapola intervalo de {period_id}"
                    )

            else:
                error(f"Child inexistente '{child_id}' em período {period_id}")

    return period_ids

#-------------------------------------------------------------------
# Execução principal
if __name__ == "__main__":
    print("Validando dados da timeline...\n")

    events_data = load_json(EVENTS_FILE)
    periods_data = load_json(PERIODS_FILE)

    valid_event_ids = validate_events(events_data)
    validate_periods(periods_data, valid_event_ids)

    print("\nValidação concluída com sucesso.")