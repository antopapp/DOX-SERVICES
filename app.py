from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Active CORS pour autoriser les requêtes venant de ton frontend
CORS(app)

# Route explicite /search en POST pour matcher la requête de ton JS
@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json(silent=True) or {}
        
        search_type = data.get('type', 'email')
        query_term = data.get('query', '')

        if not query_term:
            return jsonify({
                "status": "error",
                "message": "Aucun terme de recherche fourni."
            }), 400

        # Place ta logique de traitement/recherche ici
        # Exemple de réponse :
        response_data = {
            "status": "success",
            "type": search_type,
            "query": query_term,
            "message": "Requête reçue avec succès par l'API Render !"
        }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Route de secours sur la racine pour tester si le serveur répond
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "API F9UM operational"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
