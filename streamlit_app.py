
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import math
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression


# Configuration de la page
st.set_page_config(page_title="ERP Lots", layout="wide")

# Connexion à la base de données
conn = sqlite3.connect("erp_lots", check_same_thread=False)
cursor = conn.cursor()

# Création des tables si elles n'existent pas

cursor.execute("""
CREATE TABLE IF NOT EXISTS utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifiant TEXT UNIQUE,
    mot_de_passe TEXT,
    role TEXT,
    doit_changer_mdp INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS lots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_lot TEXT,
    type_lot TEXT,
    quantite INTEGER,
    date_production TEXT,
    date_enregistrement TEXT,
    filiale TEXT,
    impression_pin TEXT,
    nombre_pin INTEGER,
    cartes_a_tester INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS controle_qualite (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id INTEGER,
    type_carte TEXT,
    quantite INTEGER,
    quantite_a_tester INTEGER,
    date_controle TEXT,
    remarque TEXT,
    resultat TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS agences_livraison (
    pays TEXT PRIMARY KEY,
    agence TEXT
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS livreurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agence TEXT,
    nom TEXT,
    prenom TEXT,
    contact TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS references_expedition (
    pays TEXT PRIMARY KEY,
    reference TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS expedition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id INTEGER,
    pays TEXT,
    statut TEXT,
    bordereau TEXT,
    reference TEXT,
    agence TEXT,
    agent_id INTEGER,
    date_expedition TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS droits_utilisateur (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifiant TEXT,
    onglet TEXT,
    lecture INTEGER DEFAULT 0,
    execution INTEGER DEFAULT 0,
    FOREIGN KEY (identifiant) REFERENCES utilisateurs(identifiant)
)
""")

conn.commit()

import hashlib
# Fonction de hachage du mot de passe
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Création de la table utilisateurs
cursor.execute("""
CREATE TABLE IF NOT EXISTS utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifiant TEXT UNIQUE,
    mot_de_passe TEXT,
    role TEXT,
    doit_changer_mdp INTEGER
)
""")
conn.commit()

# Création automatique du compte admin si inexistant
cursor.execute("SELECT COUNT(*) FROM utilisateurs WHERE role = 'admin'")
admin_exists = cursor.fetchone()[0]

if admin_exists == 0:
    cursor.execute("""
    INSERT INTO utilisateurs (identifiant, mot_de_passe, role, doit_changer_mdp)
    VALUES (?, ?, ?, ?)
    """, ("admin", hash_password("admin123"), "admin", 1))
    conn.commit()

# Fonction de connexion avec affichage centré
def login_form():
    st.markdown("<h2 style='text-align: center;'>🔐 Connexion à l'application ERP</h2>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'>Veuillez entrer vos identifiants pour accéder à l'application.</div>", unsafe_allow_html=True)
    st.divider()
    with st.form("login_form"):
        st.image("imageExcelis.png", width=200)
        st.markdown("<h6 style='text-align: center; color: grey;'><em>Département Cartes et Partenariat DCP</em></h6>", unsafe_allow_html=True)
    
        st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        with col2:
            identifiant = st.text_input("Identifiant")
            mot_de_passe = st.text_input("Mot de passe", type="password")
            submit = st.form_submit_button("✅ Se connecter")
        st.markdown("</div>", unsafe_allow_html=True)

    if submit:
        cursor.execute("SELECT mot_de_passe, role, doit_changer_mdp FROM utilisateurs WHERE identifiant = ?", (identifiant,))
        result = cursor.fetchone()
        if result and result[0] == hash_password(mot_de_passe):
            st.session_state["utilisateur"] = identifiant
            st.session_state["role"] = result[1]
            st.session_state["doit_changer_mdp"] = result[2]
            st.success("✅ Connexion réussie")
            st.rerun()
        else:
            st.error("❌ Identifiants incorrects")

def formulaire_droits_utilisateur(identifiant):
    st.markdown("### 🔐 Définir les droits d'accès par onglet")
    for onglet in menu:
        col1, col2 = st.columns(2)
        lecture = col1.checkbox(f"📖 Lecture : {onglet}", key=f"lecture_{onglet}")
        execution = col2.checkbox(f"⚙️ Exécution : {onglet}", key=f"exec_{onglet}")
        if lecture or execution:
            cursor.execute("""
                INSERT INTO droits_utilisateur (identifiant, onglet, lecture, execution)
                VALUES (?, ?, ?, ?)
            """, (identifiant, onglet, int(lecture), int(execution)))
    conn.commit()

# Fonction de changement de mot de passe
def changer_mot_de_passe():
    st.warning("🔄 Vous devez changer votre mot de passe.")
    nouveau_mdp = st.text_input("Nouveau mot de passe", type="password")
    confirmer_mdp = st.text_input("Confirmer le mot de passe", type="password")
    if st.button("✅ Mettre à jour"):
        if nouveau_mdp == confirmer_mdp and nouveau_mdp != "":
            cursor.execute("UPDATE utilisateurs SET mot_de_passe = ?, doit_changer_mdp = 0 WHERE identifiant = ?",
                           (hash_password(nouveau_mdp), st.session_state["utilisateur"]))
            conn.commit()
            st.success("🔐 Mot de passe mis à jour avec succès.")
            st.session_state["doit_changer_mdp"] = 0
            st.rerun()
        else:
            st.error("❌ Les mots de passe ne correspondent pas ou sont vides.")

# Blocage de l'accès si non connecté
if "utilisateur" not in st.session_state:
    login_form()
    st.stop()

# Blocage si mot de passe doit être changé
if "doit_changer_mdp" in st.session_state and st.session_state["doit_changer_mdp"] == 1:
    changer_mot_de_passe()
    st.stop()



references_data = {
    "Côte d'Ivoire": "CORIS BANK INTERNATIONAL COTE D'IVOIRE Abidjan Treichville Zone 1, Bld VGE Angle Bld Delafosse, 01 BP 4690 01, COTE D'IVOIRE Tel : +225 27 20209492 A l'attention de Mr PHILIP JUNIOR N'GUESSAN.",
    "Guinée Conakry": "CORIS BANK INTERNATIONAL GUINEE CONAKRY Boulevard DIALLO, angle av. de la Gare, Kaloum, Almamya BP  : 3048 République de Micro Tel : (+224) 610000818 A l'attention de Mr. SANDAOGO Guy Damascène Email : gsandaogo@coris-bank.com.",
    "Bénin": "CORIS BANK INTERNATIONAL BENIN Lot 122 Parcelle ZA, Avenue Steinmetz 01 BP : 5783 Cotonou, Bénin Tel Std : (+229) 63 63 08 59 A l'attention de Mr. Nestor M.ZANKPO LAGBO.",
    "Guinée Bissau": "BISSAU, CORIS BANK INTERNATIONAL Sede Praça dos Herois Nacionais, Bissau CP 390-1031 Tel : (+245) 95 56 010 10 / 95 70 558 57 A l'attention de Mr. COULIBALY FOYTIENHORO LAURENT Email : flcoulibaly@coris-bank.com.",
    "Mali": "CORIS BANK INTERNATIONAL MALI RUE : +223 20 70 59 00 / Mobile : +223 70 22 87 39 A l'attention de Mr. CHEICK OUMAR DIARRA.",
    "Niger": "CORIS BANK INTERNATIONAL NIGER Bld de la liberté, Rue N° NM-2 / BP 10377 Niamey-Niger  Tel : +227 20 34 04 08 : Mobile : +227 96 40 09 90 Email : hfaycal@coris-bank.com A l'attention de Mme FAYCAL HALIMATOU SOUNNA.",
    "Sénégal": "CORIS BANK INTERNATIONAL SENEGAL Immeuble Futura, Corniche Ouest des Almadies, Dakar BP 14 310, SENEGAL Tel : +221 33 829 66 93 / Fax : +221 33 823 88 88 Mobile : +221 78 425 8230 A l'attention de Mme BEATRICE NGOM.",
    "Togo": "CORIS BANK INTERNATIONAL TOGO 1258 Bd du 13 Janvier, Béniglato 01 BP 4032 Lomé TOGO Tel : +228 22 20 82 82  Mobile : +228 93 88 82 12 A l'attention de Mr YAO BENJAMIN SIKA Email : ysika@coris-bank.com"
}

for pays, ref in references_data.items():
    try:
        cursor.execute("INSERT INTO references_expedition (pays, reference) VALUES (?, ?)", (pays, ref))
    except sqlite3.IntegrityError:
        pass
conn.commit()


agences_initiales = {
    "Burkina Faso": "Burkina/Coris",
    "Togo": "DHL",
    "Sénégal": "DHL",
    "Niger": "DHL",
    "Guinée Conakry": "DHL",
    "Guinée Bissau": "DHL",
    "Côte d'Ivoire": "CHRONOPOST",
    "Mali": "CHRONOPOST",
    "Bénin": "CHRONOPOST"
}

