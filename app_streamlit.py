import os
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

# Charge les variables d'environnement
load_dotenv()

st.set_page_config(
    page_title="Gestionnaire de Commandes IA",
    page_icon="📦",
    layout="wide",
)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "mon_secret_123")
HEADERS = {"X-API-Key": API_KEY}

st.title("📦 Gestionnaire de Commandes par IA")
st.write("Analyse automatique d'e-mails via FastAPI & Ollama")

col_gauche, col_droite = st.columns([1, 1])

# --- COLONNE GAUCHE : ANALYSE MAIL ---
with col_gauche:
    st.subheader("✉️ Analyser un nouvel e-mail")

    email_defaut = (
        "Bonjour, je souhaite commander 2 tables en chêne à 150 EUR l'unité "
        "et 1 chaise ergonomique à 80 EUR. Merci de livrer en urgent pour le client Dupont."
    )

    texte_email = st.text_area("Contenu de l'e-mail :", value=email_defaut, height=180)

    if st.button("🚀 Lancer l'analyse", use_container_width=True):
        if not texte_email.strip():
            st.warning("Veuillez saisir le contenu d'un e-mail.")
        else:
            with st.spinner("Envoi de l'e-mail à l'API..."):
                try:
                    res = requests.post(
                        f"{API_URL}/commandes/analyser",
                        json={"contenu_email": texte_email},
                        headers=HEADERS,
                        timeout=10,
                    )
                    if res.status_code == 202:
                        st.success("E-mail reçu ! L'analyse IA s'exécute en arrière-plan.")
                        st.info("Attends 3 à 5 secondes puis clique sur **Rafraîchir la liste**.")
                    else:
                        st.error(f"Erreur API ({res.status_code}) : {res.text}")
                except Exception as e:
                    st.error(f"Impossible de contacter l'API : {e}")

# --- COLONNE DROITE : LISTES (COMMANDES VS SERVICE CLIENT) ---
with col_droite:
    st.subheader("📋 Suivi des e-mails en base")

    if st.button("🔄 Rafraîchir la liste", use_container_width=True):
        st.rerun()

    try:
        res = requests.get(f"{API_URL}/commandes", headers=HEADERS, timeout=5)
        if res.status_code == 200:
            commandes = res.json()
            if commandes:
                df_all = pd.DataFrame(commandes)

                # Séparation selon le statut "transfere_sav"
                df_commandes = df_all[df_all["statut"] != "transfere_sav"]
                df_sav = df_all[df_all["statut"] == "transfere_sav"]

                # 1. Tableau Commandes Valides
                st.markdown("#### 📦 Commandes logistiques")
                if not df_commandes.empty:
                    st.dataframe(
                        df_commandes[["id", "client", "montant_total", "urgente", "statut"]],
                        use_container_width=True,
                    )
                else:
                    st.info("Aucune commande logistique enregistrée.")

                st.divider()

                # 2. Tableau Mails Transférés au Service Client
                st.markdown("#### 🎧 Mails transférés au Service Client (Hors-sujet / Support)")
                if not df_sav.empty:
                    st.dataframe(
                        df_sav[["id", "client", "statut"]],
                        use_container_width=True,
                    )
                else:
                    st.caption("Aucun mail transféré au service client pour le moment.")

            else:
                st.info("Aucune donnée enregistrée pour le moment.")
        else:
            st.error(f"Erreur API ({res.status_code})")
    except Exception as e:
        st.error(f"Impossible de contacter l'API : {e}")

st.divider()

# --- SECTION BASSE : DÉTAIL ET GESTION D'UNE COMMANDE ---
st.subheader("🔍 Détail et gestion d'une demande")
col_id, col_btn = st.columns([1, 2])

with col_id:
    commande_id = st.number_input("ID à consulter :", min_value=1, step=1, value=1)

with col_btn:
    st.write("")  # Espace alignement
    st.write("") 
    chercher = st.button("Chercher la demande")

if chercher or "dernier_id" in st.session_state:
    target_id = commande_id if chercher else st.session_state.get("dernier_id", commande_id)
    try:
        res = requests.get(f"{API_URL}/commandes/{target_id}", headers=HEADERS, timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.session_state["dernier_id"] = target_id
            
            st.markdown(f"### Demande #{data['id']} — Client : **{data['client']}**")
            
            priorite = "🚨 **URGENTE**" if data.get('urgente') else "🟢 Normale"
            st.write(f"**Montant :** {data.get('montant_total', 0)} € | **Priorité :** {priorite} | **Statut actuel :** `{data.get('statut')}`")

            # Formulaire isolé avec st.form pour éviter les erreurs de soumission
            with st.form(key=f"form_statut_{data['id']}"):
                statuts_possibles = ["en_attente", "en_preparation", "expediee", "annulee", "transfere_sav"]
                index_actuel = statuts_possibles.index(data['statut']) if data['statut'] in statuts_possibles else 0

                nouveau_statut = st.selectbox(
                    "Changer le statut / Réorienter :",
                    statuts_possibles,
                    index=index_actuel
                )
                
                submit_btn = st.form_submit_button("💾 Enregistrer le nouveau statut")

                if submit_btn:
                    res_patch = requests.patch(
                        f"{API_URL}/commandes/{data['id']}/statut",
                        json={"statut": nouveau_statut},
                        headers=HEADERS,
                    )
                    if res_patch.status_code == 200:
                        st.success("Statut mis à jour avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de la mise à jour.")

            if data.get('articles'):
                st.write("**Articles à préparer :**")
                df_articles = pd.DataFrame(data['articles'])
                st.dataframe(df_articles, use_container_width=True)

        elif res.status_code == 404:
            st.warning(f"La demande #{target_id} n'existe pas.")
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")