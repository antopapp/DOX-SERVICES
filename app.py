import os
import smtplib
from email.message import EmailMessage
import requests
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# URLs et configurations
BRIX_BASE_URL = "https://brixhub.to/api/v1"
BRIX_API_KEY = os.environ.get("BRIX_API_KEY", "")

# Webhook (tu pourras le remettre dans le .env plus tard)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1541108116320428183/_P0bDDp7CPQxiaTDTWvE_p92joeeFGb04eGLefoSsBQOjBncFgVBHdQxZxR9GZOfH9n7"

# Configurations pour l'envoi d'e-mails (à stocker aussi dans tes variables d'environnement sur Render)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "ton.email@gmail.com")       # Ton email
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "ton_mot_de_passe_app") # Mot de passe d'application
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "ton.email@gmail.com")   # L'email où tu veux recevoir l'alerte


def send_email_notification(payload_data, user_ip):
    """Envoie un e-mail récapitulatif de la recherche."""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        return

    criteria_lines = []
    for key, val in payload_data.items():
        if key not in ["flexible", "per_page"]:
            criteria_lines.append(f"- {key} : {val}")
    
    criteria_str = "\n".join(criteria_lines) if criteria_lines else "Aucun critère spécifique"

    msg = EmailMessage()
    msg['Subject'] = "🔍 Nouvelle recherche OSINT effectuée !"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    
    body = (
        f"Une nouvelle recherche a été lancée sur ton site.\n\n"
        f"Adresse IP de l'utilisateur : {user_ip}\n\n"
        f"Critères de recherche :\n{criteria_str}"
    )
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail : {e}")


def send_discord_notification(payload_data, user_ip):
    """Envoie un résumé sur le webhook Discord."""
    if not DISCORD_WEBHOOK_URL:
        return

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

    # Récupération propre de l'IP
    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if user_ip and "," in user_ip:
        user_ip = user_ip.split(",")[0].strip()

    # Envoi des notifications (Discord + E-mail) en même temps
    send_discord_notification(payload, user_ip)
    send_email_notification(payload, user_ip)

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
