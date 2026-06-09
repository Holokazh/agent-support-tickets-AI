from typing import Optional, Dict, Any, List
from app.database import get_db_cursor

def get_all_customers() -> List[Dict[str, Any]]:
    """
    Récupère la liste de tous les clients en base de données.
    """
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, nom, email, statut FROM clients ORDER BY id ASC;")
        rows = cursor.fetchall()

        customers = []
        for row in rows:
            customers.append({
                "id": row[0],
                "nom": row[1],
                "email": row[2],
                "statut": row[3]
            })
        return customers

def get_customer_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Recherche un client en base de données par son adresse email.

    Args:
        email: L'adresse e-mail recherchée.

    Returns:
        Un dictionnaire contenant les informations du client (id, nom, email, statut)
        ou None si aucun client ne correspond.
    """
    # On utilise notre context manager sécurisé pour obtenir un curseur
    with get_db_cursor() as cursor:
        # Exécution de la requête SQL paramétrée (le %s évite les injections SQL)
        cursor.execute(
            "SELECT id, nom, email, statut FROM clients WHERE email = %s;",
            (email,)
        )
        # fetchone() récupère la première ligne de résultat
        row = cursor.fetchone()

        # Si une ligne est trouvée, on la formate en dictionnaire Python propre
        if row:
            return {
                "id": row[0],
                "nom": row[1],
                "email": row[2],
                "statut": row[3]
            }
        # Sinon, on renvoie None
        return None
