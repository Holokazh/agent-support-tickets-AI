import asyncio
import logging
import ollama
from mcp import ClientSession
from mcp.client.sse import sse_client
from app.config import settings

# -------------------------------------------------------------
# CONFIGURATION DU LOGGING PROFESSIONNEL
# -------------------------------------------------------------
# On configure le format de sortie : Horodatage [Niveau de gravité] Nom du logger : Message
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("crm_agent")


# -------------------------------------------------------------
# 1. FONCTION DE CHARGEMENT DU PROMPT DEPUIS LE FICHIER TEXTE
# -------------------------------------------------------------
def load_system_prompt(file_path: str = "app/prompts/system_prompt.txt") -> str:
    """
    Lit le fichier de prompt système externe.
    Permet de modifier les instructions de l'agent sans modifier le code.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Fichier de prompt non trouvé à l'adresse {file_path}. Utilisation d'un prompt vide.")
        return "Tu es un agent de support client."

# -------------------------------------------------------------
# 2. FONCTION DE TRADUCTION DES OUTILS (MCP -> OLLAMA)
# -------------------------------------------------------------
def mcp_to_ollama_tool(mcp_tool) -> dict:
    """
    Traduit un outil au format MCP vers le format d'outil attendu par Ollama (OpenAI style).
    """
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": mcp_tool.description,
            "parameters": mcp_tool.inputSchema
        }
    }

# -------------------------------------------------------------
# 3. LOGIQUE PRINCIPALE DE L'AGENT (ASYNC)
# -------------------------------------------------------------
async def run_agent(ticket_message: str):
    # L'adresse de notre serveur MCP SSE hébergé par FastAPI
    mcp_server_url = f"{settings.ollama_url.replace('11434', '8000')}/mcp/sse"  # Dynamique à partir de config.py

    logger.info(f"Connexion au serveur MCP à l'adresse : {mcp_server_url}...")

    # Étape A : Connexion réseau SSE au serveur MCP
    async with sse_client(mcp_server_url) as (read, write):
        # Étape B : Initialisation de la session MCP
        async with ClientSession(read, write) as session:
            await session.initialize()
            logger.info("Connexion au serveur MCP réussie !")

            # Étape C : Récupération de la liste des outils exposés par le serveur
            mcp_tools_response = await session.list_tools()
            logger.info(f"Outils MCP découverts : {[t.name for t in mcp_tools_response.tools]}")

            # Étape D : Traduction des outils pour Ollama
            ollama_tools = [mcp_to_ollama_tool(t) for t in mcp_tools_response.tools]

            # Étape E : Chargement dynamique du prompt système
            system_prompt = load_system_prompt()

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ticket_message}
            ]

            logger.info("=== Début de la résolution du ticket par l'Agent ===")

            # Variable locale pour mémoriser le statut du client
            customer_status = None

            for step in range(10):
                logger.info(f"--- [Réflexion Étape {step + 1}] Consultation d'Ollama... ---")

                # Appel du modèle Ollama local
                response = ollama.chat(
                    model=settings.ollama_model,
                    messages=messages,
                    tools=ollama_tools
                )

                # On ajoute la réponse à l'historique
                messages.append(response.message)

                # Si le modèle a fini et ne demande plus d'outils :
                if not response.message.tool_calls:
                    logger.info("L'Agent a fini sa réflexion.")
                    print("\n" + "="*50)
                    print("RÉPONSE FINALE ADRESSÉE AU CLIENT :")
                    print("="*50)
                    print(response.message.content)
                    print("="*50 + "\n")
                    break

                logger.info(f"Ollama demande d'appeler {len(response.message.tool_calls)} outil(s)...")

                for tool_call in response.message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = tool_call.function.arguments

                    logger.info(f"Appel de l'outil '{tool_name}' avec args : {tool_args}")

                    # -------------------------------------------------------------
                    # GARDE-FOU DE CONFORMITÉ (GUARDRAIL) APPLICATIF
                    # -------------------------------------------------------------
                    if tool_name == "fetch_customer_info":
                        tool_result = await session.call_tool(tool_name, arguments=tool_args)
                        result_text = str(tool_result.content)
                        if "Statut=VIP" in result_text:
                            customer_status = "VIP"
                        elif "Statut=STANDARD" in result_text:
                            customer_status = "STANDARD"

                    elif tool_name == "create_refund_voucher" and customer_status == "STANDARD":
                        logger.warning(f"SÉCURITÉ INTERCEPTÉE : Tentative de bon d'achat pour client STANDARD bloquée.")
                        result_text = "Erreur de conformité : Le client est STANDARD. Il est strictement interdit de générer un bon d'achat pour lui. Vous devez vous excuser pour le retard de livraison et clore le ticket."

                    elif tool_name == "modify_order_status" and customer_status == "STANDARD" and tool_args.get("new_status") == "REMBOURSÉ":
                        logger.warning(f"SÉCURITÉ INTERCEPTÉE : Tentative de remboursement pour client STANDARD bloquée.")
                        result_text = "Erreur de conformité : Le client est STANDARD. Vous ne pouvez pas modifier le statut de la commande en REMBOURSÉ. Vous devez vous excuser pour le retard de livraison et clore le ticket."

                    else:
                        tool_result = await session.call_tool(tool_name, arguments=tool_args)
                        result_text = str(tool_result.content)

                    logger.info(f"Résultat renvoyé à l'IA : {result_text}")

                    # On ajoute la réponse au message de l'historique
                    messages.append({
                        "role": "tool",
                        "name": tool_name,
                        "content": result_text
                    })

if __name__ == "__main__":
    # --- SCÉNARIO DE TEST PAR DÉFAUT : CLIENT STANDARD (Paul Martin) ---
    test_ticket = "Bonjour, je suis Paul Martin (paul.martin@standard.com). Où est ma souris commandée le mois dernier ? (Ticket ID: 2)"

    asyncio.run(run_agent(test_ticket))
