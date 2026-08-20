from uuid import uuid4

def new_ticket_id() -> str:
    return f"TKT-{uuid4().hex[:8].upper()}"