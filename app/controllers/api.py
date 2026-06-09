from fastapi import APIRouter

# Import de nos services d'affichage global
from app.services.ticket import get_all_tickets
from app.services.customer import get_all_customers
from app.services.order import get_all_orders
from app.services.voucher import get_all_vouchers

# On crée un routeur avec le préfixe '/api' pour regrouper nos routes de dashboard
router = APIRouter(prefix="/api")

@router.get("/tickets")
def list_tickets():
    """
    Expose la liste de tous les tickets de support.
    Utile pour afficher le flux de tickets dans le dashboard.
    """
    return get_all_tickets()

@router.get("/clients")
def list_customers():
    """
    Expose la liste de tous les clients enregistrés.
    """
    return get_all_customers()

@router.get("/commandes")
def list_orders():
    """
    Expose la liste de toutes les commandes.
    """
    return get_all_orders()

@router.get("/vouchers")
def list_vouchers():
    """
    Expose la liste de tous les bons d'achat créés.
    """
    return get_all_vouchers()
