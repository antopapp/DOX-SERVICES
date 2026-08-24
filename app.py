import os
import requests
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# URLs et configurations
BRIX_BASE_URL = "https://brixhub.to/api/v1"
BRIX_API_KEY = os.environ.get("BRIX_API_KEY", "")

# Configuration de la clé API OathNet depuis les variables d'environnement Render
OATHNET_API_KEY = os.environ.get("OATHNET_API_KEY", "")

# URL du webhook intégrée pour le test (pense à la supprimer/changer après)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1541108116320428183/_P0bDDp7CPQxiaTDTWvE_p92joeeFGb04eGLefoSsBQOjBncFgVBHdQxZxR9GZOfH9n7"


def send_discord_notification(payload_data, user_ip, search_type="OSINT"):
    """Envoie un résumé de la recherche effectuée sur le webhook Discord."""
    if not DISCORD_WEBHOOK_URL:
        return

    if isinstance(payload_data, dict):
        criteria_lines = []
        for key, val in payload_data.items():
            if key not in ["flexible", "per_page"]:
                criteria_lines.append(f"- **{key}** : `{val}`")
        criteria_str = "\n".join(criteria_lines) if criteria_lines else "Aucun critère spécifique"
    else:
        criteria_str = f"- **Requête** : `{payload_data}`"

    discord_payload = {
        "content": (
            f"🔍 **Nouvelle recherche {search_type} sur le site !**\n"
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


# Nouvelle route pour intégrer la recherche OathNet (Breach / Leaks)
@app.route("/search-oathnet", methods=["GET"])
def search_oathnet():
    query = request.args.get("query") or request.args.get("q")

    if not query:
        return jsonify({
            "status": "error",
            "message": "Veuillez renseigner un terme ou une adresse e-mail pour OathNet."
        }), 400

    query = query.strip()

    # Récupération de l'IP
    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if user_ip and "," in user_ip:
        user_ip = user_ip.split(",")[0].strip()

    # Notification Discord
    send_discord_notification(query, user_ip, search_type="OathNet (Breach)")

    # Ajout des headers incluant l'User-Agent pour éviter le blocage 403
    headers = {
        "x-api-key": OATHNET_API_KEY,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }

    try:
        # 1. Initialisation d'une session de recherche OathNet (pour économiser les quotas)
        session_resp = requests.post(
            "https://oathnet.org/api/service/search/init",
            json={"query": query, "search_type": "auto"},
            headers=headers,
            timeout=10
        ).json()

        session_id = None
        if session_resp.get("success"):
            session_id = session_resp.get("data", {}).get("session", {}).get("id")

        # 2. Requête vers l'endpoint de recherche de brèches v2
        params = {"q": query}
        if session_id:
            params["search_id"] = session_id

        response = requests.get(
            "https://oathnet.org/",
            params=params,
            headers=headers,
            timeout=15
        )

        if response.status_code != 200:
            return jsonify({
                "status": "error",
                "message": f"Erreur de l'API OathNet (Code {response.status_code})"
            }), response.status_code

        oath_data = response.json()
        items = oath_data.get("data", {}).get("items", [])

        formatted_results = []
        for item in items:
            email = item.get("email", "N/A")
            password = item.get("password", "***REDACTED***")
            dbname = item.get("dbname", "Base inconnue")
            indexed_at = item.get("indexed_at", "N/A")

            details_str = (
                f"EMAIL : {email}\n"
                f"MOT DE PASSE : {password}\n"
                f"SOURCE (DB) : {dbname}\n"
                f"INDEXÉ LE : {indexed_at}"
            )

            formatted_results.append({
                "source": f"OathNet ({dbname})",
                "type": "BREACH",
                "data": details_str,
            })

        return jsonify({"status": "success", "results": formatted_results})

    except requests.exceptions.Timeout:
        return jsonify({
            "status": "error",
            "message": "L'appel vers OathNet a expiré (Timeout)"
        }), 504
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/search", methods=["GET"])
def search():
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

    # Récupération de l'IP
    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if user_ip and "," in user_ip:
        user_ip = user_ip.split(",")[0].strip()

    # Envoi de la notification Discord
    send_discord_notification(payload, user_ip, search_type="BrixHub OSINT")

    # Options BrixHub
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
