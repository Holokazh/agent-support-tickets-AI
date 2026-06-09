from typing import List, Dict, Any
from app.database import get_db_cursor

def get_all_orders() -> List[Dict[str, Any]]:
    """
    Récupère l'intégralité des commandes de la base.
    Effectue une jointure pour inclure le nom du client.
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT o.id, o.client_id, c.nom, o.produit, o.prix, o.statut
            FROM commandes o
            JOIN clients c ON o.client_id = c.id
            ORDER BY o.id DESC;
        """)
        rows = cursor.fetchall()

        orders = []
        for row in rows:
            orders.append({
                "id": row[0],
                "client_id": row[1],
                "client_nom": row[2],
                "produit": row[3],
                "prix": float(row[4]),
                "statut": row[5]
            })
        return orders

def get_customer_orders(client_id: int) -> List[Dict[str, Any]]:
    """
    Récupère l'historique des commandes d'un client spécifique.

    Args:
        client_id: L'identifiant du client en base.

    Returns:
        Une liste de dictionnaires représentant ses commandes.
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, client_id, produit, prix, statut FROM commandes WHERE client_id = %s;",
            (client_id,)
        )
        # fetchall() récupère toutes les lignes de résultats
        rows = cursor.fetchall()

        orders = []
        for row in rows:
            orders.append({
                "id": row[0],
                "client_id": row[1],
                "produit": row[2],
                "prix": float(row[3]),  # Conversion du type NUMERIC Postgres en float Python
                "statut": row[4]
            })
        return orders

def update_order_status(order_id: int, new_status: str) -> bool:
    """
    Met à jour le statut d'une commande dans la base de données.

    Args:
        order_id: L'identifiant de la commande.
        new_status: Le nouveau statut (ex: 'REMBOURSÉ').

    Returns:
        True si la commande a bien été mise à jour, False sinon.
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            "UPDATE commandes SET statut = %s WHERE id = %s;",
            (new_status, order_id)
        )
        # cursor.rowcount contient le nombre de lignes affectées par la requête UPDATE
        return cursor.rowcount > 0
