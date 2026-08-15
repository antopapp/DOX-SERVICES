from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Route principale : Affiche ton index.html depuis le dossier templates
@app.route('/')
def home():
    return render_template('index.html')

# Route API pour traiter les recherches de ton interface
@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json(silent=True) or {}
        search_type = data.get('type', 'email')
        query_term = data.get('query', '')

        if not query_term:
            return jsonify({"status": "error", "message": "Aucun terme fourni."}), 400

        # ---> Mets ta logique de recherche OSINT ici <---
        
        # Réponse test renvoyée à ton interface
        return jsonify({
            "status": "success",
            "module": search_type,
            "query": query_term,
            "results": [
                {"info": "Exemple de résultat trouvé pour " + query_term}
            ]
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
