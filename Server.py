import os
import csv
from datetime import datetime
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pizza_sarcelles_95'

# Utilisation du mode threading pour plus de stabilité sur Render
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Fichier journal des ventes
JOURNAL_FILE = f"JOURNAL_VENTES_{datetime.now().strftime('%d-%m-%Y')}.csv"

def initialiser_fichier():
    if not os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['HEURE', 'DETAILS', 'TYPE', 'TOTAL'])
        print(f"✅ Journal Excel prêt : {JOURNAL_FILE}")

initialiser_fichier()

# --- ROUTES ---

# 1. La Console de Contrôle (Le tableau de bord sombre)
@app.route('/')
def index():
    return render_template('index.html')

# 2. La Caisse (Tes 3 boutons Orange/Vert/Bleu)
@app.route('/cashier')
def cashier():
    return render_template('cashier.html')

# --- GESTION DES COMMANDES ---

@socketio.on('new_order')
def handle_new_order(data):
    # On renvoie la commande à tout le monde (pour qu'elle apparaisse sur la console)
    emit('new_order', data, broadcast=True)
    print(f"🍕 Nouvelle commande reçue : {data.get('nom')}")

@socketio.on('delete_order')
def handle_delete(data):
    try:
        with open(JOURNAL_FILE, mode='a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow([
                datetime.now().strftime("%H:%M"),
                data.get('details', 'N/A'),
                data.get('type', 'N/A').upper(),
                f"{data.get('total', 0)} €"
            ])
        print(f"💾 Archivé dans Excel")
    except Exception as e:
        print(f"❌ Erreur Excel : {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)