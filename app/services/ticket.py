from app.database import get_db_cursor

def update_ticket_status(ticket_id: int, new_status: str) -> bool:
    """
    Met à jour le statut d'un ticket de support (ex: 'RÉSOLU').

    Args:
        ticket_id: L'identifiant du ticket.
        new_status: Le nouveau statut (ex: 'RÉSOLU').

    Returns:
        True si le ticket a bien été mis à jour, False sinon.
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            "UPDATE tickets SET statut = %s WHERE id = %s;",
            (new_status, ticket_id)
        )
        return cursor.rowcount > 0
