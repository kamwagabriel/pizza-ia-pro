from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os

# --- 1. INITIALISATION (OBLIGATOIRE EN PREMIER) ---
app = Flask(__name__)

# --- 2. TA BASE DE DONNÉES TEMPORAIRE ---
orders = [
    {"id": 1, "client": "Exemple Jean", "commande": "1 Pizza Reine", "adresse": "12 rue de la Paix", "status": "En attente", "heure": "19:30"},
]

# --- 3. TES ROUTES (LES DÉCORATEURS @app.route) ---

@app.route('/')
def index():
    sorted_orders = sorted(orders, key=lambda x: x['id'], reverse=True)
    return render_template('index.html', orders=sorted_orders)

@app.route('/webhook_vapi', methods=['POST'])
def webhook_vapi():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    # On récupère les infos (flexibilité sur les noms de cases)
    nom_client = data.get('nom') or data.get('client') or 'Client Inconnu'
    details_commande = data.get('commande') or 'Commande non précisée'
    adresse_client = data.get('adresse') or 'À emporter'

    nouvelle_commande = {
        "id": len(orders) + 1,
        "client": nom_client,
        "commande": details_commande,
        "adresse": adresse_client,
        "status": "En attente",
        "heure": datetime.now().strftime("%H:%M")
    }

    orders.append(nouvelle_commande)
    return jsonify({"message": "Commande enregistrée"}), 200

# Tu peux garder tes autres routes (update_status, etc.) ici...

# --- 4. LANCEMENT DU SERVEUR ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
