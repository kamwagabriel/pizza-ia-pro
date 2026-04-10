from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# Liste pour stocker les commandes (se vide si le serveur redémarre)
orders = [
    {"id": 1, "client": "Exemple Jean", "commande": "1 Pizza Reine", "adresse": "12 rue de la Paix", "status": "En attente", "heure": "19:30"},
]

@app.route('/')
def index():
    # Affiche les commandes, les plus récentes en premier
    sorted_orders = sorted(orders, key=lambda x: x['id'], reverse=True)
    return render_template('index.html', orders=sorted_orders)

# --- ROUTE POUR LE FORMULAIRE MANUEL ---
@app.route('/add_order', methods=['POST'])
def add_order():
    client = request.form.get('client')
    commande = request.form.get('commande')
    adresse = request.form.get('adresse')
    
    if client and commande:
        new_order = {
            "id": len(orders) + 1,
            "client": client,
            "commande": commande,
            "adresse": adresse if adresse else "À emporter",
            "status": "En attente",
            "heure": datetime.now().strftime("%H:%M")
        }
        orders.append(new_order)
    return jsonify({"status": "success"})

# --- ROUTE POUR L'IA VOCALE (Vapi Webhook) ---
@app.route('/webhook_vapi', methods=['POST'])
def webhook_vapi():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    # L'IA extrait ces infos de l'appel
    nom_client = data.get('nom', 'Client Inconnu')
    details_commande = data.get('commande', 'Commande non précisée')
    adresse_client = data.get('adresse', 'À emporter')

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

# --- CHANGEMENT DE STATUT ---
@app.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    for order in orders:
        if order['id'] == order_id:
            if order['status'] == "En attente":
                order['status'] = "En préparation"
            elif order['status'] == "En préparation":
                order['status'] = "Prêt / Livré"
            return jsonify({"status": "updated"})
    return jsonify({"error": "Not found"}), 404

# --- LANCEMENT DU SERVEUR (Configuré pour Render) ---
if __name__ == '__main__':
    # Render utilise la variable d'environnement PORT
    port = int(os.environ.get("PORT", 10000))
    # host='0.0.0.0' est OBLIGATOIRE pour Render
    app.run(host='0.0.0.0', port=port)
