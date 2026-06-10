import asyncio
import ollama
from mcp import ClientSession
from mcp.client.sse import sse_client

# -------------------------------------------------------------
# 1. FONCTION DE TRADUCTION DES OUTILS (MCP -> OLLAMA)
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
# 2. LOGIQUE PRINCIPALE DE L'AGENT (ASYNC)
# -------------------------------------------------------------
async def run_agent(ticket_message: str):
    # L'adresse de notre serveur MCP SSE hébergé par FastAPI
    mcp_server_url = "http://localhost:8000/mcp/sse"

    print(f"Connexion au serveur MCP à l'adresse : {mcp_server_url}...")

    # Étape A : Connexion réseau SSE au serveur MCP
    async with sse_client(mcp_server_url) as (read, write):
        # Étape B : Initialisation de la session MCP
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connexion au serveur MCP réussie !")

            # Étape C : Récupération de la liste des outils exposés par le serveur
            mcp_tools_response = await session.list_tools()
            print(f"Outils MCP découverts : {[t.name for t in mcp_tools_response.tools]}")

            # Étape D : Traduction des outils pour Ollama
            ollama_tools = [mcp_to_ollama_tool(t) for t in mcp_tools_response.tools]

            # Étape E : Préparation du prompt système et de l'historique
            system_prompt = """
            Tu es un agent de support client senior chez AST AI.
            Ton rôle est de résoudre le ticket de support de manière autonome en utilisant tes outils.
            Tu ne connais aucune information par défaut. Tu dois obligatoirement interroger la base via tes outils.

            Tu dois suivre SCRUPULEUSEMENT la séquence d'étapes suivante :

            1. IDENTIFICATION : Appelle 'fetch_customer_info' avec l'email du client.
            2. DIAGNOSTIC : Appelle 'fetch_customer_orders' avec le client_id obtenu.
            3. ACTIONS COMMERCIALES :
               - Si le client est VIP et qu'une de ses commandes est 'RETARDÉ' :
                 a. Calcule 20% du montant de cette commande.
                 b. Appelle 'create_refund_voucher' avec ce montant pour générer le bon.
                 c. Appelle 'modify_order_status' pour passer le statut de cette commande à 'REMBOURSÉ'.
               - Si le client est STANDARD et en retard : n'appelle aucun bon et ne modifie pas la commande.
            4. CLÔTURE : Appelle obligatoirement 'resolve_ticket' pour passer le ticket à 'RÉSOLU' en base.
            5. RÉPONSE CLIENT : Rédige enfin l'e-mail de réponse.

            RÈGLES CRITIQUES DE CONFORMITÉ FINANCIÈRE :
            - Il est STRICTEMENT INTERDIT d'appeler 'create_refund_voucher' ou 'modify_order_status' pour un client au statut 'STANDARD'.
            - Offrir un bon d'achat à un client STANDARD est considéré comme une faute financière grave. Si le client est STANDARD, excuse-toi simplement pour le retard et passe directement à l'étape 4 (Clôture).

            CONSIGNES DE FORME :
            - Tu n'as le droit de rédiger ta réponse finale qu'APRÈS avoir appelé 'resolve_ticket'.
            - La réponse finale doit être un e-mail complet, courtois et professionnel rédigé à la première personne, adressé directement au client (ex: "Bonjour Paul Martin,").
            - Si un bon d'achat a été généré, indique son code unique et son montant dans le corps de l'e-mail pour lui remettre.
            """

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ticket_message}
            ]

            # Étape F : Boucle de réflexion de l'Agent (Max 10 étapes)
            print("\n=== Début de la résolution du ticket par l'Agent ===")

            # Variable locale de notre code Python pour surveiller le statut du client
            customer_status = None

            for step in range(10):
                print(f"\n[Réflexion Étape {step + 1}] Consultation d'Ollama...")

                # Appel du modèle Ollama local
                response = ollama.chat(
                    model="qwen2.5:7b",
                    messages=messages,
                    tools=ollama_tools
                )

                # On ajoute la réponse à l'historique
                messages.append(response.message)

                # Si le modèle a fini et ne demande plus d'outils :
                if not response.message.tool_calls:
                    print("\n=== Réponse finale rédigée par l'Agent ===")
                    print(response.message.content)
                    break

                # Si le modèle demande des outils :
                print(f"Ollama demande d'appeler {len(response.message.tool_calls)} outil(s)...")

                for tool_call in response.message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = tool_call.function.arguments

                    print(f"  -> Exécution de '{tool_name}' avec les arguments : {tool_args}")

                    # -------------------------------------------------------------
                    # GARDE-FOU DE CONFORMITÉ (GUARDRAIL) EXÉCUTÉ PAR LE CODE PYTHON
                    # -------------------------------------------------------------

                    # 1. Enregistrement du statut du client pour surveillance
                    if tool_name == "fetch_customer_info":
                        tool_result = await session.call_tool(tool_name, arguments=tool_args)
                        result_text = str(tool_result.content)
                        if "Statut=VIP" in result_text:
                            customer_status = "VIP"
                        elif "Statut=STANDARD" in result_text:
                            customer_status = "STANDARD"

                    # 2. Blocage d'attribution de bon de réduction à un client STANDARD
                    elif tool_name == "create_refund_voucher" and customer_status == "STANDARD":
                        print("  [SÉCURITÉ APPLICATIVE INTERCEPTÉE] Refus de générer un bon d'achat pour un client STANDARD.")
                        result_text = "Erreur de conformité : Le client est STANDARD. Il est strictement interdit de générer un bon d'achat pour lui. Vous devez vous excuser pour le retard de livraison et clore le ticket."

                    # 3. Blocage de remboursement de commande pour un client STANDARD
                    elif tool_name == "modify_order_status" and customer_status == "STANDARD" and tool_args.get("new_status") == "REMBOURSÉ":
                        print("  [SÉCURITÉ APPLICATIVE INTERCEPTÉE] Refus de modifier le statut de commande pour un client STANDARD.")
                        result_text = "Erreur de conformité : Le client est STANDARD. Vous ne pouvez pas modifier le statut de la commande en REMBOURSÉ. Vous devez vous excuser pour le retard de livraison et clore le ticket."

                    # Sinon, l'appel est conforme et on l'exécute normalement
                    else:
                        tool_result = await session.call_tool(tool_name, arguments=tool_args)
                        result_text = str(tool_result.content)

                    print(f"  -> Résultat retourné à l'IA : {result_text}")

                    # On ajoute la réponse au message de l'historique
                    messages.append({
                        "role": "tool",
                        "name": tool_name,
                        "content": result_text
                    })

if __name__ == "__main__":
    # -------------------------------------------------------------
    # JEUX DE TEST (Commentez/Décommentez le scénario à tester)
    # -------------------------------------------------------------

    # --- SCÉNARIO 1 : CLIENT VIP (Jean Dupont) ---
    # test_ticket = "Bonjour, je suis Jean Dupont (jean.dupont@vip.com). Mon MacBook Pro (commande #1) est marqué en retard ! Je veux être remboursé ou avoir un geste commercial ! (Ticket ID: 1)"

    # --- SCÉNARIO 2 : CLIENT STANDARD (Paul Martin) ---
    test_ticket = "Bonjour, je suis Paul Martin (paul.martin@standard.com). Où est ma souris commandée le mois dernier ? (Ticket ID: 2)"

    asyncio.run(run_agent(test_ticket))
