from fastapi import FastAPI
from app.mcp.server import mcp

# -------------------------------------------------------------
# 1. INITIALISATION DE FASTAPI
# -------------------------------------------------------------
app = FastAPI(
    title="AST AI CRM Backend",
    description="Backend de gestion de support client intégrant le protocole MCP pour Agent IA.",
    version="1.0.0"
)

# -------------------------------------------------------------
# 2. ROUTE REST STANDARD (Pour les humains)
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
# 3. LE MONTAGE DU SERVEUR MCP (Pour l'IA)
# -------------------------------------------------------------
# La propriété 'mcp.app' est une application ASGI standard compatible Starlette/FastAPI.
# En la montant sur '/mcp', FastAPI va router toutes les requêtes arrivant sur
# '/mcp/*' (notamment '/mcp/sse' et '/mcp/messages') directement vers le moteur MCP.
print("Montage du serveur MCP sur la route /mcp...")
app.mount("/mcp", mcp.app)
print("Serveur MCP monté et prêt !")
