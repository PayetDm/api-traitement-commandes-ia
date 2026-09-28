import os
import requests
import streamlit as st
from style import apply_custom_style

# Configuration de la page Streamlit
st.set_page_config(
    page_title="PyTechData — Gestion des Commandes IA",
    page_icon="📦",
    layout="wide",
)

apply_custom_style()

# Récupération des variables d'environnement
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    st.error("API_KEY n'est pas configurée. L'interface ne peut pas démarrer.")
    st.stop()

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}

st.title("📦 Dashboard de Traitement IA")
st.caption("Supervision en temps réel des commandes extraites par LLM")

# ==========================================
# 1. BANDEAU DE MÉTRIQUES (KPIs)
# ==========================================
try:
    res_stats = requests.get(f"{API_URL}/stats", headers=HEADERS, timeout=4)
    if res_stats.status_code == 200:
        kpi = res_stats.json()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(
            label="Total Demandes", 
            value=kpi.get("total_demandes", 0)
        )
        col2.metric(
            label="Chiffre d'Affaires", 
            value=f"{kpi.get('chiffre_affaires_cumule', 0.0):,.2f} €"
        )
        col3.metric(
            label="Commandes Urgentes 🚨", 
            value=kpi.get("commandes_urgentes", 0)
        )
        col4.metric(
            label="À Vérifier (Erreurs IA) ⚠️", 
            value=kpi.get("dossiers_a_verifier", 0)
        )
    else:
        st.warning("⚠️ Impossible de charger les statistiques depuis l'API.")
except Exception as err:
    st.error(f"Erreur de connexion à l'API pour les métriques : {err}")

st.divider()

# ==========================================
# 2. SECTIONS & ONGLETS DE DOSSIERS
# ==========================================
st.subheader("📋 Traitement des dossiers")

col_left, col_right = st.columns([8, 2])
with col_right:
    if st.button("🔄 Rafraîchir les données", type= "secondary", use_container_width=True):
        st.rerun()

tab_commandes, tab_sav, tab_test = st.tabs([
    "🛒 Commandes Clients", 
    "🎧 Service Client / SAV", 
    "🧪 Zone de Test (Simulation)"
])

