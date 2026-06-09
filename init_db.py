import psycopg2
from psycopg2 import sql

# -------------------------------------------------------------
# CONFIGURATION DES PARAMÈTRES DE CONNEXION
# -------------------------------------------------------------
DB_HOST = "localhost"
DB_PORT = "5433"
DB_NAME = "ast_ai"
DB_USER = "ast_ai_user"
DB_PASSWORD = "ast_ai_password_secret"

def init_database():
    print("Connexion à la base de données PostgreSQL...")
    try:
        # 1. Établissement de la connexion
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        print("Connexion réussie !")

        # -------------------------------------------------------------
        # 2. NETTOYAGE DES ANCIENNES TABLES
        # -------------------------------------------------------------
        print("Nettoyage des anciennes tables...")
        cursor.execute("DROP TABLE IF EXISTS vouchers CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS tickets CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS commandes CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS clients CASCADE;")

        # -------------------------------------------------------------
        # 3. CRÉATION DES TABLES
        # -------------------------------------------------------------
        print("Création des tables...")

        # Table Clients
        cursor.execute("""
            CREATE TABLE clients (
                id SERIAL PRIMARY KEY,
                nom VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                statut VARCHAR(20) CHECK (statut IN ('VIP', 'STANDARD')) NOT NULL
            );
        """)

        # Table Commandes (liée aux clients)
        cursor.execute("""
            CREATE TABLE commandes (
                id SERIAL PRIMARY KEY,
                client_id INT REFERENCES clients(id) ON DELETE CASCADE,
                produit VARCHAR(100) NOT NULL,
                prix NUMERIC(10, 2) NOT NULL,
                statut VARCHAR(50) CHECK (statut IN ('LIVRÉ', 'EN_COURS', 'RETARDÉ', 'REMBOURSÉ')) NOT NULL
            );
        """)

        # Table Tickets de support (liés aux clients)
        cursor.execute("""
            CREATE TABLE tickets (
                id SERIAL PRIMARY KEY,
                client_id INT REFERENCES clients(id) ON DELETE CASCADE,
                message TEXT NOT NULL,
                statut VARCHAR(50) CHECK (statut IN ('OUVERT', 'RÉSOLU')) NOT NULL
            );
        """)

        # Table Vouchers (Bons de réduction liés aux clients)
        cursor.execute("""
            CREATE TABLE vouchers (
                id SERIAL PRIMARY KEY,
                client_id INT REFERENCES clients(id) ON DELETE CASCADE,
                code VARCHAR(50) UNIQUE NOT NULL,
                montant NUMERIC(10, 2) NOT NULL,
                statut VARCHAR(20) CHECK (statut IN ('ACTIF', 'UTILISÉ', 'EXPIRÉ')) DEFAULT 'ACTIF' NOT NULL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """)

        # -------------------------------------------------------------
        # 4. INSERTION DES DONNÉES DE TEST
        # -------------------------------------------------------------
        print("Insertion des données de test...")

        # Insertion des clients et récupération de leurs IDs générés
        # Client 1 : Jean Dupont (VIP)
        cursor.execute(
            "INSERT INTO clients (nom, email, statut) VALUES (%s, %s, %s) RETURNING id;",
            ("Jean Dupont", "jean.dupont@vip.com", "VIP")
        )
        jean_id = cursor.fetchone()[0]

        # Client 2 : Paul Martin (STANDARD)
        cursor.execute(
            "INSERT INTO clients (nom, email, statut) VALUES (%s, %s, %s) RETURNING id;",
            ("Paul Martin", "paul.martin@standard.com", "STANDARD")
        )
        paul_id = cursor.fetchone()[0]

        # Insertion des commandes liées à ces clients
        # Commande de Jean (MacBook Pro en retard)
        cursor.execute(
            "INSERT INTO commandes (client_id, produit, prix, statut) VALUES (%s, %s, %s, %s);",
            (jean_id, "MacBook Pro", 2000.00, "RETARDÉ")
        )

        # Commande de Paul (Souris Sans Fil en retard)
        cursor.execute(
            "INSERT INTO commandes (client_id, produit, prix, statut) VALUES (%s, %s, %s, %s);",
            (paul_id, "Souris Sans Fil", 50.00, "RETARDÉ")
        )

        # Insertion des tickets de support ouverts
        # Ticket de Jean (VIP réclame dédommagement)
        cursor.execute(
            "INSERT INTO tickets (client_id, message, statut) VALUES (%s, %s, %s);",
            (jean_id, "Mon MacBook Pro est en retard ! Je veux être dédommagé !", "OUVERT")
        )

        # Ticket de Paul (Standard demande des infos)
        cursor.execute(
            "INSERT INTO tickets (client_id, message, statut) VALUES (%s, %s, %s);",
            (paul_id, "Où est ma souris ?", "OUVERT")
        )

        # Enregistrement définitif de toutes les modifications
        conn.commit()
        print("Base de données initialisée avec succès avec les jeux de test !")

    except Exception as e:
        print(f"Une erreur est survenue : {e}")
        # En cas d'erreur, on annule toutes les modifications non enregistrées
        if 'conn' in locals() and conn:
            conn.rollback()

    finally:
        # Fermeture propre des connexions
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
            print("Connexion à PostgreSQL fermée.")

if __name__ == "__main__":
    init_database()
