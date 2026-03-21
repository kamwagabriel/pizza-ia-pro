import os
import csv
from datetime import datetime
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pizza_sarcelles_95'

# Configuration pour Render : on autorise toutes les origines pour le SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Nom du fichier Excel (Journal des ventes du jour)
JOURNAL_FILE = f"JOURNAL_VENTES_{datetime.now().strftime('%d-%m-%Y')}.csv"

def initialiser_fichier():
    if not os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['HEURE', 'DETAILS', 'TYPE', 'TOTAL'])
        print(f"✅ Journal Excel prêt : {JOURNAL_FILE}")

initialiser_fichier()

# --- ROUTES (LES PAGES) ---

# 1. La Console de Contrôle (Le tableau de bord bleu nuit pour le patron)
@app.route('/')
def index():
    return render_template('index.html')

# 2. La Caisse (Ta télécommande avec les boutons Orange/Vert/Bleu)
@app.route('/cashier')
def cashier():
    return render_template('cashier.html')

# --- GESTION DES COMMANDES (COMMUNICATION) ---

@socketio.on('new_order')
def handle_new_order(data):
    # On renvoie la commande à TOUT LE MONDE (pour qu'elle apparaisse sur la console)
    emit('new_order', data, broadcast=True)
    print(f"🍕 Nouvelle commande reçue de : {data.get('nom')}")

@socketio.on('delete_order')
def handle_delete(data):
    # Cette partie enregistre la vente dans le fichier Excel quand tu cliques sur "FINIR"
    try:
        with open(JOURNAL_FILE, mode='a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow([
                datetime.now().strftime("%H:%M"),
                data.get('details', 'N/A'),
                data.get('type', 'N/A').upper(),
                f"{data.get('total', 0)} €"
            ])
        print(f"💾 Vente archivée dans le journal Excel")
    except Exception as e:
        print(f"❌ Erreur lors de l'écriture Excel : {e}")

# --- LANCEMENT DU SERVEUR ---

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    # Le paramètre allow_unsafe_werkzeug=True corrige l'erreur rouge sur Render
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
