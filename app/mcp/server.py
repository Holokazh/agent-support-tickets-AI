import re
from mcp.server.fastmcp import FastMCP

# Import de nos services métier
from app.services.customer import get_customer_by_email
from app.services.order import get_customer_orders, update_order_status
from app.services.ticket import update_ticket_status
from app.services.voucher import generate_refund_voucher
from app.logger import logger

# Initialisation du serveur MCP
mcp = FastMCP("AST AI CRM Tools")

# Regex de validation d'email simple et standard
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# -------------------------------------------------------------
# DÉCLARATION DES OUTILS MCP
# -------------------------------------------------------------

@mcp.tool()
def fetch_customer_info(email: str) -> str:
    """
    Récupère les informations d'un client à partir de son email (id, nom, email, statut).
    """
    email_clean = email.strip()
    logger.info(f"[MCP Outil] fetch_customer_info(email='{email_clean}')")

    if not EMAIL_REGEX.match(email_clean):
        logger.warning(f"[MCP Outil] Email invalide soumis : '{email_clean}'")
        return f"Erreur : L'email '{email_clean}' n'a pas un format valide."

    customer = get_customer_by_email(email_clean)
    if customer:
        return f"Client trouvé : ID={customer['id']}, Nom={customer['nom']}, Statut={customer['statut']}"
    return f"Aucun client trouvé pour l'email '{email_clean}'."

@mcp.tool()
def fetch_customer_orders(client_id: int) -> str:
    """
    Récupère toutes les commandes d'un client à partir de son client_id.
    Renvoie la liste des produits, leur prix et leur statut de livraison.
    """
    logger.info(f"[MCP Outil] fetch_customer_orders(client_id={client_id})")

    if client_id <= 0:
        logger.warning(f"[MCP Outil] ID client invalide soumis : {client_id}")
        return "Erreur : Le client_id doit être un entier strictement supérieur à 0."

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
    logger.info(f"[MCP Outil] modify_order_status(order_id={order_id}, new_status='{new_status}')")

    if order_id <= 0:
        logger.warning(f"[MCP Outil] ID commande invalide soumis : {order_id}")
        return "Erreur : Le order_id doit être un entier strictement supérieur à 0."

    valid_statuses = ['LIVRÉ', 'EN_COURS', 'RETARDÉ', 'REMBOURSÉ']
    if new_status not in valid_statuses:
        logger.warning(f"[MCP Outil] Statut invalide soumis : '{new_status}'")
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
    logger.info(f"[MCP Outil] create_refund_voucher(client_id={client_id}, amount={amount})")

    if client_id <= 0:
        logger.warning(f"[MCP Outil] ID client invalide soumis : {client_id}")
        return "Erreur : Le client_id doit être un entier strictement supérieur à 0."

    if amount <= 0:
        logger.warning(f"[MCP Outil] Montant négatif ou nul soumis : {amount}")
        return "Erreur : Le montant du bon d'achat doit être strictement supérieur à 0€."

    if amount > 1000.0:
        logger.warning(f"[MCP Outil] Montant suspect ou excessif soumis : {amount}")
        return "Erreur : Le montant du bon d'achat ne peut pas dépasser la limite de sécurité de 1000€."

    try:
        voucher_code = generate_refund_voucher(client_id, amount)
        return f"Bon d'achat de {amount}€ généré avec succès. Code : {voucher_code}."
    except Exception as e:
        logger.error(f"Erreur lors de la génération du bon d'achat : {e}")
        return f"Erreur interne lors de la génération du bon d'achat."

@mcp.tool()
def resolve_ticket(ticket_id: int) -> str:
    """
    Met à jour le statut d'un ticket de support à 'RÉSOLU'.
    """
    logger.info(f"[MCP Outil] resolve_ticket(ticket_id={ticket_id})")

    if ticket_id <= 0:
        logger.warning(f"[MCP Outil] ID ticket invalide soumis : {ticket_id}")
        return "Erreur : Le ticket_id doit être un entier strictement supérieur à 0."

    success = update_ticket_status(ticket_id, "RÉSOLU")
    if success:
        return f"Le ticket #{ticket_id} a bien été mis à jour au statut 'RÉSOLU'."
    return f"Échec : aucun ticket trouvé avec l'ID #{ticket_id}."
