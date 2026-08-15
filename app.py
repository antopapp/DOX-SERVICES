from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os

# On indique à Flask de chercher le HTML dans le dossier courant ou templates
app = Flask(__name__, template_folder='.', static_folder='.')
CORS(app)

# 1. Route racine : renvoie ton interface HTML au lieu du JSON
@app.route('/')
def home():
    if os.path.exists('index.html'):
        return render_template('index.html')
    return "Fichier index.html introuvable sur le serveur", 404

# 2. Route de recherche pour tes requêtes POST
@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json(silent=True) or {}
        search_type = data.get('type', 'email')
        query_term = data.get('query', '')

        if not query_term:
            return jsonify({"status": "error", "message": "Aucun terme fourni."}), 400

        # Mets ta logique de traitement ici
        return jsonify({
            "status": "success",
            "type": search_type,
            "query": query_term,
            "results": []
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