for pays, agence in agences_initiales.items():
    try:
        cursor.execute("INSERT INTO agences_livraison (pays, agence) VALUES (?, ?)", (pays, agence))
    except sqlite3.IntegrityError:
        pass  # Ignore si déjà présent
conn.commit()

def module_expedition():
    st.markdown("## 🚚 Préparation des expéditions")
    st.divider()

    # Sélection du lot
    cursor.execute("SELECT id, nom_lot FROM lots")
    lots = cursor.fetchall()
    lot_selectionne = st.selectbox("Sélectionnez un lot à expédier :", lots, format_func=lambda x: x[1])

    if lot_selectionne:
        lot_id = lot_selectionne[0]

        # Choix du pays destinataire
        pays = st.selectbox("Pays destinataire :", [
            "Burkina Faso", "Mali", "Niger", "Côte d'Ivoire", "Sénégal",
            "Bénin", "Togo", "Guinée Conakry", "Guinée Bissau"
        ])

        # Statut d'expédition
        statut = st.radio("Statut d'expédition :", ["En attente", "En cours d'expédition", "Expédié"])

        # Numéro de bordereau
        bordereau = st.text_input("Numéro de bordereau")

        # Référence d'expédition
        cursor.execute("SELECT reference FROM references_expedition WHERE pays = ?", (pays,))
        ref_result = cursor.fetchone()
        reference = ref_result[0] if ref_result else "Référence non disponible"
        st.text_area("📍 Référence d'expédition", value=reference, disabled=True)

        # Agence de livraison
        cursor.execute("SELECT agence FROM agences_livraison WHERE pays = ?", (pays,))
        agence_result = cursor.fetchone()
        agence = agence_result[0] if agence_result else "Agence non définie"
        st.text_input("🚚 Agence de livraison", value=agence, disabled=True)

        
# Sélection de l'agent livreur associé à l'agence
        cursor.execute("SELECT id, nom, prenom FROM livreurs WHERE agence = ?", (agence,))
        agents = cursor.fetchall()

        if agents:
            agent_selectionne = st.selectbox("👤 Sélectionnez un agent livreur :", agents, format_func=lambda x: f"{x[1]} {x[2]}")
            agent_id = agent_selectionne[0]
        else:
            st.warning("Aucun livreur disponible pour cette agence.")
            agent_id = None


        # Enregistrement
            
        if st.button("✅ Enregistrer l'expédition") and agent_id is not None:
            cursor.execute("""
                INSERT INTO expedition (lot_id, pays, statut, bordereau, reference, agence, agent_id, date_expedition)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (lot_id, pays, statut, bordereau, reference, agence, agent_id, str(date.today())))
            conn.commit()
            st.success("✅ Expédition enregistrée avec succès.")


def gestion_comptes_utilisateurs():
    st.markdown("<h2 style='text-align:center;'>🔐 Gestion des comptes utilisateurs</h2>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    if st.session_state.get("role") != "admin":
        st.error("⛔ Accès réservé aux administrateurs.")
        return

    onglet = st.radio("📌 Choisissez une action :", [
        "➕ Ajouter un utilisateur",
        "✏️ Modifier un utilisateur",
        "🔄 Activer/Désactiver un compte",
        "🗑️ Supprimer un utilisateur"
    ])

    # ➕ Ajouter un utilisateur
    if onglet == "➕ Ajouter un utilisateur":
        st.markdown("### ➕ Ajouter un nouvel utilisateur")
        with st.form("form_ajout_utilisateur"):
            col1, col2 = st.columns(2)
            with col1:
                new_id = st.text_input("👤 Identifiant")
                new_role = st.selectbox("🎯 Rôle", ["admin", "operateur"])
            with col2:
                new_pwd = st.text_input("🔑 Mot de passe", type="password")
            submit = st.form_submit_button("✅ Créer le compte")
            if submit:
                if new_id and new_pwd:
                    cursor.execute("SELECT * FROM utilisateurs WHERE identifiant = ?", (new_id,))
                    if cursor.fetchone():
                        st.error("❌ Cet identifiant existe déjà.")
                    else:                      
                        cursor.execute(
                            "INSERT INTO utilisateurs (identifiant, mot_de_passe, role, doit_changer_mdp, actif) VALUES (?, ?, ?, ?, ?)",
                            (new_id, hash_password(new_pwd), new_role, 1, 1)
                        )
                        conn.commit()
                        st.success("✅ Utilisateur ajouté avec succès.")


    # ✏️ Modifier un utilisateur
    
    elif onglet == "✏️ Modifier un utilisateur":
        st.markdown("### ✏️ Modifier les identifiants ou rôle")
        utilisateurs = cursor.execute("SELECT identifiant FROM utilisateurs").fetchall()
        user_list = [u[0] for u in utilisateurs]
        selected_user = st.selectbox("👤 Choisir un utilisateur", user_list)

        with st.form("form_modif_utilisateur"):
            col1, col2 = st.columns(2)
            with col1:
                new_identifiant = st.text_input("🆕 Nouvel identifiant", value=selected_user)
                new_role = st.selectbox("🎯 Nouveau rôle", ["admin", "operateur"])
            with col2:
                new_pwd = st.text_input("🔑 Nouveau mot de passe", type="password")
            submit = st.form_submit_button("✅ Mettre à jour")

            if submit:
                if new_pwd and new_identifiant:
                    if new_identifiant != selected_user:
                        cursor.execute("SELECT * FROM utilisateurs WHERE identifiant = ?", (new_identifiant,))
                        if cursor.fetchone():
                            st.error("❌ Ce nouvel identifiant est déjà utilisé.")
                            st.stop()
                    cursor.execute("""
                        UPDATE utilisateurs
                        SET identifiant = ?, mot_de_passe = ?, role = ?, doit_changer_mdp = 0
                        WHERE identifiant = ?
                    """, (new_identifiant, hash_password(new_pwd), new_role, selected_user))
                    conn.commit()
                    st.success("✅ Utilisateur mis à jour avec succès.")


    # 🔄 Activer/Désactiver un compte
    elif onglet == "🔄 Activer/Désactiver un compte":
        st.markdown("### 🔄 Activer ou désactiver un compte")
        utilisateurs = cursor.execute("SELECT identifiant, actif FROM utilisateurs").fetchall()
        for identifiant, actif in utilisateurs:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"👤 {identifiant} — {'✅ Actif' if actif else '⛔ Inactif'}")
            with col2:
                if st.button("🔁 Basculer", key=identifiant):
                    nouveau_statut = 0 if actif else 1
                    cursor.execute("UPDATE utilisateurs SET actif = ? WHERE identifiant = ?", (nouveau_statut, identifiant))
                    conn.commit()
                    st.rerun()

    # 🗑️ Supprimer un utilisateur
    elif onglet == "🗑️ Supprimer un utilisateur":
        st.markdown("### 🗑️ Supprimer un utilisateur")
        utilisateurs = cursor.execute("SELECT identifiant FROM utilisateurs WHERE identifiant != 'admin'").fetchall()
        user_list = [u[0] for u in utilisateurs]
        selected_user = st.selectbox("👤 Utilisateur à supprimer", user_list)
        if st.button("🗑️ Supprimer"):
            cursor.execute("DELETE FROM utilisateurs WHERE identifiant = ?", (selected_user,))
            conn.commit()
            st.success("✅ Utilisateur supprimé.")




def module_controle_qualite():
    conn = sqlite3.connect("erp_lots", check_same_thread=False)
    cursor = conn.cursor()

    # Sélection du lot
    cursor.execute("SELECT id, nom_lot FROM lots")
    lots = cursor.fetchall()
    lot_selectionne = st.selectbox("Sélectionnez un lot :", lots, format_func=lambda x: x[1])

    if lot_selectionne:
        lot_id = lot_selectionne[0]

        # Sélection des types de cartes
        types_cartes = [
            "challenge", "open", "challenge plus", "access", "visa leader",
            "visa gold encoche", "visa infinite encoche", "visa gold premier",
            "visa infinite premier", "wadia challenge", "wadia open", "wadia challenge plus"
        ]
        types_selectionnes = st.multiselect("Types de cartes dans le lot :", types_cartes)

        quantites = {}
        quantites_a_tester = {}
        total_a_tester = 0

        for type_carte in types_selectionnes:
            qte = st.number_input(f"Quantité pour {type_carte} :", min_value=1, step=1, key=f"qte_{type_carte}")
            quantites[type_carte] = qte

            # Calcul des cartes à tester
            if len(types_selectionnes) == 1:
                test = math.ceil(qte / 50)
            else:
                if qte <= 50:
                    test = 1
                elif qte <= 100:
                    test = 2
                else:
                    test = 3
            quantites_a_tester[type_carte] = test
            total_a_tester += test

        remarque = st.text_area("Remarques / Anomalies", value="RAS")

        resultat_test = st.radio("Résultat du test :", ["Réussite", "Échec"], key="resultat_test")

        if st.button("Enregistrer le contrôle qualité"):
            for type_carte in types_selectionnes:
                cursor.execute("""
                    INSERT INTO controle_qualite (lot_id, type_carte, quantite, quantite_a_tester, date_controle, remarque, resultat)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (lot_id, type_carte, quantites[type_carte], quantites_a_tester[type_carte], str(date.today()), remarque, resultat_test))
            conn.commit()
            st.success("✅ Contrôle qualité enregistré avec succès.")

        # Résumé
        if types_selectionnes:
            st.subheader("📋 Résumé des tests")
            for type_carte in types_selectionnes:
                st.write(f"{type_carte} : {quantites[type_carte]} cartes → {quantites_a_tester[type_carte]} à tester")
            st.write(f"🔢 Total des cartes à tester : {total_a_tester}")


