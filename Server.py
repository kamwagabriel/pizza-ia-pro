@app.route('/webhook_vapi', methods=['POST'])
def webhook():
    # 1. On récupère les données
    data = request.json
    print(f"DONNÉES REÇUES : {data}") # Cela va s'afficher dans tes logs Render

    # 2. On extrait les infos (avec des valeurs par défaut si vide)
    nouveau_nom = data.get('nom', 'Inconnu')
    nouvelle_adresse = data.get('adresse', 'Non précisée')
    nouvelle_commande = data.get('commande', 'Vide')

    # 3. On crée le dictionnaire de la commande
    commande_complete = {
        "nom": nouveau_nom,
        "adresse": nouvelle_adresse,
        "commande": nouvelle_commande
    }

    # 4. On l'ajoute à ta liste (la variable qui remplit ton tableau)
    commandes.append(commande_complete)

    # 5. On répond à Vapi pour qu'il soit content
    return jsonify({"message": "Commande enregistrée", "status": "success"}), 200
