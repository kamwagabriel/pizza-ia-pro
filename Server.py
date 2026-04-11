from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import os
import pandas as pd
import io

app = Flask(__name__)

# Base de données temporaire (se vide au redémarrage)
orders = []
total_ca = 0.0
stats = {"livraison": 0, "emporter": 0}

@app.route('/')
def index():
    # On trie pour avoir la plus récente en haut
    sorted_orders = sorted(orders, key=lambda x: x['id'], reverse=True)
    return render_template('index.html', orders=sorted_orders, ca=total_ca, stats=stats)

@app.route('/webhook_vapi', methods=['POST'])
def webhook_vapi():
    global total_ca
    data = request.json
    if not data:
        return jsonify({"error": "No data"}), 400

    # Extraction des données envoyées par l'IA
    nom = data.get('nom') or data.get('client') or 'Client Inconnu'
    commande = data.get('commande') or 'Pizza'
    adresse = data.get('adresse') or 'À emporter'

    # Logique métier
    total_ca += 12.0 # Prix fixe par défaut
    
    # Détection automatique du type de commande
    est_livraison = any(word in adresse.lower() for word in ["rue", "ave", "bd", "place", "route", "allée"]) or len(adresse) > 10
    
    if est_livraison:
        stats["livraison"] += 1
        type_cmd = "LIVRAISON"
        maps_url = f"https://www.google.com/maps/search/?api=1&query={adresse.replace(' ', '+')}"
    else:
        stats["emporter"] += 1
        type_cmd = "EMPORTER"
        maps_url = None

    nouvelle_commande = {
        "id": len(orders) + 1,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "heure": datetime.now().strftime("%H:%M"),
        "client": nom,
        "commande": commande,
        "adresse": adresse,
        "type": type_cmd,
        "maps_url": maps_url,
        "prix": 12.0
    }

    orders.append(nouvelle_commande)
    return jsonify({"message": "Commande reçue"}), 200

@app.route('/export_excel')
def export_excel():
    if not orders:
        return "Aucune vente aujourd'hui", 400
    
    df = pd.DataFrame(orders)
    # On enlève la colonne technique maps_url pour le tableau propre
    if 'maps_url' in df.columns:
        df = df.drop(columns=['maps_url'])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Ventes')
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"bilan_ventes_{datetime.now().strftime('%d_%m_%Y')}.xlsx"
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
