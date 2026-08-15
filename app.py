from flask import Flask, jsonify, request, render_template
import requests
import urllib.parse
import re
import os

app = Flask(__name__)

BRIXHUB_BASE_URL = "https://api.brixhub.is/api/v1"

# Récupération de la clé API configurée dans Render
API_KEY = os.getenv('BRIXHUB_API_KEY', '')

def get_headers():
    return {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

# --- RECHERCHES BRIXHUB ---

def search_email(email):
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return {"error": "Format d'adresse e-mail invalide."}
    
    encoded_email = urllib.parse.quote(email)
    url = f"{BRIXHUB_BASE_URL}/lookup/email/{encoded_email}"
    
    try:
        res = requests.get(url, headers=get_headers(), timeout=10)
        return res.json()
    except requests.RequestException as e:
        return {"error": "Erreur de connexion à l'API BrixHub", "details": str(e)}

def search_phone(phone):
    clean_phone = re.sub(r'[^\d+]', '', phone)
    if len(clean_phone) < 8:
        return {"error": "Numéro de téléphone trop court ou invalide."}
        
    encoded_phone = urllib.parse.quote(clean_phone)
    url = f"{BRIXHUB_BASE_URL}/lookup/phone/{encoded_phone}"
    
    try:
        res = requests.get(url, headers=get_headers(), timeout=10)
        return res.json()
    except requests.RequestException as e:
        return {"error": "Erreur de connexion à l'API BrixHub", "details": str(e)}

def search_fullname(fullname):
    parts = fullname.strip().split()
    if len(parts) < 2:
        return {"error": "Veuillez entrer un Prénom ET un Nom (ex: Jean Dupont)."}
    
    prenom = parts[0]
    nom_famille = " ".join(parts[1:])
    
    url = f"{BRIXHUB_BASE_URL}/search"
    payload = {
        "nom_famille": nom_famille,
        "prenom": prenom,
        "flexible": True,
        "per_page": 10
    }
    
    try:
        res = requests.post(url, json=payload, headers=get_headers(), timeout=10)
        return res.json()
    except requests.RequestException as e:
        return {"error": "Erreur de connexion à l'API BrixHub", "details": str(e)}


# --- ROUTES FLASK ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    search_type = data.get('module', 'email')
    
    if not query:
        return jsonify({"error": "Veuillez entrer une valeur à chercher."}), 400

    if search_type == 'email':
        results = search_email(query)
    elif search_type == 'phone':
        results = search_phone(query)
    elif search_type == 'fullname':
        results = search_fullname(query)
    else:
        return jsonify({"error": "Type de recherche inconnu."}), 400
        
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
