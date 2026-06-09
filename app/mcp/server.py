from mcp.server.fastmcp import FastMCP

# Import de nos services métier
from app.services.customer import get_customer_by_email
from app.services.order import get_customer_orders, update_order_status
from app.services.ticket import update_ticket_status
from app.services.voucher import generate_refund_voucher

# Initialisation du serveur MCP avec un nom pour l'application
mcp = FastMCP("AST AI CRM Tools")

# -------------------------------------------------------------
# DÉCLARATION DES OUTILS MCP
# -------------------------------------------------------------

@mcp.tool()
def fetch_customer_info(email: str) -> str:
    """
    Récupère les informations d'un client à partir de son email (id, nom, email, statut).
    """
    print(f"[MCP Outil] -> fetch_customer_info(email='{email}')")
    customer = get_customer_by_email(email)
    if customer:
        return f"Client trouvé : ID={customer['id']}, Nom={customer['nom']}, Statut={customer['statut']}"
    return f"Aucun client trouvé pour l'email '{email}'."

@mcp.tool()
def fetch_customer_orders(client_id: int) -> str:
    """
    Récupère toutes les commandes d'un client à partir de son client_id.
    Renvoie la liste des produits, leur prix et leur statut de livraison (LIVRÉ, EN_COURS, RETARDÉ, REMBOURSÉ).
    """
    print(f"[MCP Outil] -> fetch_customer_orders(client_id={client_id})")
    orders = get_customer_orders(client_id)
    if not orders:
        return f"Aucune commande trouvée pour le client ID {client_id}."

    result = []
    for order in orders:
        result.append(
            f"Commande #{order['id']} : {order['produit']} - Prix: {order['prix']}€ - Statut: {order['statut']}"
        )
    return "\n".join(result)

@mcp.tool()
def modify_order_status(order_id: int, new_status: str) -> str:
    """
    Modifie le statut d'une commande (ex: passer de 'RETARDÉ' à 'REMBOURSÉ').
    Les valeurs de statut valides sont : 'LIVRÉ', 'EN_COURS', 'RETARDÉ', 'REMBOURSÉ'.
    """
    print(f"[MCP Outil] -> modify_order_status(order_id={order_id}, new_status='{new_status}')")
    valid_statuses = ['LIVRÉ', 'EN_COURS', 'RETARDÉ', 'REMBOURSÉ']
    if new_status not in valid_statuses:
        return f"Erreur : Statut '{new_status}' invalide. Les statuts valides sont : {valid_statuses}"

    success = update_order_status(order_id, new_status)
    if success:
        return f"Le statut de la commande #{order_id} a bien été mis à jour à '{new_status}'."
    return f"Échec : aucune commande trouvée avec l'ID #{order_id}."

@mcp.tool()
def create_refund_voucher(client_id: int, amount: float) -> str:
    """
    Génère un bon d'achat de dédommagement d'un montant spécifique pour le client.
    Insère le code en base et crée le fichier coupon.
    """
    print(f"[MCP Outil] -> create_refund_voucher(client_id={client_id}, amount={amount})")
    try:
        voucher_code = generate_refund_voucher(client_id, amount)
        return f"Bon d'achat de {amount}€ généré avec succès. Code : {voucher_code}."
    except Exception as e:
        return f"Erreur lors de la génération du bon d'achat : {e}"

@mcp.tool()
def resolve_ticket(ticket_id: int) -> str:
    """
    Met à jour le statut d'un ticket de support à 'RÉSOLU'.
    """
    print(f"[MCP Outil] -> resolve_ticket(ticket_id={ticket_id})")
    success = update_ticket_status(ticket_id, "RÉSOLU")
    if success:
        return f"Le ticket #{ticket_id} a bien été mis à jour au statut 'RÉSOLU'."
    return f"Échec : aucun ticket trouvé avec l'ID #{ticket_id}."
