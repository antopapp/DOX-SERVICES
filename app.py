import os
import requests
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# URLs et configurations
BRIX_BASE_URL = "https://brixhub.to/api/v1"
BRIX_API_KEY = os.environ.get("BRIX_API_KEY", "")
DISCORD_WEBHOOK_URL = os.environ.get("https://discord.com/api/webhooks/1541108116320428183/_P0bDDp7CPQxiaTDTWvE_p92joeeFGb04eGLefoSsBQOjBncFgVBHdQxZxR9GZOfH9n7", "")


def send_discord_notification(payload_data, user_ip):
    """Envoie un résumé de la recherche effectuée sur le webhook Discord."""
    if not DISCORD_WEBHOOK_URL:
        return  # Si le webhook n'est pas configuré, on ne fait rien

    # Formatage propre des critères de recherche pour Discord
    criteria_lines = []
    for key, val in payload_data.items():
        if key not in ["flexible", "per_page"]:
            criteria_lines.append(f"- **{key}** : `{val}`")
    
    criteria_str = "\n".join(criteria_lines) if criteria_lines else "Aucun critère spécifique"

    discord_payload = {
        "content": (
            f"🔍 **Nouvelle recherche OSINT sur le site !**\n"
            f"🌐 **IP Utilisateur :** `{user_ip}`\n"
            f"📋 **Critères utilisés :**\n{criteria_str}"
        )
    }

    try:
        requests.post(DISCORD_WEBHOOK_URL, json=discord_payload, timeout=5)
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification Discord : {e}")


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/search", methods=["GET"])
def search():
    # Récupération de tous les paramètres passés dans l'URL par le front-end
    allowed_fields = [
        "nom_famille", "prenom", "nom_naissance", "nom_utilisateur",
        "email", "telephone", "adresse_ip", "discord_id",
        "adresse", "code_postal", "ville"
    ]
    
    payload = {}
    for field in allowed_fields:
        val = request.args.get(field)
        if val:
            payload[field] = val.strip()

    if not payload:
        return jsonify({
            "status": "error",
            "message": "Veuillez renseigner au moins un critère de recherche."
        }), 400

    # Récupération de l'IP (gère les proxys de Render)
    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if user_ip and "," in user_ip:
        user_ip = user_ip.split(",")[0].strip()

    # Envoi de la notification Discord en arrière-plan (sans bloquer la réponse de l'API)
    send_discord_notification(payload, user_ip)

    # Ajout des options demandées par l'API BrixHub
    payload["flexible"] = True
    payload["per_page"] = 15

    headers = {
        "X-API-Key": BRIX_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{BRIX_BASE_URL}/search", json=payload, headers=headers, timeout=15
        )

        if response.status_code != 200:
            return jsonify({
                "status": "error",
                "message": f"Erreur de l'API Brix Hub (Code {response.status_code})"
            }), response.status_code

        brix_data = response.json()
        results = brix_data.get("data", {}).get("results", [])

        formatted_results = []
        for item in results:
            sources = item.get("_sources", ["Brix Hub"])
            confidence = item.get("_confidence", 0)

            details_lines = []
            for key, val in item.items():
                if val and not key.startswith("_"):
                    details_lines.append(f"{key.upper()} : {val}")

            details_lines.append(f"SCORE DE CONFIANCE : {confidence}%")

            formatted_results.append({
                "source": ", ".join(sources),
                "type": "MULTI",
                "data": "\n".join(details_lines),
            })

        return jsonify({"status": "success", "results": formatted_results})

    except requests.exceptions.Timeout:
        return jsonify({
            "status": "error",
            "message": "L'appel vers Brix Hub a expiré (Timeout)"
        }), 504
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
