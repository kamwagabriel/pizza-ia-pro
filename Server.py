from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import os
import pandas as pd
import io

app = Flask(__name__)

# Base de données temporaire
orders = []
total_ca = 0.0

@app.route('/')
def index():
    active_orders = [o for o in orders if o.get('status') != 'Archivé']
    sorted_orders = sorted(active_orders, key=lambda x: x['id'], reverse=True)
    return render_template('index.html', orders=sorted_orders, ca=total_ca)

@app.route('/webhook_vapi', methods=['POST'])
def webhook_vapi():
    global total_ca
    data = request.json
    if not data: return jsonify({"error": "No data"}), 400

    # 1. RÉCUPÉRATION DU PRIX
    prix_ia = data.get('prix') or data.get('price') or data.get('total')
    try:
        valeur_prix = float(prix_ia)
    except (TypeError, ValueError):
        valeur_prix = 0.0
    total_ca += valeur_prix

    # 2. NETTOYAGE DU TEXTE COMMANDE
    raw_cmd = data.get('commande') or data.get('order') or "Détails non transmis"
    if isinstance(raw_cmd, (list, dict)):
        commande_txt = str(raw_cmd).replace('[','').replace(']','').replace('{','').replace('}','').replace("'", "")
    else:
        commande_txt = str(raw_cmd)

    # 3. CALCUL DE L'ATTENTE (10 min par ticket actif)
    commandes_actives = [o for o in orders if o['status'] != 'Archivé']
    attente_estimee = (len(commandes_actives) + 1) * 10

    # 4. LOGIQUE LIVRAISON / EMPORTER
    adresse = data.get('adresse', 'À emporter')
    est_livraison = any(word in adresse.lower() for word in ["rue", "ave", "bd", "place", "route", "allée"]) or len(adresse) > 10

    orders.append({
        "id": len(orders) + 1,
        "heure": datetime.now().strftime("%H:%M"),
        "client": data.get('nom') or data.get('customer') or 'Client',
        "commande": commande_txt,
        "adresse": adresse,
        "type": "LIVRAISON" if est_livraison else "EMPORTER",
        "prix": valeur_prix,
        "attente": attente_estimee,
        "status": "En attente",
        "maps_url": f"https://www.google.com/maps/search/?api=1&query={adresse.replace(' ', '+')}" if est_livraison else None
    })
    return jsonify({"status": "ok"}), 200

@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.json
    for o in orders:
        if o['id'] == int(data['id']):
            o['status'] = data['status']
            break
    return jsonify({"status": "updated"})

@app.route('/export_excel')
def export_excel():
    try:
        if not orders: return "Aucune donnée", 400
        df = pd.DataFrame(orders).drop(columns=['maps_url'], errors='ignore')
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Ventes_IA')
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name=f"cloture_{datetime.now().strftime('%d_%m')}.xlsx")
    except Exception as e:
        return f"Erreur : {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
