import os
import uuid
from app.database import get_db_cursor

def generate_refund_voucher(client_id: int, amount: float) -> str:
    """
    Génère un bon d'achat de dédommagement pour un client.

    1. Génère un code unique (ex: VIP-400-E3B2A14D).
    2. Enregistre ce bon d'achat en base de données.
    3. Crée un fichier texte physique sous 'vouchers/voucher_client_<id>.txt'.

    Args:
        client_id: L'identifiant du client bénéficiaire.
        amount: Le montant en euros du bon.

    Returns:
        Le code unique du bon généré.
    """
    # 1. Génération d'un code promo unique et court (premiers caractères d'un UUID)
    unique_suffix = str(uuid.uuid4())[:8].upper()
    voucher_code = f"VIP-{int(amount)}-{unique_suffix}"

    # 2. Enregistrement en base de données dans la table 'vouchers'
    with get_db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO vouchers (client_id, code, montant, statut) VALUES (%s, %s, %s, %s);",
            (client_id, voucher_code, amount, "ACTIF")
        )

    # 3. Création du fichier physique local
    # os.makedirs(..., exist_ok=True) crée le dossier 'vouchers' s'il n'existe pas encore
    os.makedirs("vouchers", exist_ok=True)

    file_path = f"vouchers/voucher_client_{client_id}.txt"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("=========================================\n")
            f.write("            BON DE RÉDUCTION E-COMMERCE  \n")
            f.write("=========================================\n")
            f.write(f"Client ID   : {client_id}\n")
            f.write(f"Code Unique : {voucher_code}\n")
            f.write(f"Montant     : {amount:.2f} €\n")
            f.write("Statut      : ACTIF (Valable 1 an)\n")
            f.write("=========================================\n")
            f.write("Généré automatiquement par l'Agent Support AI.\n")
            f.write("=========================================\n")
        print(f"[Fichier Créé] -> {file_path}")
    except Exception as e:
        print(f"Erreur d'écriture du fichier voucher : {e}")
        # On ne bloque pas l'exécution globale, mais on logue l'erreur

    return voucher_code