def calcul_paquets_conditionnement(quantite_totale, filiale):
    """
    Calcule le nombre de paquets et le type d'emballage selon la filiale et la quantité.
    Retourne une liste de tuples : (type_emballage, cartes_emballees)
    """
    paquets = []
    capacite = 249 if filiale.lower() == "sénégal" else 500

    reste = quantite_totale
    while reste > 0:
        if reste <= 150:
            type_emballage = "Enveloppe"
            cartes_emballees = reste
        else:
            type_emballage = "Paquet"
            cartes_emballees = min(capacite, reste)
        paquets.append((type_emballage, cartes_emballees))
        reste -= cartes_emballees

    return paquets

def module_conditionnement():
    st.markdown("## 📦 Module de Conditionnement des Cartes")
    st.divider()

    conn = sqlite3.connect("erp_lots", check_same_thread=False)
    cursor = conn.cursor()

    # Création de la table si elle n'existe pas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conditionnement (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_id INTEGER,
        type_lot TEXT,
        filiale TEXT,
        type_emballage TEXT,
        nombre_cartes INTEGER,
        date_conditionnement TEXT,
        operateur TEXT,
        remarque TEXT
    )
    """)
    conn.commit()
   

    # Sélection de la date
    selected_date = st.date_input("📅 Sélectionnez une date", value=date.today())

    # Filtrage des filiales
    cursor.execute("SELECT DISTINCT filiale FROM lots WHERE date_enregistrement = ?", (str(selected_date),))
    filiales = [row[0] for row in cursor.fetchall()]
    if not filiales:
        st.warning("Aucune filiale n'a enregistré de lots à cette date.")
        return

    selected_filiale = st.selectbox("🏢 Sélectionnez une filiale", filiales)

    # Affichage des lots
    cursor.execute("""
        SELECT id, nom_lot, type_lot, quantite FROM lots
        WHERE date_enregistrement = ? AND filiale = ?
    """, (str(selected_date), selected_filiale))
    lots = cursor.fetchall()
    if not lots:
        st.warning("Aucun lot enregistré pour cette filiale à cette date.")
        return

    st.subheader("📋 Lots enregistrés")
    df_lots = pd.DataFrame(lots, columns=["ID", "Nom du lot", "Type de lot", "Quantité"])
    st.dataframe(df_lots)

    # Regroupement par type de lot
    regroupement = {}
    for lot_id, nom_lot, type_lot, quantite in lots:
        regroupement.setdefault(type_lot, []).append((lot_id, nom_lot, quantite))

    for type_lot, lots_groupes in regroupement.items():
        st.markdown(f"### 🎯 Type de lot : {type_lot}")
        total = sum(q for _, _, q in lots_groupes)
        st.write(f"Total cartes : {total}")

        # Spécifications VIP pour les lots ordinaires
        if type_lot.lower() == "ordinaire":
            st.markdown("#### 🏅 Spécifications (cartes VIP)")
            qte_gold = st.number_input("Quantité VISA GOLD", min_value=0, step=1, value=0, key=f"qte_gold_{type_lot}")
            qte_infinite = st.number_input("Quantité VISA INFINITE", min_value=0, step=1, value=0, key=f"qte_infinite_{type_lot}")
            packs_gold = math.ceil(qte_gold)
            packs_infinite = math.ceil(qte_infinite)
            total_packs = packs_gold + packs_infinite
            st.info(f"📦 Packs VIP à conditionner : {total_packs} (Gold: {packs_gold}, Infinite: {packs_infinite})")
            st.write("📤 Emballage : Enveloppes grand format")

        # Conditionnement des lots
        st.markdown("#### 📦 Paquets de conditionnement")
        
        paquets = calcul_paquets_conditionnement(total, selected_filiale)
        for i, (type_emballage, cartes_emballees) in enumerate(paquets, 1):
            st.write(f"📦 Paquet {i} → {cartes_emballees} cartes → {type_emballage}")


        
    if st.button("✅ Enregistrer le conditionnement"):    
        for type_emballage, cartes_emballees in paquets:
            cursor.execute("""
                INSERT INTO conditionnement (lot_id, type_lot, filiale, type_emballage, nombre_cartes, date_conditionnement, operateur, remarque, packs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lots_groupes[0][0], type_lot, selected_filiale, type_emballage,
                cartes_emballees, str(date.today()), "Automatique", "", total_packs
            ))
            conn.commit()
            st.success("✅ Conditionnement enregistré avec succès.")


# Titre principal
st.markdown("<h1 style='text-align: center;'>Gestion des tâches manuelles section DCP</h1>", unsafe_allow_html=True)
st.divider()

# Menu latéral avec icône burger
with st.sidebar:
    st.image("imageExcelis.png", width=200)
    st.markdown("<h6 style='text-align: center; color: grey;'><em>Département Cartes et Partenariat DCP</em></h6>", unsafe_allow_html=True)
    
    menu = st.selectbox("Naviguer vers :", [
        "➕ Enregistrement des lots",
        "📋 Visualisation des lots",
        "✏️ Modification / Suppression",
        "🧪 Contrôle qualité",
        "🗂 Inventaire des tests",
        "📊 Graphiques et Analyses",
        "📦 Conditionnement des cartes",
        "🗂 Inventaire des conditionnements",
        "⚙️ Gestion des agences",
        "🚚 Expédition des lots",
        "📇 Annuaire des livreurs",
        "📦 Visualisation des expéditions",
        "🔐 Gestion des comptes utilisateurs"
    ])

# Section : Enregistrement des lots
if menu == "➕ Enregistrement des lots":
    st.markdown("## ➕ Enregistrement d'un nouveau lot")
    st.divider()
    with st.form("form_enregistrement"):
        col1, col2 = st.columns(2)
        with col1:
            nom_lot = st.text_input("Nom du lot")
            type_lot = st.selectbox("Type de lot", ["Ordinaire", "Émission instantanée", "Renouvellement"])
            quantite = st.number_input("Quantité totale", min_value=1)
            date_production = st.date_input("Date de production", value=date.today())
        with col2:
            date_enregistrement = st.date_input("Date d'enregistrement", value=date.today())
            filiale = st.selectbox("Filiale", ["Burkina Faso", "Mali", "Niger", "Côte d'Ivoire", "Sénégal", "Bénin", "Togo", "Guinée Bissau", "Guinée Conakry"])
            impression_pin = st.radio("Impression de PIN ?", ["Oui", "Non"])
            nombre_pin = st.number_input("Nombre de PIN", min_value=1) if impression_pin == "Oui" else 0

        cartes_a_tester = math.ceil(quantite / 50)
        submitted = st.form_submit_button("✅ Enregistrer le lot")
        if submitted:
            
