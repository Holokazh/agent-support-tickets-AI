import asyncio
import logging
import ollama
from mcp import ClientSession
from mcp.client.sse import sse_client
from app.config import settings
from app.logger import setup_logger

# Configuration du logger pour l'agent sous le namespace "ast-ai.agent"
logger = setup_logger("ast-ai.agent")

# -------------------------------------------------------------
# 1. TRADUCTION DES OUTILS (MCP -> OLLAMA)
# -------------------------------------------------------------
def mcp_to_ollama_tool(mcp_tool) -> dict:
    """Traduit un outil MCP au format attendu par Ollama."""
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": mcp_tool.description,
            "parameters": mcp_tool.inputSchema
        }
    }


# -------------------------------------------------------------
# 2. GARDE-FOUS DE SÉCURITÉ APPLICATIFS (GUARDRAILS)
# -------------------------------------------------------------
def check_guardrails(customer_status: str, tool_name: str, tool_args: dict) -> tuple[bool, str]:
    """
    Règles de conformité financière de l'entreprise.
    Vérifie si l'IA est autorisée à appeler l'outil demandé selon le statut du client.

    Returns:
        (est_bloque, message_erreur)
    """
    # Si le statut n'est pas encore identifié, on bloque par précaution
    if tool_name in ["create_refund_voucher", "modify_order_status"] and not customer_status:
        return True, "Erreur de conformité : Le statut du client n'est pas encore identifié. Veuillez d'abord appeler 'fetch_customer_info'."

    # Si le client est STANDARD, on lui interdit le bon d'achat
    if tool_name == "create_refund_voucher" and customer_status == "STANDARD":
        return True, "Erreur de conformité : Le client est STANDARD. Il est strictement interdit de générer un bon d'achat pour lui. Vous devez vous excuser et clore le ticket."

    # Si le client est STANDARD, on lui interdit la modification du statut de commande à REMBOURSÉ
    if tool_name == "modify_order_status" and customer_status == "STANDARD" and tool_args.get("new_status") == "REMBOURSÉ":
        return True, "Erreur de conformité : Le client est STANDARD. Il est interdit de rembourser sa commande. Vous devez vous excuser et clore le ticket."

    # L'appel est conforme
    return False, ""


# -------------------------------------------------------------
# 3. LOGIQUE DE L'AGENT
# -------------------------------------------------------------
async def run_agent(ticket_message: str):
    # L'adresse de notre serveur MCP SSE hébergée par FastAPI
    mcp_server_url = f"{settings.ollama_url.replace('11434', '8000')}/mcp/sse"

    logger.info(f"Connexion au serveur MCP à l'adresse : {mcp_server_url}...")

    async with sse_client(mcp_server_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            logger.info("Connexion au serveur MCP réussie !")

            # Découverte et traduction des outils
            mcp_tools_response = await session.list_tools()
            ollama_tools = [mcp_to_ollama_tool(t) for t in mcp_tools_response.tools]

            # Le prompt système écrit en dur (très facile à lire et modifier ici !)
            system_prompt = f"""
            Tu es un agent de support client senior chez AST AI.
            Ton rôle est de résoudre le ticket de support de manière autonome en utilisant tes outils.
            Tu ne connais aucune information par défaut. Tu dois obligatoirement interroger la base via tes outils.

            Tu dois suivre SCRUPULEUSEMENT la séquence d'étapes suivante :

            1. IDENTIFICATION : Appelle 'fetch_customer_info' avec l'email du client.
            2. DIAGNOSTIC : Appelle 'fetch_customer_orders' avec le client_id obtenu.
            3. ACTIONS COMMERCIALES :
               - Si le client est VIP et qu'une de ses commandes est 'RETARDÉ' :
                 a. Calcule {settings.vip_refund_percent}% du montant de cette commande.
                 b. Appelle 'create_refund_voucher' avec le client_id et ce montant calculé pour générer le bon.
                 c. Appelle 'modify_order_status' avec l'order_id de la commande pour passer son statut à 'REMBOURSÉ'.
               - Si le client est STANDARD et en retard : n'appelle aucun bon et ne modifie pas la commande.
            4. CLÔTURE : Appelle obligatoirement 'resolve_ticket' avec le ticket_id pour passer le ticket à 'RÉSOLU' en base.
            5. RÉPONSE CLIENT : Rédige enfin l'e-mail de réponse.

            RÈGLES CRITIQUES DE CONFORMITÉ FINANCIÈRE :
            - Il est STRICTEMENT INTERDIT d'appeler 'create_refund_voucher' ou 'modify_order_status' pour un client au statut 'STANDARD'.
            - Offrir un bon d'achat à un client STANDARD est considéré comme une faute financière grave. Si le client est STANDARD, excuse-toi simplement pour le retard de livraison et passe directement à l'étape 4 (Clôture).

            CONSIGNES DE FORME :
            - Tu n'as le droit de rédiger ta réponse finale qu'APRÈS avoir appelé 'resolve_ticket'.
            - La réponse finale doit être un e-mail complet, courtois et professionnel rédigé à la première personne, adressé directement au client (ex: "Bonjour Paul Martin,").
            - Si un bon d'achat a été généré, indique son code unique et son montant dans le corps de l'e-mail pour lui remettre.
            """

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ticket_message}
            ]

            logger.info("=== Début de la résolution du ticket par l'Agent ===")
            customer_status = None

            for step in range(10):
                logger.info(f"--- [Réflexion Étape {step + 1}] Consultation d'Ollama... ---")

                response = ollama.chat(
                    model=settings.ollama_model,
                    messages=messages,
                    tools=ollama_tools
                )
                messages.append(response.message)

                # Fin de la boucle
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
                    # VÉRIFICATION DU STATUT CLIENT
                    # -------------------------------------------------------------
                    if tool_name == "fetch_customer_info":
                        tool_result = await session.call_tool(tool_name, arguments=tool_args)
                        result_text = str(tool_result.content)
                        if "Statut=VIP" in result_text:
                            customer_status = "VIP"
                        elif "Statut=STANDARD" in result_text:
                            customer_status = "STANDARD"

                    # -------------------------------------------------------------
                    # ÉVALUATION DES GARDE-FOUS PYTHON (CONFORMITÉ)
                    # -------------------------------------------------------------
                    blocked, error_message = check_guardrails(customer_status, tool_name, tool_args)

                    if blocked:
                        logger.warning(f"GARDE-FOU ACTIVÉ : Outil '{tool_name}' bloqué pour client '{customer_status}'")
                        result_text = error_message
                    elif tool_name != "fetch_customer_info":
                        # Exécution réelle
                        tool_result = await session.call_tool(tool_name, arguments=tool_args)
                        result_text = str(tool_result.content)

                    logger.info(f"Résultat renvoyé à l'IA : {result_text}")

                    messages.append({
                        "role": "tool",
                        "name": tool_name,
                        "content": result_text
                    })

if __name__ == "__main__":
    # --- SCÉNARIO DE TEST : CLIENT VIP (Jean Dupont) ---
    # test_ticket = "Bonjour, je suis Jean Dupont (jean.dupont@vip.com). Mon MacBook Pro (commande #1) est marqué en retard ! Je veux être remboursé ou avoir un geste commercial ! (Ticket ID: 1)"

    # (Décommentez pour retester le client STANDARD Paul Martin)
    test_ticket = "Bonjour, je suis Paul Martin (paul.martin@standard.com). Où est ma souris commandée le mois dernier ? (Ticket ID: 2)"

    asyncio.run(run_agent(test_ticket))
