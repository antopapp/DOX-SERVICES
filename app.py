from flask import Flask, jsonify, request, render_template
import requests
import re
import os

app = Flask(__name__)

# --- MODULES DE RECHERCHE AVEC DONNÉES PUBLIQUES ---

def search_by_email(email):
    # Validation du format email
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return {"error": "Format d'adresse e-mail invalide."}
    
    username = email.split('@')[0]
    domain = email.split('@')[1]
    
    # 1. On réutilise la recherche de pseudo sur la première partie de l'email
    sites = {
        "GitHub": f"https://github.com/{username}",
        "Reddit": f"https://www.reddit.com/user/{username}",
        "Pinterest": f"https://www.pinterest.com/{username}"
    }
    
    found_profiles = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for platform, url in sites.items():
        try:
            res = requests.get(url, headers=headers, timeout=4)
            if res.status_code == 200:
                found_profiles.append({"platform": platform, "url": url})
        except requests.RequestException:
            pass

    return {
        "email": email,
        "username_extracted": username,
        "domain": domain,
        "possible_profiles": found_profiles if found_profiles else "Aucun profil public direct trouvé"
    }

def search_by_phone(phone):
    # Nettoyage du numéro (ne garder que les chiffres et le +)
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
    if len(clean_phone) < 8:
        return {"error": "Numéro de téléphone trop court ou invalide."}
        
    # Analyse basique de la structure du numéro
    country = "Inconnu"
    if clean_phone.startswith("+33") or clean_phone.startswith("06") or clean_phone.startswith("07") or clean_phone.startswith("01"):
        country = "France (+33)"
    elif clean_phone.startswith("+1"):
        country = "USA / Canada (+1)"
    elif clean_phone.startswith("+32"):
        country = "Belgique (+32)"
    elif clean_phone.startswith("+41"):
        country = "Suisse (+41)"

    return {
        "phone_input": phone,
        "formatted": clean_phone,
        "detected_country": country,
        "note": "Pour des détails plus approfondis (opérateur, fuites de données), connecte ton API privée."
    }

def search_by_fullname(fullname):
    parts = fullname.strip().split()
    if len(parts) < 2:
        return {"error": "Veuillez entrer au moins un Nom ET un Prénom."}
    
    firstname = parts[0]
    lastname = " ".join(parts[1:])
    
    # Génération de formats de recherche ou requêtes suggérées
    return {
        "query": fullname,
        "firstname": firstname,
        "lastname": lastname,
        "search_links": {
            "Google_Exact": f"https://www.google.com/search?q=\"{firstname}+{lastname}\"",
            "LinkedIn": f"https://www.google.com/search?q=site:linkedin.com/in/+\"{firstname}+{lastname}\"",
            "Twitter_X": f"https://twitter.com/search?q={firstname}%20{lastname}&f=user"
        }
    }


# --- ROUTES SERVER FLASK ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query', '').strip()
    search_type = data.get('module', 'email')
    
    if not query:
        return jsonify({"error": "Veuillez entrer une valeur à chercher."}), 400

    # Aiguillage selon le type de recherche
    if search_type == 'email':
        results = search_by_email(query)
    elif search_type == 'phone':
        results = search_by_phone(query)
    elif search_type == 'fullname':
        results = search_by_fullname(query)
    else:
        return jsonify({"error": "Type de recherche non pris en charge."}), 400
        
    return jsonify({"status": "success", "type": search_type, "results": results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)