# Vérification de l'existence du nom de lot
           cursor.execute("SELECT COUNT(*) FROM lots WHERE nom_lot = ?", (nom_lot,))
           if cursor.fetchone()[0] > 0:
               st.error("❌ Ce nom de lot existe déjà. Verifier le nom de lot.")
           else:
               cursor.execute("""
            INSERT INTO lots (nom_lot, type_lot, quantite, date_production, date_enregistrement, filiale, impression_pin, nombre_pin, cartes_a_tester)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nom_lot, type_lot, quantite, str(date_production), str(date_enregistrement), filiale, impression_pin, nombre_pin, cartes_a_tester))
            
               conn.commit()
               st.success("✅ Lot enregistré avec succès.")
               st.rerun()
               

               



# Section : Visualisation des lots
elif menu == "📋 Visualisation des lots":
    st.markdown("## 📋 Liste des lots enregistrés")
    st.divider()
    cursor.execute("SELECT * FROM lots")
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    df = pd.DataFrame(rows, columns=column_names)

    if not df.empty:
        df["date_enregistrement"] = pd.to_datetime(df["date_enregistrement"])

        st.sidebar.header("🔍 Filtres")
        min_date = df["date_enregistrement"].min().date()
        max_date = df["date_enregistrement"].max().date()
        date_range = st.sidebar.date_input("Date d'enregistrement", [min_date, max_date])

        filiales = df["filiale"].unique().tolist()
        filiale_selection = st.sidebar.multiselect("Filiale", filiales, default=filiales)

        types_lot = df["type_lot"].unique().tolist()
        type_selection = st.sidebar.multiselect("Type de lot", types_lot, default=types_lot)

        df_filtered = df[
            (df["date_enregistrement"].dt.date >= date_range[0]) &
            (df["date_enregistrement"].dt.date <= date_range[1]) &
            (df["filiale"].isin(filiale_selection)) &
            (df["type_lot"].isin(type_selection))
        ]

        st.dataframe(df_filtered)
    else:
        st.warning("Aucun lot enregistré dans la base de données.")

# Section : Modification / Suppression
elif menu == "✏️ Modification / Suppression":
    st.markdown("## ✏️ Modifier ou supprimer un lot")
    st.divider()
    cursor.execute("SELECT id, nom_lot FROM lots")
    lots = cursor.fetchall()
    lot_dict = {f"{lot[0]} - {lot[1]}": lot[0] for lot in lots}
    selected_lot = st.selectbox("Sélectionner un lot à modifier ou supprimer", list(lot_dict.keys()))
    lot_id = lot_dict[selected_lot]
    cursor.execute("SELECT * FROM lots WHERE id = ?", (lot_id,))
    lot_data = cursor.fetchone()
    if lot_data:
        with st.form("form_modification"):
            col1, col2 = st.columns(2)
            with col1:
                new_nom = st.text_input("Nom du lot", value=lot_data[1])
                new_type = st.selectbox("Type de lot", ["Ordinaire", "Émission instantanée", "Renouvellement"], index=["Ordinaire", "Émission instantanée", "Renouvellement"].index(lot_data[2]))
                new_quantite = st.number_input("Quantité totale", min_value=1, value=lot_data[3])
                new_date_prod = st.date_input("Date de production", value=pd.to_datetime(lot_data[4]).date())
            with col2:
                new_date_enr = st.date_input("Date d'enregistrement", value=pd.to_datetime(lot_data[5]).date())
                new_filiale = st.selectbox("Filiale", ["Burkina Faso", "Mali", "Niger", "Côte d'Ivoire", "Sénégal", "Bénin", "Togo", "Guinée Bissau", "Guinée Conakry"], index=["Burkina Faso", "Mali", "Niger", "Côte d'Ivoire", "Sénégal", "Bénin", "Togo", "Guinée Bissau", "Guinée Conakry"].index(lot_data[6]))
                new_impression = st.radio("Impression de PIN ?", ["Oui", "Non"], index=["Oui", "Non"].index(lot_data[7]))
                default_pin = lot_data[8] if lot_data[7] == "Oui" else 1
                new_nombre_pin = st.number_input("Nombre de PIN", min_value=1, value=default_pin) if new_impression == "Oui" else 0

            new_cartes_test = math.ceil(new_quantite / 50)
            mod_submit = st.form_submit_button("✅ Modifier le lot")
            if mod_submit:
                cursor.execute("""
                    UPDATE lots SET nom_lot=?, type_lot=?, quantite=?, date_production=?, date_enregistrement=?, filiale=?, impression_pin=?, nombre_pin=?, cartes_a_tester=?
                    WHERE id=?
                """, (new_nom, new_type, new_quantite, str(new_date_prod), str(new_date_enr), new_filiale, new_impression, new_nombre_pin, new_cartes_test, lot_id))
                conn.commit()
                st.success("✅ Lot modifié avec succès.")
                st.rerun()

        if st.button("🗑️ Supprimer ce lot"):
            cursor.execute("DELETE FROM lots WHERE id = ?", (lot_id,))
            conn.commit()
            st.warning("🗑️ Lot supprimé avec succès.")
            st.rerun()

# Section : Contrôle qualité
elif menu == "🧪 Contrôle qualité":
    st.markdown("## 🧪 Enregistrement d'un contrôle qualité")
    st.divider()
    # Appel de la fonction existante
    module_controle_qualite()

# Section : Inventaire des tests
elif menu == "🗂 Inventaire des tests":
    st.markdown("## 🗂 Inventaire des tests de contrôle qualité")
    st.divider()
    # Le code de cette section sera repris depuis le fichier existant
    if "mod_test_id" not in st.session_state:
        st.session_state["mod_test_id"] = None


    conn = sqlite3.connect("erp_lots", check_same_thread=False)
    cursor = conn.cursor()

    query = """
    SELECT cq.id, cq.date_controle, l.nom_lot, l.filiale, cq.type_carte, cq.quantite, cq.quantite_a_tester, cq.resultat, cq.remarque
    FROM controle_qualite cq
    JOIN lots l ON cq.lot_id = l.id
    """
    df = pd.read_sql_query(query, conn)
    
# Conversion de la date et ajout des colonnes temporelles
    df["date_controle"] = pd.to_datetime(df["date_controle"])
    df["Année"] = df["date_controle"].dt.year
    df["Mois"] = df["date_controle"].dt.month_name()
    df["Mois"] = df["Mois"].map({'January': 'Janvier', 'February': 'Février', 'March': 'Mars', 'April': 'Avril', 'May': 'Mai', 'June': 'Juin', 'July': 'Juillet', 'August': 'Août', 'September': 'Septembre', 'October': 'Octobre', 'November': 'Novembre', 'December': 'Décembre'})
    df["Trimestre"] = df["date_controle"].dt.quarter
    df["Semaine"] = df["date_controle"].dt.isocalendar().week
    df["Jour"] = df["date_controle"].dt.day
    df["Jour_Semaine"] = df["date_controle"].dt.day_name()
    df["Jour_Semaine"] = df["Jour_Semaine"].map({'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi', 'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'})

    if df.empty:
        st.warning("Aucun test de contrôle qualité enregistré.")
    else:
        df["date_controle"] = pd.to_datetime(df["date_controle"])

        st.sidebar.header("🔎 Filtres Inventaire")
        date_min = df["date_controle"].min().date()
        date_max = df["date_controle"].max().date()
        date_range = st.sidebar.date_input("Période de contrôle", [date_min, date_max])

        lots = df["nom_lot"].unique().tolist()
        lot_selection = st.sidebar.multiselect("Nom du lot", lots, default=lots)

        filiales = df["filiale"].unique().tolist()
        filiale_selection = st.sidebar.multiselect("Filiale", filiales, default=filiales)

        resultats = df["resultat"].unique().tolist()
        resultat_selection = st.sidebar.multiselect("Résultat", resultats, default=resultats)

        df_filtered = df[
            (df["date_controle"].dt.date >= date_range[0]) &
            (df["date_controle"].dt.date <= date_range[1]) &
            (df["nom_lot"].isin(lot_selection)) &
            (df["filiale"].isin(filiale_selection)) &
            (df["resultat"].isin(resultat_selection))
        ]
        
        st.dataframe(df_filtered, use_container_width=True)
        st.subheader("📊 Résumé des tests")
        total_testees = df_filtered["quantite_a_tester"].sum()
        nb_reussites = df_filtered[df_filtered["resultat"] == "Réussite"].shape[0]
        nb_echecs = df_filtered[df_filtered["resultat"] == "Échec"].shape[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total cartes testées", total_testees)
        col2.metric("Tests réussis", nb_reussites)
        col3.metric("Tests échoués", nb_echecs)

        st.subheader("🛠️ Gestion des tests enregistrés")

# Affichage des tests avec actions
        for index, row in df_filtered.iterrows():
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.write(f"📄 **{row['nom_lot']}** | {row['filiale']} | {row['type_carte']} | {row['quantite']} cartes | {row['quantite_a_tester']} à tester | {row['resultat']} | {row['remarque']}")
            with col2:
                
                if st.button("✏️ Modifier", key=f"mod_{index}"):
                    st.session_state["mod_test_id"] = row["id"]
                    st.rerun()

            # Formulaire de modification
                if st.session_state["mod_test_id"] == row["id"]:
                    with st.form(f"form_mod_{index}"):
                        new_type = st.text_input("Type de carte", value=row["type_carte"])
                        new_quantite = st.number_input("Nouvelle quantité", value=row["quantite"], min_value=1)
                        new_quantite_test = st.number_input("Nouvelle quantité à tester", value=row["quantite_a_tester"], min_value=1)
                        new_resultat = st.selectbox("Résultat", ["Réussite", "Échec"], index=["Réussite", "Échec"].index(row["resultat"]))
                        new_remarque = st.text_area("Remarque", value=row["remarque"])
                        submit_mod = st.form_submit_button("✅ Enregistrer les modifications")
                        
                        if submit_mod:
                            cursor.execute("""
                                UPDATE controle_qualite
                                SET type_carte=?, quantite=?, quantite_a_tester=?, resultat=?, remarque=?
                                WHERE id=?
                            """, (new_type, new_quantite, new_quantite_test, new_resultat, new_remarque, row["id"]))
                            conn.commit()
                            st.success("✅ Test modifié avec succès.")
                            st.session_state["mod_test_id"] = None  # 🔐 Réinitialise l'état
                            st.rerun()


            with col3:
                if st.button("🗑️ Supprimer", key=f"del_{index}"):
                    cursor.execute("DELETE FROM controle_qualite WHERE id=?", (row["id"],))
                    conn.commit()
                    st.warning("🗑️ Test supprimé.")
                    st.rerun()
    # avec les filtres déplacés dans cette section

# Section : Graphiques et Analyses
elif menu == "📊 Graphiques et Analyses":
    st.markdown("## 📊 Tableau de bord des indicateurs")
    st.divider()
    # Le code de cette section sera repris depuis le fichier existant
    conn = sqlite3.connect("erp_lots", check_same_thread=False)
    cursor = conn.cursor()

    lots_df = pd.read_sql_query("SELECT * FROM lots", conn)
    controle_df = pd.read_sql_query("""
        SELECT cq.*, l.filiale 
        FROM controle_qualite cq 
        JOIN lots l ON cq.lot_id = l.id
    """, conn)

    # KPIs sur les lots
    st.header("Lots Enrégistrés")
    total_lots = len(lots_df)
    total_cartes = lots_df["quantite"].sum()
    moyenne_cartes = lots_df["quantite"].mean()
    lots_par_type = lots_df["type_lot"].value_counts()
    lots_par_filiale = lots_df["filiale"].value_counts()
    lots_avec_pin = lots_df[lots_df["impression_pin"] == "Oui"].shape[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Nombre total de lots", total_lots)
    col2.metric("Total cartes produites", total_cartes)
    col3.metric("Moyenne cartes/lot", f"{moyenne_cartes:.2f}")
    col4.metric("Lots avec impression PIN", lots_avec_pin)

       
    import plotly.graph_objects as go
    import numpy as np

# Connexion à la base de données
    conn = sqlite3.connect("erp_lots", check_same_thread=False)

# Extraction des données réelles depuis la table 'lots'
    query = "SELECT type_lot, SUM(quantite) as total_quantite FROM lots GROUP BY type_lot"
    df = pd.read_sql_query(query, conn)

# Préparation des données pour le graphique
    types_lot = df["type_lot"].tolist()
    quantites = df["total_quantite"].tolist()

# Couleurs pastel
    colors = ['lightblue', 'lightgreen', 'lightpink']

    fig = go.Figure()

# Paramètres du cône
    n_points = 50
    r_base = 0.3

    for i, (type_lot, height) in enumerate(zip(types_lot, quantites)):
        theta = np.linspace(0, 2 * np.pi, n_points)
        x_base = r_base * np.cos(theta) + i
        y_base = r_base * np.sin(theta)
        z_base = np.zeros(n_points)

    # Sommet du cône
        x_tip = np.full(n_points, i)
        y_tip = np.zeros(n_points)
        z_tip = np.full(n_points, height)

    # Surface latérale du cône
        fig.add_trace(go.Surface(
            x=np.array([x_base, x_tip]),
            y=np.array([y_base, y_tip]),
            z=np.array([z_base, z_tip]),
            showscale=False,
            colorscale=[[0, colors[i % len(colors)]], [1, colors[i % len(colors)]]],
            name=type_lot,
            opacity=0.85
        ))

    # Étiquette au sommet
        fig.add_trace(go.Scatter3d(
            x=[i],
            y=[0],
            z=[height + 500],
            text=[f"{type_lot}<br>{height} cartes"],
            mode="text",
            showlegend=False
        ))

# Mise en page immersive
    fig.update_layout(
        title="📊 Répartition des lots enregistrés par type de lot (Cônes 3D)",
        scene=dict(
            xaxis=dict(title="Type de lot", tickvals=list(range(len(types_lot))), ticktext=types_lot),
            yaxis=dict(title=""),
            zaxis=dict(title="Quantité enregistrée")
    ),
    margin=dict(l=0, r=0, b=0, t=40),
    scene_camera=dict(eye=dict(x=1.8, y=1.8, z=2.5)),
    autosize=True
)

    st.plotly_chart(fig, use_container_width=True)

# Graphique production mensuelle 
    
    import plotly.graph_objects as go
    import numpy as np
    
# Conversion des dates et extraction du mois
    lots_df["date_enregistrement"] = pd.to_datetime(lots_df["date_enregistrement"], errors="coerce")
    lots_df["Mois"] = lots_df["date_enregistrement"].dt.month_name()
    lots_df["Mois"] = lots_df["Mois"].map({'January': 'Janvier', 'February': 'Février', 'March': 'Mars', 'April': 'Avril', 'May': 'Mai', 'June': 'Juin', 'July': 'Juillet', 'August': 'Août', 'September': 'Septembre', 'October': 'Octobre', 'November': 'Novembre', 'December': 'Décembre'})

# Agrégation mensuelle
    production_mensuelle = lots_df.groupby("Mois")["quantite"].sum().reset_index()

# Ordre des mois
    mois_ordonne = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                   "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    production_mensuelle["Mois"] = pd.Categorical(production_mensuelle["Mois"], categories=mois_ordonne, ordered=True)
    production_mensuelle = production_mensuelle.sort_values("Mois")

# Coordonnées Mesh3D
    x = np.arange(len(production_mensuelle))
    y = np.zeros(len(production_mensuelle))
    z = production_mensuelle["quantite"].values
    i = list(range(len(x) - 2))
    j = [k + 1 for k in i]
    k = [k + 2 for k in i]

# Graphique Mesh3D
    fig = go.Figure(data=[
        go.Mesh3d(
           x=x, y=y, z=z,
           i=i, j=j, k=k,
           intensity=z,
           colorscale='Plasma',  # Palette personnalisée
           opacity=0.9,
           name="Production mensuelle"
        ),
        go.Scatter3d(
           x=x,
           y=y,
           z=z + 500,
           text=[f"{mois}<br>{val} cartes" for mois, val in zip(production_mensuelle["Mois"], z)],
           mode="text",
           showlegend=False
        )
    ])
    fig.update_layout(
        title="📦 Production mensuelle des cartes (Mesh3D)",
        scene=dict(
            xaxis=dict(title="Mois", tickvals=x, ticktext=production_mensuelle["Mois"]),
            yaxis=dict(title=""),
            zaxis=dict(title="Quantité produite")
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )
    st.plotly_chart(fig, use_container_width=True)



    
# Production mensuelle
    lots_df["date_enregistrement"] = pd.to_datetime(lots_df["date_enregistrement"], errors="coerce")
    controle_df["date_controle"] = pd.to_datetime(controle_df["date_controle"], errors="coerce")




    import plotly.graph_objects as go
    
# Conversion des dates
    lots_df["date_enregistrement"] = pd.to_datetime(lots_df["date_enregistrement"], errors="coerce")
    lots_df["Trimestre"] = lots_df["date_enregistrement"].dt.to_period("Q").astype(str)
    
# Agrégation par trimestre
    
    production_trimestrielle = lots_df.groupby("Trimestre")["quantite"].sum().reset_index()
    production_trimestrielle["Trimestre"] = production_trimestrielle["Trimestre"].apply(lambda x: f"Trimestre {x}")


    import plotly.graph_objects as go
    import numpy as np

# Conversion des dates
    lots_df["date_enregistrement"] = pd.to_datetime(lots_df["date_enregistrement"], errors="coerce")
    lots_df["Trimestre"] = lots_df["date_enregistrement"].dt.quarter

# Agrégation
    data = lots_df.groupby("Trimestre")["quantite"].sum().reset_index()
    data["Trimestre"] = data["Trimestre"].apply(lambda x: f"Trimestre {x}")

# Coordonnées pour Mesh3d
    x = np.arange(len(data))  # positions sur l'axe X
    y = np.zeros(len(data))   # base Y
    z = np.zeros(len(data))   # base Z
    dx = np.ones(len(data))   # largeur
    dy = np.ones(len(data))   # profondeur
    dz = data["quantite"].values  # hauteur = quantité

# Création des cubes (volumes) avec Mesh3d
    fig = go.Figure()

    for i in range(len(data)):
        fig.add_trace(go.Mesh3d(
            x=[x[i], x[i]+dx[i], x[i]+dx[i], x[i], x[i], x[i]+dx[i], x[i]+dx[i], x[i]],
            y=[y[i], y[i], y[i]+dy[i], y[i]+dy[i], y[i], y[i], y[i]+dy[i], y[i]+dy[i]],
            z=[z[i], z[i], z[i], z[i], z[i]+dz[i], z[i]+dz[i], z[i]+dz[i], z[i]+dz[i]],
            color='lightblue',
            opacity=0.7,
            name=data["Trimestre"][i],
            showscale=False
    ))

# PARTIE A ISOLEE   
    import plotly.graph_objects as go
    import numpy as np
    import pandas as pd

# Conversion des dates
    lots_df["date_enregistrement"] = pd.to_datetime(lots_df["date_enregistrement"], errors="coerce")
    lots_df["Année"] = lots_df["date_enregistrement"].dt.year
    lots_df["Trimestre"] = lots_df["date_enregistrement"].dt.quarter

# Création de toutes les combinaisons année-trimestre
    all_periods = pd.DataFrame([
        {"Année": year, "Trimestre": trimestre}
        for year in lots_df["Année"].unique()
        for trimestre in [1, 2, 3, 4]
    ])

# Agrégation réelle
    agg = lots_df.groupby(["Année", "Trimestre"])["quantite"].sum().reset_index()

# Fusion pour inclure les trimestres sans production
    data = pd.merge(all_periods, agg, on=["Année", "Trimestre"], how="left").fillna(0)
    data["Label"] = data.apply(lambda row: f"{row['Année']} - Trimestre {row['Trimestre']}", axis=1)

# Paramètres du cylindre
    n_points = 50
    r = 0.4

    fig = go.Figure()

    for i, row in data.iterrows():
        label = row["Label"]
        height = row["quantite"]
        theta = np.linspace(0, 2*np.pi, n_points)
        x_circle = r * np.cos(theta) + i
        y_circle = r * np.sin(theta)
        z_base = np.zeros(n_points)
        z_top = np.ones(n_points) * height

    # Surface latérale du cylindre
        fig.add_trace(go.Surface(
            x=np.array([x_circle, x_circle]),
            y=np.array([y_circle, y_circle]),
            z=np.array([z_base, z_top]),
            showscale=False,
            colorscale=[[0, 'lightblue'], [1, 'lightblue']],
            name=label
        ))

    # Étiquette au sommet
        fig.add_trace(go.Scatter3d(
            x=[i],
            y=[0],
            z=[height + 100],
            text=[f"{label}<br>{int(height)} cartes"],
            mode="text",
            showlegend=False
        ))


    fig.update_layout(
        title="📦 Production trimestrielle en cylindres 3D",
        scene=dict(
            xaxis=dict(title="Trimestre", tickvals=list(range(len(data))), ticktext=data["Label"].tolist()),
            yaxis=dict(title=""),
            zaxis=dict(title="Cartes produites")
    ),
    margin=dict(l=0, r=0, b=0, t=40)
)

    st.plotly_chart(fig, use_container_width=True)



    import plotly.graph_objects as go
    import numpy as np

# Données simulées
    filiales = ["Benin", "Burkina Faso", "Côte d'Ivoire", "Guinée Bissau", "Guinée Conakry", "Mali", "Niger", "Sénégal", "Togo"]
    quantites = [3644, 31256, 10226, 401, 1402, 1770, 323, 7957, 3191]

# Coordonnées X (position des filiales)
    x = np.arange(len(filiales))
    y = np.zeros(len(filiales))  # une seule ligne
    z = np.array(quantites)

# Triangulation pour Mesh3D
    i = list(range(len(x) - 2))
    j = [k + 1 for k in i]
    k = [k + 2 for k in i]

    fig = go.Figure(data=[
        go.Mesh3d(
            x=x, y=y, z=z,
            i=i, j=j, k=k,
            intensity=z,
            colorscale='Viridis',  # palette colorée
            opacity=0.9,
            flatshading=False,
            lighting=dict(ambient=0.5, diffuse=0.9, specular=0.6, roughness=0.3),
            lightposition=dict(x=100, y=200, z=300),
            name="Surface libre",
            showscale=True
    ),
    go.Scatter3d(
        x=x,
        y=y,
        z=z + 500,
        text=[f"{filiale}<br>{qte}" for filiale, qte in zip(filiales, quantites)],
        mode="text",
        showlegend=False
    )
])

    fig.update_layout(
        title="📊 Répartition des lots enregistrés par filiale (Surface libre Mesh3D colorée)",
        scene=dict(
            xaxis=dict(title="Filiale", tickvals=x, ticktext=filiales),
            yaxis=dict(title=""),
            zaxis=dict(title="Quantité enregistrée")
    ),
    margin=dict(l=0, r=0, b=0, t=40),
    scene_camera=dict(eye=dict(x=1.8, y=1.8, z=2.5)),
    autosize=True
)

    st.plotly_chart(fig, use_container_width=True)

        # KPIs sur le contrôle qualité
    st.header("Contrôle qualité")
    total_tests = controle_df["quantite_a_tester"].sum()
    nb_reussites = controle_df[controle_df["resultat"] == "Réussite"].shape[0]
    nb_echecs = controle_df[controle_df["resultat"] == "Échec"].shape[0]
    taux_reussite = (nb_reussites / (nb_reussites + nb_echecs)) * 100 if (nb_reussites + nb_echecs) > 0 else 0
    taux_echec = 100 - taux_reussite
    anomalies = controle_df[controle_df["remarque"].notna() & (controle_df["remarque"] != "")].shape[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total cartes testées", total_tests)
    col2.metric("Taux de réussite", f"{taux_reussite:.2f}%")
    col3.metric("Taux d'échec", f"{taux_echec:.2f}%")
    col4.metric("Nombre d'anomalies signalées", anomalies)

    import plotly.express as px

# Conversion des dates
    controle_df["date_controle"] = pd.to_datetime(controle_df["date_controle"], errors="coerce")

# Agrégation des données : total des tests par filiale
    df_grouped = controle_df.groupby("filiale")["quantite_a_tester"].sum().reset_index()

# Création du graphique en barres
    fig = px.bar(
        df_grouped,
        x="filiale",
        y="quantite_a_tester",
        text="quantite_a_tester",
        title="📊 Total des tests de contrôle qualité par filiale",
        labels={"filiale": "Filiale", "quantite_a_tester": "Nombre total de tests"},
        color="filiale",
        height=500
    )

# Affichage des étiquettes sur les barres
    fig.update_traces(textposition="outside")

# Mise en page
    fig.update_layout(
        xaxis_title="Filiale",
        yaxis_title="Nombre total de tests",
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )

    st.plotly_chart(fig, use_container_width=True)

# Conversion des dates
    controle_df["date_controle"] = pd.to_datetime(controle_df["date_controle"], errors="coerce")
    controle_df["Mois"] = controle_df["date_controle"].dt.to_period("M").astype(str)

# Agrégation des données
    grouped = controle_df.groupby(["filiale", "type_carte"])["quantite_a_tester"].sum().reset_index()

# Graphique interactif
    fig = px.bar(
       grouped,
       x="filiale",
       y="quantite_a_tester",
       color="type_carte",
       title="📊 Tests mensuels par carte et par filiale",
       labels={"quantite_a_tester": "Cartes testées", "type_carte": "Type de carte"},
       height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    
    import numpy as np
    import plotly.graph_objects as go

# Conversion des dates
    controle_df["date_controle"] = pd.to_datetime(controle_df["date_controle"], errors="coerce")
    controle_df["Mois"] = controle_df["date_controle"].dt.to_period("M").astype(str)

# Agrégation mensuelle
    tests_mensuels = controle_df.groupby("Mois")["quantite_a_tester"].sum().reset_index()

# Paramètres de la pyramide
    fig = go.Figure()
    base_size = 0.5
    n_points = 4  # base carrée

    for i, row in tests_mensuels.iterrows():
        label = row["Mois"]
        height = row["quantite_a_tester"]

    # Coordonnées de la base carrée
        x_base = np.array([i - base_size, i + base_size, i + base_size, i - base_size])
        y_base = np.array([-base_size, -base_size, base_size, base_size])
        z_base = np.zeros(4)

    # Coordonnées du sommet
        x_tip = i
        y_tip = 0
        z_tip = height

    # Construction des 4 faces triangulaires
        for j in range(4):
            x_face = [x_base[j], x_base[(j + 1) % 4], x_tip]
            y_face = [y_base[j], y_base[(j + 1) % 4], y_tip]
            z_face = [z_base[j], z_base[(j + 1) % 4], z_tip]

            fig.add_trace(go.Mesh3d(
                x=x_face,
                y=y_face,
                z=z_face,
                color='lightcoral',
                opacity=0.9,
                showscale=False
            ))

    # Étiquette au sommet
        fig.add_trace(go.Scatter3d(
            x=[i],
            y=[0],
            z=[height + 100],
            text=[f"{label}<br>{int(height)} tests"],
            mode="text",
            showlegend=False
        ))

# Mise en page
    fig.update_layout(
        title="📊 Nombre total de tests de contrôle qualité réalisés par mois (Pyramides 3D)",
        scene=dict(
            xaxis=dict(title="Mois", tickvals=list(range(len(tests_mensuels))), ticktext=tests_mensuels["Mois"].tolist()),
            yaxis=dict(title=""),
            zaxis=dict(title="Nombre de tests")
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        scene_camera=dict(eye=dict(x=1.8, y=1.8, z=2.5)),
        autosize=True
    )

    st.plotly_chart(fig, use_container_width=True)

    
    import plotly.express as px
    from sklearn.linear_model import LinearRegression
    import numpy as np

# Préparation des données
    controle_df["date_controle"] = pd.to_datetime(controle_df["date_controle"], errors="coerce")
    controle_df["Mois"] = controle_df["date_controle"].dt.to_period("M").astype(str)
    monthly_tests = controle_df.groupby("Mois")["quantite_a_tester"].sum().reset_index()

# Transformation pour la régression
    monthly_tests["Mois_Num"] = pd.to_datetime(monthly_tests["Mois"]).map(lambda x: x.toordinal())
    X = monthly_tests[["Mois_Num"]]
    y = monthly_tests["quantite_a_tester"]

# Modèle de régression
    model = LinearRegression()
    model.fit(X, y)

# Prévision pour les 6 prochains mois
    last_month = pd.to_datetime(monthly_tests["Mois"]).max()
    future_months = [last_month + pd.DateOffset(months=i) for i in range(1, 7)]
    future_ordinals = [m.toordinal() for m in future_months]
    future_preds = model.predict(np.array(future_ordinals).reshape(-1, 1))

# Données prévisionnelles
    future_df = pd.DataFrame({
        "Mois": [m.strftime("%Y-%m") for m in future_months],
        "quantite_a_tester": future_preds,
        "Source": "Prévision"
    })

# Données historiques
    monthly_tests["Source"] = "Historique"
    monthly_tests = monthly_tests[["Mois", "quantite_a_tester", "Source"]]

# Fusion
    combined_df = pd.concat([monthly_tests, future_df], ignore_index=True)

# Graphique
    fig = px.line(
        combined_df,
        x="Mois",
        y="quantite_a_tester",
        color="Source",
        markers=True,
        title="📈 Prévision des tests mensuels de contrôle qualité",
        labels={"quantite_a_tester": "Nombre de tests", "Mois": "Mois"}
    )

    fig.update_layout(xaxis_title="Mois", yaxis_title="Nombre de tests")
    st.plotly_chart(fig, use_container_width=True)


    st.subheader("Tests par type de carte")
    st.bar_chart(controle_df["type_carte"].value_counts())

    
    
    controle_df["date_controle"] = pd.to_datetime(controle_df["date_controle"], errors="coerce")
    controle_df["Jour_Semaine"] = controle_df["date_controle"].dt.day_name()
    controle_df["Jour_Semaine"] = controle_df["Jour_Semaine"].map({'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi', 'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'})
    tests_par_jour = controle_df.groupby("Jour_Semaine")["quantite_a_tester"].sum().reset_index()
    
    import plotly.graph_objects as go

# Ordre des jours
    jours_ordonne = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    tests_par_jour["Jour_Semaine"] = pd.Categorical(tests_par_jour["Jour_Semaine"], categories=jours_ordonne, ordered=True)
    tests_par_jour = tests_par_jour.sort_values("Jour_Semaine")

    x = list(range(len(tests_par_jour)))
    y = [0] * len(tests_par_jour)
    z = tests_par_jour["quantite_a_tester"].tolist()
    labels = tests_par_jour["Jour_Semaine"].tolist()

    fig = go.Figure(data=[
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode='lines+markers+text',
            text=[f"{jour}<br>{val} tests" for jour, val in zip(labels, z)],
            line=dict(color='royalblue', width=4),
            marker=dict(size=6)
    )
])

    fig.update_layout(
        title="📈 Total des tests journaliers par jour de la semaine (Courbe 3D)",
        scene=dict(
            xaxis=dict(title="Jour", tickvals=x, ticktext=labels),
            yaxis=dict(title=""),
            zaxis=dict(title="Nombre de tests")
    ),
    margin=dict(l=0, r=0, b=0, t=40),
    scene_camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
)

    st.plotly_chart(fig, use_container_width=True)


        # KPIs temporels
    st.header("📅 Évolution temporelle")
    lots_df["date_enregistrement"] = pd.to_datetime(lots_df["date_enregistrement"])
    controle_df["date_controle"] = pd.to_datetime(controle_df["date_controle"])

    evolution_lots = lots_df.groupby(lots_df["date_enregistrement"].dt.to_period("M")).size()
    evolution_tests = controle_df.groupby(controle_df["date_controle"].dt.to_period("W")).size()

    st.subheader("Évolution mensuelle des lots enregistrés")
    st.line_chart(evolution_lots)

    st.subheader("Évolution hebdomadaire des tests qualité")
    st.line_chart(evolution_tests)
    # pour afficher les graphiques 3D et les KPIs


elif menu == "📦 Conditionnement des cartes":
    module_conditionnement()


elif menu == "🗂 Inventaire des conditionnements":
    st.markdown("## 📦 Inventaire des conditionnements enregistrés")
    st.divider()

    conn = sqlite3.connect("erp_lots", check_same_thread=False)
    query = """
        SELECT c.id, c.date_conditionnement, l.nom_lot, c.filiale, c.type_lot, c.type_emballage, c.nombre_cartes,c.packs, c.operateur, c.remarque
        FROM conditionnement c
        JOIN lots l ON c.lot_id = l.id
    """
    df = pd.read_sql_query(query, conn)

    if df.empty:
        st.warning("Aucun conditionnement enregistré.")
    else:
        df["date_conditionnement"] = pd.to_datetime(df["date_conditionnement"])
        st.sidebar.header("🔍 Filtres")
        min_date = df["date_conditionnement"].min().date()
        max_date = df["date_conditionnement"].max().date()
        date_range = st.sidebar.date_input("Période", [min_date, max_date])
        filiales = df["filiale"].unique().tolist()
        filiale_selection = st.sidebar.multiselect("Filiale", filiales, default=filiales)
        types_lot = df["type_lot"].unique().tolist()
        type_selection = st.sidebar.multiselect("Type de lot", types_lot, default=types_lot)

        df_filtered = df[
            (df["date_conditionnement"].dt.date >= date_range[0]) &
            (df["date_conditionnement"].dt.date <= date_range[1]) &
            (df["filiale"].isin(filiale_selection)) &
            (df["type_lot"].isin(type_selection))
        ]
        
        
        st.dataframe(df_filtered, use_container_width=True)

        if st.button("🧹 Effacer le tableau des conditionnements"):
            try:
                conn = sqlite3.connect("erp_lots", check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM conditionnement")
                conn.commit()
                st.warning("🧹 Tous les conditionnements ont été supprimés.")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la suppression : {e}")

        st.subheader("📊 Résumé des conditionnements")
        total_cartes = df_filtered["nombre_cartes"].sum()
        total_paquets = df_filtered.shape[0]
        enveloppes = df_filtered[df_filtered["type_emballage"] == "Enveloppe"].shape[0]
        paquets = df_filtered[df_filtered["type_emballage"] == "Paquet"].shape[0]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total cartes emballées", total_cartes)
        col2.metric("Nombre total d'emballages", total_paquets)
        col3.metric("Enveloppes", enveloppes)
        col4.metric("Paquets", paquets)

        import plotly.graph_objects as go
        import numpy as np

# Agrégation des données
        conditionnements_par_type = df_filtered.groupby("type_emballage")["nombre_cartes"].sum().reset_index()

# Coordonnées
        x = np.arange(len(conditionnements_par_type))
        y = np.zeros(len(conditionnements_par_type))
        z = conditionnements_par_type["nombre_cartes"].values
        labels = conditionnements_par_type["type_emballage"].tolist()

# Triangulation pour Mesh3D
        i = list(range(len(x) - 2))
        j = [k + 1 for k in i]
        k = [k + 2 for k in i]

# Création du graphique
        fig = go.Figure(data=[
            go.Mesh3d(
                x=x, y=y, z=z,
                i=i, j=j, k=k,
                intensity=z,
                colorscale='Blues',
                opacity=0.9,
                flatshading=True,
                lighting=dict(ambient=0.5, diffuse=0.9, specular=0.6, roughness=0.3),
                lightposition=dict(x=100, y=200, z=300),
                name="Conditionnements",
                showscale=True
            ),
            go.Scatter3d(
                x=x,
                y=y,
                z=z + 500,
                text=[f"{label}<br>{val} cartes" for label, val in zip(labels, z)],
                mode="text",
                showlegend=False
            )
        ])

    fig.update_layout(
        title="📦 Répartition des conditionnements par type d'emballage (Mesh3D)",
        scene=dict(
            xaxis=dict(title="Type d'emballage", tickvals=x, ticktext=labels),
            yaxis=dict(title=""),
            zaxis=dict(title="Nombre de cartes")
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        scene_camera=dict(eye=dict(x=1.8, y=1.8, z=2.5)),
        autosize=True
    )

    st.plotly_chart(fig, use_container_width=True)



# Section Gestion des agences
if menu == "⚙️ Gestion des agences":
    st.markdown("## ⚙️ Gestion des agences de livraison")
    st.divider()

    # 🔍 Affichage de la liste des agences existantes
    st.subheader("📋 Liste des agences existantes")
    
    try:
        df_agences = pd.read_sql_query("SELECT * FROM agences_livraison", conn)
        st.dataframe(df_agences, use_container_width=True)
    except Exception as e:
        st.error(f"Erreur lors de la lecture des données : {e}")


    st.divider()

    # 🔧 Choix de l'action
    action = st.radio("Choisissez une action :", ["Ajouter", "Modifier", "Supprimer"])

    if action == "Ajouter":
        st.subheader("➕ Ajouter une nouvelle agence")
        nouveau_pays = st.text_input("Pays")
        nouvelle_agence = st.text_input("Nom de l'agence")
        if st.button("✅ Ajouter"):
            if nouveau_pays and nouvelle_agence:
                try:
                    cursor.execute("INSERT INTO agences_livraison (pays, agence) VALUES (?, ?)", (nouveau_pays, nouvelle_agence))
                    conn.commit()
                    st.success(f"✅ Agence ajoutée pour {nouveau_pays}")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.warning("⚠️ Ce pays existe déjà. Utilisez 'Modifier' pour le mettre à jour.")
            else:
                st.warning("Veuillez renseigner tous les champs.")

    elif action == "Modifier":
        st.subheader("✏️ Modifier une agence existante")
        cursor.execute("SELECT pays, agence FROM agences_livraison")
        agences = cursor.fetchall()
        if agences:
            agence_selectionnee = st.selectbox("Sélectionnez une agence :", agences, format_func=lambda x: f"{x[0]} - {x[1]}")
            nouveau_nom = st.text_input("Nouveau nom de l'agence", value=agence_selectionnee[1])
            if st.button("✅ Modifier"):
                cursor.execute("UPDATE agences_livraison SET agence = ? WHERE pays = ?", (nouveau_nom, agence_selectionnee[0]))
                conn.commit()
                st.success(f"✏️ Agence modifiée pour {agence_selectionnee[0]}")
                st.rerun()
        else:
            st.info("Aucune agence disponible pour modification.")

    elif action == "Supprimer":
        st.subheader("🗑️ Supprimer une agence existante")
        cursor.execute("SELECT pays, agence FROM agences_livraison")
        agences = cursor.fetchall()
        if agences:
            agence_selectionnee = st.selectbox("Sélectionnez une agence à supprimer :", agences, format_func=lambda x: f"{x[0]} - {x[1]}")
            if st.button("🗑️ Supprimer"):
                cursor.execute("DELETE FROM agences_livraison WHERE pays = ?", (agence_selectionnee[0],))
                conn.commit()
                st.warning(f"🗑️ Agence supprimée pour {agence_selectionnee[0]}")
                st.rerun()
        else:
            st.info("Aucune agence disponible pour suppression.")



elif menu == "🚚 Expédition des lots":
    module_expedition()



elif menu == "📇 Annuaire des livreurs":
    st.markdown("## 📇 Annuaire des livreurs par agence")
    st.divider()
    
    # Récupération des livreurs
    cursor.execute("SELECT id, agence, nom, prenom, contact FROM livreurs")
    livreurs = cursor.fetchall()
    df_livreurs = pd.DataFrame(livreurs, columns=["ID", "Agence", "Nom", "Prénom", "Contact"])
    st.dataframe(df_livreurs, use_container_width=True)

    # Récupération des agences existantes
    cursor.execute("SELECT DISTINCT agence FROM agences_livraison")
    agences_existantes = [row[0] for row in cursor.fetchall()]

    # Ajout d'un livreur
    st.subheader("➕ Ajouter un livreur")
    with st.form("form_ajout_livreur"):
        col1, col2 = st.columns(2)
        with col1:
            agence = st.selectbox("Agence de livraison", agences_existantes)
            nom = st.text_input("Nom")
            prenom = st.text_input("Prénom")
        with col2:
            contact = st.text_input("Contact")
        submit_ajout = st.form_submit_button("✅ Ajouter")
        if submit_ajout:
            cursor.execute("INSERT INTO livreurs (agence, nom, prenom, contact) VALUES (?, ?, ?, ?)", (agence, nom, prenom, contact))
            conn.commit()
            st.success(f"✅ Livreurs ajouté pour l'agence {agence}")
            st.rerun()

    # Modification / Suppression
    st.subheader("🛠 Modifier ou Supprimer un livreur")
    livreur_dict = {f"{l[1]} - {l[2]} {l[3]} ({l[4]})": l[0] for l in livreurs}
    selected_livreur = st.selectbox("Sélectionner un livreur", list(livreur_dict.keys()))
    livreur_id = livreur_dict[selected_livreur]

    cursor.execute("SELECT agence, nom, prenom, contact FROM livreurs WHERE id = ?", (livreur_id,))
    data = cursor.fetchone()

    with st.form("form_modif_livreur"):
        col1, col2 = st.columns(2)
        with col1:
            new_agence = st.selectbox("Agence", agences_existantes, index=agences_existantes.index(data[0]) if data[0] in agences_existantes else 0)
            new_nom = st.text_input("Nom", value=data[1])
        with col2:
            new_prenom = st.text_input("Prénom", value=data[2])
            new_contact = st.text_input("Contact", value=data[3])
        action = st.radio("Action", ["Modifier", "Supprimer"])
        submitted = st.form_submit_button("✅ Valider")

        if submitted:
            if action == "Modifier":
                cursor.execute("""
                    UPDATE livreurs SET agence=?, nom=?, prenom=?, contact=? WHERE id=?
                """, (new_agence, new_nom, new_prenom, new_contact, livreur_id))
                conn.commit()
                st.success("✏️ Livreurs modifié avec succès.")
                st.rerun()
            elif action == "Supprimer":
                cursor.execute("DELETE FROM livreurs WHERE id=?", (livreur_id,))
                conn.commit()
                st.warning("🗑️ Livreurs supprimé.")
                st.rerun()




elif menu == "📦 Visualisation des expéditions":
    st.markdown("## 📦 Indicateurs des expéditions")

    query = "SELECT statut, agence FROM expedition"
    df = pd.read_sql_query(query, conn)

    if df.empty:
        st.warning("Aucune expédition enregistrée.")
    else:
        # Indicateurs par statut
        en_attente = df[df["statut"] == "En attente"].shape[0]
        en_cours = df[df["statut"] == "En cours d'expédition"].shape[0]
        expediees = df[df["statut"] == "Expédié"].shape[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("🕒 En attente", en_attente)
        col2.metric("🚚 En cours", en_cours)
        col3.metric("✅ Expédiées", expediees)

        st.divider()
        st.subheader("🚛 Répartition par agence de livraison")

        agence_counts = df["agence"].value_counts().reset_index()
        agence_counts.columns = ["Agence", "Nombre"]

        cols = st.columns(len(agence_counts))
        for i, row in agence_counts.iterrows():
            cols[i].metric(f"🏢 {row['Agence']}", row["Nombre"])

    st.divider()
    st.markdown("## 📋 Inventaire des expéditions enregistrées")

    query = """
    SELECT e.id, l.nom_lot, e.pays, e.statut, e.bordereau, e.agence,
           lv.nom || ' ' || lv.prenom AS agent_livreur, e.date_expedition
    FROM expedition e
    JOIN lots l ON e.lot_id = l.id
    LEFT JOIN livreurs lv ON e.agent_id = lv.id
    """
    df_expeditions = pd.read_sql_query(query, conn)

    if df_expeditions.empty:
        st.warning("Aucune expédition enregistrée.")
    else:
        st.dataframe(df_expeditions, use_container_width=True)

        st.subheader("🛠️ Gestion des expéditions")
        for index, row in df_expeditions.iterrows():
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.write(f"📦 **{row['nom_lot']}** | {row['pays']} | {row['statut']} | {row['bordereau']} | {row['agence']} | {row['agent_livreur']} | {row['date_expedition']}")
            
            
            
            with col2:
                if st.button("✏️ Modifier", key=f"mod_{index}"):
                    st.session_state["mod_expedition_id"] = row["id"]
                    st.rerun()

            if "mod_expedition_id" in st.session_state and st.session_state["mod_expedition_id"] == row["id"]:
                with st.form(f"form_mod_expedition_{index}"):
                    new_statut = st.selectbox(
                        "Nouveau statut",
                        ["En attente", "En cours d'expédition", "Expédié"],
                        index=["En attente", "En cours d'expédition", "Expédié"].index(row["statut"])
                    )
                    submitted = st.form_submit_button("✅ Enregistrer les modifications")
                    if submitted:
                        cursor.execute("""
                            UPDATE expedition SET statut = ? WHERE id = ?
                            """, (new_statut, row["id"]))
                        conn.commit()
                        st.success("✅ Statut modifié avec succès.")
                        st.session_state["mod_expedition_id"] = None
                        st.rerun()




            with col3:
                if st.button("🗑️ Supprimer", key=f"del_{index}"):
                    cursor.execute("DELETE FROM expedition WHERE id = ?", (row["id"],))
                    conn.commit()
                    st.warning("🗑️ Expédition supprimée.")
                    st.rerun()

elif menu == "🔐 Gestion des comptes utilisateurs":
    gestion_comptes_utilisateurs()

# Message de bienvenue
st.sidebar.success(f"{st.session_state['utilisateur']} est connecté")
st.markdown("<div style='text-align: left;'>", unsafe_allow_html=True)
if st.sidebar.button("🔓 Se déconnecter"):
    del st.session_state["utilisateur"]
    del st.session_state["role"]
    if "doit_changer_mdp" in st.session_state:
        del st.session_state["doit_changer_mdp"]
    st.rerun()






    






