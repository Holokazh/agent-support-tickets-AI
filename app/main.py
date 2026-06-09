from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # <-- [NOUVEAU] Import du middleware de sécurité CORS

# Import de nos composants internes
from app.mcp.server import mcp
from app.controllers.api import router as api_router  # <-- [NOUVEAU] Import de notre routeur de dashboard

# -------------------------------------------------------------
# 1. INITIALISATION DE FASTAPI
# -------------------------------------------------------------
app = FastAPI(
    title="AST AI CRM Backend",
    description="Backend de gestion de support client intégrant le protocole MCP pour Agent IA.",
    version="1.0.0"
)

# -------------------------------------------------------------
# 2. CONFIGURATION DU CORS (Sécurité Navigateur)
# -------------------------------------------------------------
# Ce middleware injecte les en-têtes HTTP requis pour autoriser des applications
# tierces (comme notre futur front-end React) à interroger notre API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # En dev, on autorise tout. En production, on restreindrait à l'URL du front.
    allow_credentials=True,
    allow_methods=["*"],      # Autorise toutes les méthodes (GET, POST, PUT, DELETE)
    allow_headers=["*"],      # Autorise tous les headers
)

# -------------------------------------------------------------
# 3. ROUTE D'ACCUEIL REST
# -------------------------------------------------------------
@app.get("/")
def read_root():
    """
    Route d'accueil REST pour vérifier l'état du serveur.
    """
    return {
        "status": "online",
        "message": "Bienvenue sur le Backend AST AI CRM API !",
        "mcp_endpoint": "/mcp",
        "mcp_sse_url": "/mcp/sse"
    }

# -------------------------------------------------------------
# 4. INCLUSION DES ROUTES REST (Dashboard)
# -------------------------------------------------------------
# Cette ligne active officiellement les routes du routeur (/api/tickets, /api/clients, etc.)
app.include_router(api_router)

# -------------------------------------------------------------
# 5. MONTAGE DU SERVEUR MCP (IA)
# -------------------------------------------------------------
print("Montage du serveur MCP sur la route /mcp...")
app.mount("/mcp", mcp.app)
print("Serveur MCP monté et prêt !")
