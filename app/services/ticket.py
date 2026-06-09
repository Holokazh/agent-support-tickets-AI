from app.database import get_db_cursor
from typing import List, Dict, Any

def get_all_tickets() -> List[Dict[str, Any]]:
    """
    Récupère la liste de tous les tickets de support en base de données.
    Effectue une jointure pour inclure les détails du client.
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT t.id, t.client_id, c.nom, c.email, t.message, t.statut
            FROM tickets t
            JOIN clients c ON t.client_id = c.id
            ORDER BY t.id DESC;
        """)
        rows = cursor.fetchall()

        tickets = []
        for row in rows:
            tickets.append({
                "id": row[0],
                "client_id": row[1],
                "client_nom": row[2],
                "client_email": row[3],
                "message": row[4],
                "statut": row[5]
            })
        return tickets

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