try:
    response = requests.get(f"{API_URL}/commandes", headers=HEADERS, timeout=5)
    
    if response.status_code == 200:
        toutes_commandes = response.json()
        
        # Séparation des dossiers entre commandes valides et SAV
        commandes_valides = [c for c in toutes_commandes if c.get("statut") != "transfere_sav"]
        dossiers_sav = [c for c in toutes_commandes if c.get("statut") == "transfere_sav"]

        # ---------------------------------------------------------
        # ONGLET 1 : COMMANDES CLIENTS
        # ---------------------------------------------------------
        with tab_commandes:
            if not commandes_valides:
                st.info("Aucune commande valide enregistrée pour le moment.")
            else:
                for cmd in reversed(commandes_valides):
                    statut = cmd.get("statut", "inconnu")
                    urgente = cmd.get("urgente", False)
                    badge_urgence = "🚨 URGENT" if urgente else "🟢 Normal"
                    
                    with st.expander(f"Commande #{cmd['id']} - {cmd['client']} ({cmd['montant_total']} €) | {badge_urgence} | Statut: {statut}"):
                        c1, c2 = st.columns([2, 1])
                        
                        with c1:
                            st.write(f"**Client :** {cmd['client']}")
                            st.write(f"**Montant Total :** {cmd['montant_total']} €")
                            st.write(f"**Urgent :** {'Oui' if urgente else 'Non'}")
                            st.write(f"**Date de création :** {cmd.get('date_creation', 'N/A')}")

                            # --- AJOUT DE L'AFFICHAGE DU MAIL ---
                            if cmd.get("contenu_email"):
                                with st.expander("📄 Afficher l'e-mail d'origine"):
                                    st.text(cmd["contenu_email"])
                            # ------------------------------------
                            
                            st.write("**Articles détectés :**")
                            articles = cmd.get("articles", [])
                            if articles:
                                for art in articles:
                                    st.markdown(f"- **{art.get('nom', 'Produit')}** x{art.get('quantite', 1)} ({art.get('prix_unitaire', 0.0)} €/u)")
                            else:
                                st.caption("Aucun article détaillé.")

                        with c2:
                            st.write("**Changer le statut :**")
                            statuts_disponibles = ["en_attente", "traitee", "expediee", "transfere_sav", "a_verifier_manuellement"]
                            
                            idx_actuel = statuts_disponibles.index(statut) if statut in statuts_disponibles else 0
                            nouveau_statut = st.selectbox(
                                "Nouveau statut",
                                options=statuts_disponibles,
                                index=idx_actuel,
                                key=f"select_{cmd['id']}"
                            )
                            
                            if st.button("Mettre à jour", key=f"btn_{cmd['id']}"):
                                patch_res = requests.patch(
                                    f"{API_URL}/commandes/{cmd['id']}/statut",
                                    json={"statut": nouveau_statut},
                                    headers=HEADERS,
                                    timeout=5
                                )
                                if patch_res.status_code == 200:
                                    st.success("Statut mis à jour !")
                                    st.rerun()
                                else:
                                    st.error("Échec de la mise à jour.")

        # ---------------------------------------------------------
        # ONGLET 2 : SERVICE CLIENT / SAV
        # ---------------------------------------------------------
        with tab_sav:
            if not dossiers_sav:
                st.info("Aucun dossier classé en Service Client / SAV.")
            else:
                for sav in reversed(dossiers_sav):
                    with st.expander(f"Dossier SAV #{sav['id']} - {sav['client']} | Statut: Transfert SAV"):
                        st.warning("⚠️ Cet e-mail a été classé comme Hors-Sujet ou demande SAV par l'IA.")
                        st.write(f"**Client :** {sav['client']}")
                        st.write(f"**Date :** {sav.get('date_creation', 'N/A')}")
                        
                        if st.button("Reclasser en commande client", key=f"btn_reclasser_{sav['id']}"):
                            patch_res = requests.patch(
                                f"{API_URL}/commandes/{sav['id']}/statut",
                                json={"statut": "en_attente"},
                                headers=HEADERS,
                                timeout=5
                            )
                            if patch_res.status_code == 200:
                                st.success("Dossier reclassé en commande !")
                                st.rerun()

        # ---------------------------------------------------------
        # ONGLET 3 : ZONE DE TEST & SIMULATION
        # ---------------------------------------------------------
        with tab_test:
            st.markdown("### ✉️ Tester l'analyse d'un e-mail")
            st.caption("Injecte un texte de mail personnalisé pour observer le classement automatique par le LLM.")
            
            email_test_default = (
                "Bonjour,\n\n"
                "Je souhaite passer commande pour mon entreprise :\n"
                "- 3x Écran PC 27 pouces (250€/u)\n"
                "- 1x Clavier mécanique (120€/u)\n\n"
                "Merci de livrer d'urgence avant vendredi.\n"
                "Cordialement,\nJean Dupont"
            )
            
            texte_email = st.text_area("Contenu de l'e-mail à tester", value=email_test_default, height=180)
            
            if st.button("🚀 Analyser l'e-mail", type="primary"):
                with st.spinner("Envoi à l'API pour traitement arrière-plan..."):
                    test_res = requests.post(
                        f"{API_URL}/commandes/analyser",
                        json={"contenu_email": texte_email},
                        headers=HEADERS,
                        timeout=120
                    )
                    if test_res.status_code == 202:
                        st.success("E-mail analysé et enregistré avec succès !")
                        st.rerun()
                    else:
                        st.error(f"Erreur lors de l'analyse (Code {test_res.status_code}).")

    else:
        st.error(f"Erreur lors de la récupération des commandes (Code {response.status_code}).")

except Exception as e:
    st.error(f"Impossible de joindre le serveur FastAPI : {e}")