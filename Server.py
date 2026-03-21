import os
import csv
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pizza_sarcelles_95'

# MODIFICATION 1 : Ajout de async_mode='gevent' pour que le HTTPS de Render ne coupe pas les commandes
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# Le fichier sera stocké sur le serveur Render (Attention: sur le plan gratuit, le fichier s'efface si le serveur redémarre)
JOURNAL_FILE = f"JOURNAL_VENTES_{datetime.now().strftime('%d-%m-%Y')}.csv"

def initialiser_fichier():
    if not os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['HEURE', 'COMMANDE (PIZZAS + TAILLES)', 'TYPE', 'TOTAL'])
        print(f"✅ Journal Excel prêt : {JOURNAL_FILE}")

initialiser_fichier()

# MODIFICATION 2 : Route d'accueil (Render cherche '/' par défaut)
@app.route('/')
def cashier():
    return render_template('cashier.html')

@app.route('/new_order_webhook', methods=['POST'])
def new_order():
    data = request.json
    socketio.emit('new_order', data)
    return {"status": "ok"}, 200

@socketio.on('delete_order')
def handle_delete(data):
    try:
        with open(JOURNAL_FILE, mode='a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow([
                datetime.now().strftime("%H:%M"),
                data.get('details'),
                data.get('type').upper(),
                f"{data.get('total')} €"
            ])
        print(f"💾 Archivé dans Excel : {data.get('total')}€")
    except Exception as e:
        print(f"❌ Erreur Excel : {e}")

# MODIFICATION 3 : Récupération du port dynamique de Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)