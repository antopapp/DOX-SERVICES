import os
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# URL officielle de l'API Brix Hub
BRIX_BASE_URL = "https://api.brixhub.is/api/v1"

# Récupération de la clé API depuis les variables d'environnement de Render
BRIX_API_KEY = os.environ.get("BRIX_API_KEY", "")


@app.route("/search", methods=["GET"])
def search():
  query_type = request.args.get("type")
  query_value = request.args.get("q")

  if not query_value:
    return (
        jsonify({
            "status": "error",
            "message": "Paramètre de recherche 'q' manquant",
        }),
        400,
    )

  # Correspondance entre les champs du front-end et les clés attendues par Brix Hub (/search)
  # Documentation Brix Hub : nom_famille, prenom, nom_utilisateur, email, telephone, adresse_ip, code_postal, ville, discord_id, etc.
  mapping_types = {
      "email": "email",
      "phone": "telephone",
      "lastname": "nom_famille",
      "firstname": "prenom",
      "username": "nom_utilisateur",
      "ip": "adresse_ip",
      "address": "adresse",
      "city": "ville",
      "discord_id": "discord_id",
  }

  brix_field = mapping_types.get(query_type, "nom_famille")

  # Construction du payload JSON pour l'API Brix Hub
  payload = {brix_field: query_value, "flexible": True, "per_page": 10}

  headers = {"X-API-Key": BRIX_API_KEY, "Content-Type": "application/json"}

  try:
    # Appel de l'endpoint POST /search de Brix Hub
    response = requests.post(
        f"{BRIX_BASE_URL}/search", json=payload, headers=headers, timeout=15
    )

    # Gestion des erreurs de l'API Brix Hub
    if response.status_code != 200:
      return (
          jsonify({
              "status": "error",
              "message": (
                  f"Erreur de l'API Brix Hub (Code {response.status_code})"
              ),
          }),
          response.status_code,
      )

    brix_data = response.json()
    results = brix_data.get("data", {}).get("results", [])

    # Formatage des résultats pour correspondre exactement à ce qu'attend ton front-end HTML
    formatted_results = []
    for item in results:
      # On extrait les sources et le score de confiance renvoyés par Brix Hub
      sources = item.get("_sources", ["Brix Hub"])
      confidence = item.get("_confidence", 0)

      # On nettoie l'objet pour ne garder que les infos textuelles à afficher proprement
      details_lines = []
      for key, val in item.items():
        if val and not key.startswith("_"):
          details_lines.append(f"{key.upper()} : {val}")

      details_lines.append(f"SCORE DE CONFIANCE : {confidence}%")

      formatted_results.append({
          "source": ", ".join(sources),
          "type": query_type,
          "data": "\n".join(details_lines),
      })

    return jsonify({"status": "success", "results": formatted_results})

  except requests.exceptions.Timeout:
    return (
        jsonify({
            "status": "error",
            "message": "L'appel vers Brix Hub a expiré (Timeout)",
        }),
        504,
    )
  except Exception as e:
    return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
