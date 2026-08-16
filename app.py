import os
import requests
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# URL officielle de l'API Brix Hub
BRIX_BASE_URL = "https://api.brixhub.is/api/v1"

# Récupération de la clé API depuis les variables d'environnement de Render
BRIX_API_KEY = os.environ.get("BRIX_API_KEY", "")


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
