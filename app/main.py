from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import de nos composants internes
from app.mcp.server import mcp
from app.controllers.api import router as api_router

# 1. On récupère l'application SSE via la méthode sse_app()
mcp_app = mcp.sse_app()

# 2. INITIALISATION DE FASTAPI
app = FastAPI(
    title="AST AI CRM Backend",
    description="Backend de gestion de support client intégrant le protocole MCP pour Agent IA.",
    version="1.0.0"
)

# 3. CONFIGURATION DU CORS (Sécurité Navigateur)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. ROUTE D'ACCUEIL REST
@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Bienvenue sur le Backend AST AI CRM API !",
        "mcp_endpoint": "/mcp",
        "mcp_sse_url": "/mcp/sse"
    }

# 5. INCLUSION DES ROUTES REST (Dashboard)
app.include_router(api_router)

# 6. LE MONTAGE DU SERVEUR MCP (IA)
print("Montage du serveur MCP sur la route /mcp...")
# On monte l'application retournée par sse_app()
app.mount("/mcp", mcp_app)
print("Serveur MCP monté et prêt !")
