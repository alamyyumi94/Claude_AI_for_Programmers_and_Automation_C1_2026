from uuid import uuid4

def new_ticket_id() -> str:
    """
    Generate a new unique ticket ID.
    """
    return f"TKT-{uuid4().hex[:8].upper()}"