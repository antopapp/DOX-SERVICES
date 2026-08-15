from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Code HTML complet directement dans Python (plus de fichier index.html manquant)
HTML_PAGE = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>F9UM SERVICES | OSINT Platform</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #000000;
            --glass-bg: rgba(255, 255, 255, 0.03);
            --glass-card: rgba(15, 15, 22, 0.7);
            --glass-border: rgba(255, 255, 255, 0.12);
            --glass-shine: rgba(255, 255, 255, 0.22);
            --neon-purple: #8b5cf6;
            --neon-blue: #3b82f6;
            --neon-cyan: #06b6d4;
            --neon-green: #10b981;
            --text-main: #f8fafc;
            --text-muted: #a1a1aa;
            --font-sans: 'Inter', system-ui, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: var(--font-sans);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
        }
        .container { width: 100%; max-width: 800px; text-align: center; }
        h1 { font-family: var(--font-mono); font-size: 2.5rem; margin-bottom: 20px; color: #fff; text-shadow: 0 0 15px rgba(139, 92, 246, 0.6); }
        .search-card {
            background: var(--glass-card);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 20px;
            display: flex;
            gap: 15px;
            margin-top: 30px;
            box-shadow: 0 15px 45px rgba(0, 0, 0, 0.8);
        }
        input[type="text"] {
            flex: 1; padding: 14px 18px; border-radius: 12px;
            border: 1px solid var(--glass-border); background: #050508;
            color: var(--text-main); font-size: 15px; outline: none;
        }
        input[type="text"]:focus { border-color: var(--neon-purple); }
        button.btn-search {
            padding: 0 30px; border-radius: 12px; border: none;
            background: linear-gradient(135deg, var(--neon-purple), var(--neon-blue));
            color: #ffffff; font-family: var(--font-mono); font-weight: 700; cursor: pointer;
        }
        #resultsArea { margin-top: 25px; text-align: left; }
        .result-box {
            background: var(--glass-card); border: 1px solid var(--glass-border);
            border-radius: 14px; padding: 20px; font-family: var(--font-mono); font-size: 0.85rem; white-space: pre-wrap;
        }
    </style>
</head>
<body>
<div class="container">
    <h1>F9UM SERVICES</h1>
    <p style="color: var(--text-muted);">Plateforme OSINT opérationnelle</p>
    
    <div class="search-card">
        <input type="text" id="queryInput" placeholder="Entrer une cible (ex: test@email.com)" onkeypress="if(event.key === 'Enter') lancerRecherche()">
        <button class="btn-search" onclick="lancerRecherche()">Rechercher</button>
    </div>

    <div id="resultsArea"></div>
</div>

<script>
    async function lancerRecherche() {
        const query = document.getElementById('queryInput').value.trim();
        const area = document.getElementById('resultsArea');
        if (!query) return;

        area.innerHTML = `<p style="color: var(--text-muted); text-align:center; margin-top:15px; font-family:var(--font-mono);">Recherche en cours...</p>`;

        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'email', query: query })
            });
            const data = await response.json();
            area.innerHTML = `<div class="result-box">${JSON.stringify(data, null, 2)}</div>`;
        } catch (err) {
            area.innerHTML = `<div class="result-box" style="border-color: #ef4444; color: #ef4444;">Erreur de connexion au serveur.</div>`;
        }
    }
</script>
</body>
</html>
"""

# Route racine : Affiche directement la belle interface graphique
@app.route('/', methods=['GET'])
def home():
    return HTML_PAGE

# Route API pour traiter la recherche
@app.route('/search', methods=['POST'])
def search():
    data = request.get_json(silent=True) or {}
    query = data.get('query', '')
    
    return jsonify({
        "status": "success",
        "query": query,
        "message": "Requête traitée avec succès par l'API Render !"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
