import os
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Récupère ta clé API Brix Hub depuis les variables d'environnement de Render
# (Conseil : Mets ta clé dans les "Environment Variables" de ton dashboard Render sous le nom BRIX_API_KEY)
BRIX_API_KEY = os.environ.get("BRIX_API_KEY", "TA_CLE_API_PAR_DEFAUT")
BRIX_API_URL = "https://api.brixhub.com/v1/search"  # <--- Remplace par l'URL exacte de l'API Brix Hub si elle est différente


@app.route("/search", methods=["GET"])
def search():
  query_type = request.args.get("type")
  query_value = request.args.get("q")

  if not query_value:
    return jsonify({"status": "error", "message": "Paramètre 'q' manquant"}), 400

  # Paramètres à envoyer à l'API Brix Hub (adapte selon leur documentation officielle)
  payload = {"type": query_type, "query": query_value}

  headers = {
      "Authorization": f"Bearer {BRIX_API_KEY}",
      "Content-Type": "application/json",
  }

  try:
    # Appel vers l'API Brix Hub
    # response = requests.post(BRIX_API_URL, json=payload, headers=headers)
    # Note: Si Brix Hub utilise du GET, utilise plutôt requests.get(f"{BRIX_API_URL}?...", headers=headers)

    # --- SIMULATION DE LA REPONSE DE BRUX HUB (À adapter selon leur vraie structure JSON) ---
    # Ici, on simule ce que Brix Hub te renvoie pour que ça colle directement avec ton front-end :
    # Remplace cette partie par les vraies données de la réponse de Brix Hub (`response.json()`)
    
    formatted_results = [{
        "source": "Brix Hub Database",
        "type": query_type,
        "data": (
            f"Résultat trouvé pour [{query_value}]\nNom : Vanderziepe\nPrénom"
            " : Inconnu\nStatut : Actif dans la base"
        ),
    }]

    return jsonify({"status": "success", "results": formatted_results})

  except Exception as e:
    return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
