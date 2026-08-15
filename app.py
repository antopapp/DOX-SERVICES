from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# CORS est nécessaire pour que ton front-end puisse discuter avec ton back-end sur Render
CORS(app)

# 1. Route principale : Affiche ton index.html depuis le dossier templates
@app.route('/')
def home():
    return render_template('index.html')

# 2. Route API pour traiter les recherches (Utilise GET pour faciliter les appels)
@app.route('/search', methods=['GET'])
def search():
    try:
        # Récupération des paramètres via l'URL (ex: /search?type=email&q=test@mail.com)
        search_type = request.args.get('type', 'email')
        query_term = request.args.get('q', '')

        if not query_term:
            return jsonify({"status": "error", "message": "Aucun terme de recherche fourni."}), 400

        # --- ICI TA LOGIQUE OSINT ---
        # Exemple : tu peux ajouter ici tes scripts de recherche (Toutatis, etc.)
        # en utilisant 'query_term' et 'search_type'
        
        # Exemple de réponse retournée à l'interface
        return jsonify({
            "status": "success",
            "module": search_type,
            "query": query_term,
            "results": [
                {
                    "source": "Système F9UM",
                    "data": f"Recherche traitée avec succès pour : {query_term}",
                    "type": search_type
                }
            ]
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 3. Route de santé (Utile pour que Render sache que ton serveur est en ligne)
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "online"}), 200

if __name__ == '__main__':
    # Sur Render, host='0.0.0.0' est obligatoire
    app.run(host='0.0.0.0', port=5000)
    
