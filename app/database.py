from contextlib import contextmanager
from psycopg2.pool import ThreadedConnectionPool
from app.config import settings

# -------------------------------------------------------------
# INITIALISATION DU POOL DE CONNEXIONS
# -------------------------------------------------------------
# minconn=1 : Le pool garde au moins 1 connexion ouverte en permanence.
# maxconn=10 : Le pool peut ouvrir jusqu'à 10 connexions en parallèle si l'application subit une forte charge.
try:
    print("Initialisation du pool de connexions PostgreSQL...")
    db_pool = ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=settings.database_url
    )
    print("Pool de connexions PostgreSQL initialisé avec succès.")
except Exception as e:
    print(f"Erreur critique lors de l'initialisation du pool PostgreSQL : {e}")
    db_pool = None


# -------------------------------------------------------------
# LE CONTEXT MANAGER POUR NOS REQUÊTES
# -------------------------------------------------------------
@contextmanager
def get_db_cursor():
    """
    Context Manager pour exécuter des requêtes SQL de manière sécurisée.
    """
    if db_pool is None:
        raise RuntimeError("Le pool de connexions PostgreSQL n'est pas initialisé.")

    # On récupère une connexion disponible du pool
    connection = db_pool.getconn()
    try:
        # On crée un curseur pour lancer les requêtes SQL
        cursor = connection.cursor()

        # Le code à l'intérieur du bloc 'with' est exécuté ici grâce à 'yield'
        yield cursor

        # Si le bloc 'with' s'est terminé sans erreur, on valide la transaction
        connection.commit()

    except Exception as e:
        # En cas d'erreur pendant l'exécution SQL, on annule toutes les requêtes en cours
        connection.rollback()
        # On propage l'erreur pour qu'elle puisse être loguée ou gérée plus haut
        raise e

    finally:
        # Dans tous les cas (succès ou échec), on ferme le curseur
        cursor.close()
        # Et on remet la connexion dans le pool pour les prochains appels
        db_pool.putconn(connection)
