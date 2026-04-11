from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import os
import pandas as pd
import io
from twilio.rest import Client # Pour les SMS

app = Flask(__name__)

# --- CONFIGURATION TWILIO ---
TWILIO_SID = 'TON_SID_ICI'
TWILIO_TOKEN = 'TON_TOKEN_ICI'
TWILIO_PHONE = 'TON_NUMERO_TWILIO'

# --- DONNÉES ---
orders = []
total_ca = 0.0
stats = {"livraison": 0, "emporter": 0}
livreurs = ["En cuisine", "Momo", "Yassine", "Sarah"] # Liste des livreurs

@app.route('/')
def index():
    # Calcul du temps d'attente estimé (10 min par commande en cours)
    active_orders = [o for o in orders if o.get('status') != 'Servi']
    wait_time = len(active_orders) * 10
    
    sorted_orders = sorted(orders, key=lambda x: x['id'], reverse=True)
    return render_template('index.html', 
                           orders=sorted_orders, 
                           ca=total_ca, 
                           stats=stats, 
                           wait_time=wait_time,
                           livreurs=livreurs)

@app.route('/webhook_vapi', methods=['POST'])
def webhook_vapi():
    global total_ca
    data = request.json
    if not data: return jsonify({"error": "No data"}), 400

    nom = data.get('nom') or data.get('client') or 'Client Inconnu'
    commande = data.get('commande') or 'Pizza'
    adresse = data.get('adresse') or 'À emporter'
    telephone = data.get('phone') # Récupéré de Vapi pour le SMS

    total_ca += 12.0
    
    est_livraison = any(word in adresse.lower() for word in ["rue", "ave", "bd", "place", "route"]) or len(adresse) > 8
    type_cmd = "LIVRAISON" if est_livraison else "EMPORTER"
    
    if est_livraison: stats["livraison"] += 1
    else: stats["emporter"] += 1

    nouvelle_commande = {
        "id": len(orders) + 1,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "heure": datetime.now().strftime("%H:%M"),
        "client": nom,
        "phone": telephone,
        "commande": commande,
        "adresse": adresse,
        "type": type_cmd,
        "status": "En attente",
        "livreur": "En cuisine",
        "maps_url": f"https://www.google.com/maps/search/?api=1&query={adresse.replace(' ', '+')}" if est_livraison else None
    }

    orders.append(nouvelle_commande)
    
    # OPTIONNEL : Envoyer un SMS auto à la commande
    # send_sms(telephone, f"Allo {nom}, ta pizza est reçue ! Elle sera prête dans environ {len(orders)*10} min.")

    return jsonify({"message": "OK"}), 200

# --- ENVOI DE SMS ---
@app.route('/send_status_sms', methods=['POST'])
def send_status_sms():
    data = request.json
    phone = data.get('phone')
    msg = data.get('message')
    if phone and TWILIO_SID != 'TON_SID_ICI':
        try:
            client = Client(TWILIO_SID, TWILIO_TOKEN)
            client.messages.create(body=msg, from_=TWILIO_PHONE, to=phone)
            return jsonify({"status": "sent"})
        except Exception as e:
            return jsonify({"status": "error", "msg": str(e)})
    return jsonify({"status": "skipped"})

# --- EXPORT EXCEL ---
@app.route('/export_excel')
def export_excel():
    if not orders: return "Vide", 400
    df = pd.DataFrame(orders).drop(columns=['maps_url'], errors='ignore')
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.ms-excel', as_attachment=True, download_name="bilan.xlsx")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
