from contextlib import contextmanager
import psycopg2
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
    Context Manager pour exécuter des requêtes SQL de manière sécurisée et résiliente.
    Valide la connexion avant usage et recycle les connexions mortes du pool.
    """
    if db_pool is None:
        raise RuntimeError("Le pool de connexions PostgreSQL n'est pas initialisé.")

    # Emprunt d'une connexion au pool
    connection = db_pool.getconn()

    # [RÉSILIENCE] Si la connexion obtenue a été fermée par le serveur (timeout),
    # on la détruit proprement et on en demande une nouvelle toute neuve.
    if connection.closed != 0:
        print("[DATABASE] Connexion obsolète détectée. Renouvellement de la connexion...")
        db_pool.putconn(connection, close=True) # close=True détruit la connexion défectueuse
        connection = db_pool.getconn()

    cursor = None
    try:
        cursor = connection.cursor()
        yield cursor
        connection.commit()

    except (psycopg2.InterfaceError, psycopg2.OperationalError) as e:
        # [RÉSILIENCE] Erreur de communication réseau ou connexion perdue en cours de route.
        # On ne fait pas de rollback (impossible car la connexion est déjà coupée).
        # On détruit la connexion dans le pool pour ne pas polluer les prochains appels.
        print(f"[DATABASE ERROR] Connexion perdue pendant la requête : {e}. Recyclage...")
        if cursor:
            try: cursor.close()
            except: pass
        db_pool.putconn(connection, close=True)
        raise e

    except Exception as e:
        # Autre erreur SQL classique (erreur de syntaxe, contrainte non respectée, etc.)
        # La connexion est saine, on annule juste la transaction (rollback)
        if connection.closed == 0:
            connection.rollback()
        if cursor:
            cursor.close()
        # Et on remet la connexion saine dans le pool
        db_pool.putconn(connection)
        raise e

    else:
        # Si tout s'est bien passé
        if cursor:
            cursor.close()
        # On remet la connexion fonctionnelle dans le pool
        db_pool.putconn(connection)
