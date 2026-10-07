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
        col1.metric(label="Total Demandes", value=kpi.get("total_demandes", 0))
        col2.metric(
            label="Chiffre d'Affaires",
            value=f"{kpi.get('chiffre_affaires_cumule', 0.0):,.2f} €",
        )
        col3.metric(
            label="Commandes Urgentes 🚨",
            value=kpi.get("commandes_urgentes", 0),
        )
        col4.metric(
            label="🎧 En Service Client",
            value=kpi.get("en_service_client", 0),
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
    if st.button("🔄 Rafraîchir les données", type="secondary", use_container_width=True):
        st.rerun()

tab_commandes, tab_service_client, tab_sav, tab_test = st.tabs([
    "🛒 Commandes",
    "🎧 Service Client",
    "🛠️ SAV",
    "🧪 Zone de Test",
])


# ==========================================
# Helper : affichage d'une commande
# ==========================================
def _changer_statut(commande_id: int, nouveau_statut: str):
    """Change le statut d'une commande."""
    try:
        res = requests.patch(
            f"{API_URL}/commandes/{commande_id}/statut",
            json={"statut": nouveau_statut},
            headers=HEADERS,
            timeout=5,
        )
        if res.status_code == 200:
            st.success(f"✅ Statut : {nouveau_statut}")
            st.rerun()
        else:
            st.error(f"Échec (code {res.status_code})")
    except Exception as e:
        st.error(f"Erreur : {e}")


def _rediriger(commande_id: int, nouvelle_categorie: str):
    """Redirige une commande vers une autre catégorie."""
    try:
        res = requests.post(
            f"{API_URL}/commandes/{commande_id}/rediriger",
            json={"nouvelle_categorie": nouvelle_categorie},
            headers=HEADERS,
            timeout=5,
        )
        if res.status_code == 200:
            st.success(f"✅ Redirigé vers {nouvelle_categorie}")
            st.rerun()
        else:
            st.error(f"Échec de la redirection (code {res.status_code})")
    except Exception as e:
        st.error(f"Erreur : {e}")


def afficher_commande(cmd, statuts_disponibles, cle_prefixe=""):
    """Affiche un dossier de commande avec ses actions."""
    statut = cmd.get("statut", "inconnu")
    urgente = cmd.get("urgente", False)

    # Badge de statut avec couleur
    statuts_visuels = {
        "en_attente": ("🟠", "À préparer", "#F59E0B"),
        "expediee": ("🚚", "En livraison", "#3B82F6"),
        "traitee": ("✅", "Terminée", "#10B981"),
        "transfere_sav": ("🛠️", "SAV", "#EF4444"),
        "transfere_service_client": ("🎧", "Service Client", "#8B5CF6"),
        "erreur_technique": ("⚠️", "Erreur", "#6B7280"),
    }
    emoji_statut, label_statut, couleur = statuts_visuels.get(
        statut, ("❓", "Inconnu", "#6B7280")
    )

    # Badge urgence
    if urgente:
        badge_urgence = "🚨"
        texte_urgence = "URGENT"
    else:
        badge_urgence = "🟢"
        texte_urgence = "Normal"

    titre = (
        f"{emoji_statut} Commande #{cmd['id']} — **{cmd['client']}** "
        f"| {cmd['montant_total']:.2f} € | {badge_urgence} {texte_urgence}"
    )

    with st.expander(titre):
        # Info-bulle de statut
        st.markdown(
            f"""
            <div style="
                display: inline-block;
                padding: 4px 12px;
                background-color: {couleur}20;
                color: {couleur};
                border-radius: 12px;
                font-weight: 600;
                font-size: 0.85rem;
                margin-bottom: 12px;
            ">
                {emoji_statut} {label_statut}
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns([2, 1])

        with c1:
            st.write(f"**Client :** {cmd['client']}")
            st.write(f"**Montant Total :** {cmd['montant_total']:.2f} €")
            st.write(f"**Urgent :** {'Oui' if urgente else 'Non'}")
            st.write(f"**Date :** {cmd.get('date_creation', 'N/A')}")

            if cmd.get("contenu_email"):
                with st.expander("📄 Afficher l'e-mail d'origine"):
                    st.text(cmd["contenu_email"])

            st.write("**Articles détectés :**")
            articles = cmd.get("articles", [])
            if articles:
                for art in articles:
                    st.markdown(
                        f"- **{art.get('nom', 'Produit')}** "
                        f"x{art.get('quantite', 1)} "
                        f"({art.get('prix_unitaire', 0.0)} €/u)"
                    )
            else:
                st.caption("Aucun article détaillé.")

        with c2:
            st.write("**🔄 Rediriger vers :**")

            col_btn1, col_btn2, col_btn3 = st.columns(3)

            with col_btn1:
                if statut != "en_attente":
                    if st.button(
                        "🛒 Cmd",
                        key=f"{cle_prefixe}redir_cmd_{cmd['id']}",
                        use_container_width=True,
                        help="Rediriger vers Commande",
                    ):
                        _rediriger(cmd["id"], "commande")
                else:
                    st.caption("🛒 Cmd")

            with col_btn2:
                if statut != "transfere_service_client":
                    if st.button(
                        "🎧 SC",
                        key=f"{cle_prefixe}redir_sc_{cmd['id']}",
                        use_container_width=True,
                        help="Rediriger vers Service Client",
                    ):
                        _rediriger(cmd["id"], "service_client")
                else:
                    st.caption("🎧 SC")

            with col_btn3:
                if statut != "transfere_sav":
                    if st.button(
                        "🛠️ SAV",
                        key=f"{cle_prefixe}redir_sav_{cmd['id']}",
                        use_container_width=True,
                        help="Rediriger vers SAV",
                    ):
                        _rediriger(cmd["id"], "sav")
                else:
                    st.caption("🛠️ SAV")

            # Avancement logistique (uniquement pour les commandes)
            if statut in ("en_attente", "expediee"):
                st.divider()
                st.write("**🚚 Avancer le statut :**")

                col_av1, col_av2 = st.columns(2)

                with col_av1:
                    if statut == "en_attente":
                        if st.button(
                            "📦 Expédiée",
                            key=f"{cle_prefixe}av_exp_{cmd['id']}",
                            use_container_width=True,
                            type="primary",
                            help="Marquer comme expédiée (partie du dépôt)",
                        ):
                            _changer_statut(cmd["id"], "expediee")

                with col_av2:
                    if statut == "expediee":
                        if st.button(
                            "✅ Terminée",
                            key=f"{cle_prefixe}av_term_{cmd['id']}",
                            use_container_width=True,
                            type="primary",
                            help="Marquer comme terminée (client a signé)",
                        ):
                            _changer_statut(cmd["id"], "traitee")


# ==========================================
# Chargement des données
# ==========================================
try:
    response = requests.get(f"{API_URL}/commandes", headers=HEADERS, timeout=5)

    if response.status_code == 200:
        toutes_commandes = response.json()

                # Répartition par statut
        commandes_a_traiter = [
            c for c in toutes_commandes
            if c.get("statut") == "en_attente"
        ]
        commandes_expediees = [
            c for c in toutes_commandes
            if c.get("statut") == "expediee"
        ]
        commandes_terminees = [
            c for c in toutes_commandes
            if c.get("statut") == "traitee"
        ]
        dossiers_service_client = [
            c for c in toutes_commandes
            if c.get("statut") == "transfere_service_client"
        ]
        dossiers_sav = [
            c for c in toutes_commandes
            if c.get("statut") == "transfere_sav"
        ]

        # Statuts disponibles pour les changements manuels
        statuts_disponibles = [
            "en_attente",
            "traitee",
            "expediee",
            "transfere_sav",
            "transfere_service_client",
            "erreur_technique",
        ]


                # ---------------------------------------------------------
        # ONGLET 1 : COMMANDES (3 sous-sections)
        # ---------------------------------------------------------
        with tab_commandes:
            total_commandes = (
                len(commandes_a_traiter)
                + len(commandes_expediees)
                + len(commandes_terminees)
            )
            if total_commandes == 0:
                st.info("📭 Aucune commande enregistrée pour le moment.")
            else:
                # --- Sous-section 1 : À traiter ---
                nb_attente = len(commandes_a_traiter)
                st.markdown(
                    f"""
                    <h3 style="display: flex; align-items: center; gap: 10px;">
                        🟠 En cours
                        <span style="
                            background-color: #F59E0B;
                            color: white;
                            padding: 2px 10px;
                            border-radius: 12px;
                            font-size: 0.75em;
                            font-weight: 700;
                        ">{nb_attente}</span>
                    </h3>
                    """,
                    unsafe_allow_html=True,
                )
                if not commandes_a_traiter:
                    st.success("✨ Aucune commande à préparer. Bon boulot !")
                else:
                    for cmd in reversed(commandes_a_traiter):
                        afficher_commande(
                            cmd, statuts_disponibles, cle_prefixe="encours_"
                        )

                st.divider()

                # --- Sous-section 2 : Expédiées ---
                nb_exp = len(commandes_expediees)
                st.markdown(
                    f"""
                    <h3 style="display: flex; align-items: center; gap: 10px;">
                        🚚 Expédiées
                        <span style="
                            background-color: #3B82F6;
                            color: white;
                            padding: 2px 10px;
                            border-radius: 12px;
                            font-size: 0.75em;
                            font-weight: 700;
                        ">{nb_exp}</span>
                    </h3>
                    """,
                    unsafe_allow_html=True,
                )
                if not commandes_expediees:
                    st.caption("📭 Aucune commande en cours de livraison.")
                else:
                    for cmd in reversed(commandes_expediees):
                        afficher_commande(
                            cmd, statuts_disponibles, cle_prefixe="exp_"
                        )

                st.divider()

                # --- Sous-section 3 : Terminées ---
                nb_term = len(commandes_terminees)
                st.markdown(
                    f"""
                    <h3 style="display: flex; align-items: center; gap: 10px;">
                        ✅ Terminées
                        <span style="
                            background-color: #10B981;
                            color: white;
                            padding: 2px 10px;
                            border-radius: 12px;
                            font-size: 0.75em;
                            font-weight: 700;
                        ">{nb_term}</span>
                    </h3>
                    """,
                    unsafe_allow_html=True,
                )
                if not commandes_terminees:
                    st.caption("📭 Aucune commande terminée pour le moment.")
                else:
                    for cmd in reversed(commandes_terminees):
                        afficher_commande(
                            cmd, statuts_disponibles, cle_prefixe="term_"
                        )


        # ---------------------------------------------------------
        # ONGLET 2 : SERVICE CLIENT
        # ---------------------------------------------------------
        with tab_service_client:
            if not dossiers_service_client:
                st.info("Aucun dossier en Service Client.")
            else:
                st.caption(
                    f"📬 {len(dossiers_service_client)} dossier(s) relationnel(s) "
                    "à traiter par le Service Client."
                )
                for dossier in reversed(dossiers_service_client):
                    afficher_commande(
                        dossier, statuts_disponibles, cle_prefixe="sc_"
                    )


        # ---------------------------------------------------------
        # ONGLET 3 : SAV (technique)
        # ---------------------------------------------------------
        with tab_sav:
            if not dossiers_sav:
                st.info("Aucun dossier SAV.")
            else:
                st.caption(
                    f"🛠️ {len(dossiers_sav)} dossier(s) technique(s) "
                    "à traiter par le SAV."
                )
                for dossier in reversed(dossiers_sav):
                    afficher_commande(
                        dossier, statuts_disponibles, cle_prefixe="sav_"
                    )


        # ---------------------------------------------------------
        # ONGLET 5 : ZONE DE TEST
        # ---------------------------------------------------------
        with tab_test:
            st.markdown("### ✉️ Tester l'analyse d'un e-mail")
            st.caption(
                "Injecte un texte de mail personnalisé pour observer le classement "
                "automatique par le LLM."
            )

            email_test_default = (
                "Bonjour,\n\n"
                "Je souhaite passer commande pour mon entreprise :\n"
                "- 3x Écran PC 27 pouces (250€/u)\n"
                "- 1x Clavier mécanique (120€/u)\n\n"
                "Merci de livrer d'urgence avant vendredi.\n"
                "Cordialement,\nJean Dupont"
            )

            texte_email = st.text_area(
                "Contenu de l'e-mail à tester",
                value=email_test_default,
                height=180,
            )

            if st.button("🚀 Analyser l'e-mail", type="primary"):
                with st.spinner("Envoi à l'API pour traitement arrière-plan..."):
                    test_res = requests.post(
                        f"{API_URL}/commandes/analyser",
                        json={"contenu_email": texte_email},
                        headers=HEADERS,
                        timeout=120,
                    )
                    if test_res.status_code == 202:
                        st.success("E-mail analysé et enregistré avec succès !")
                        st.rerun()
                    else:
                        st.error(
                            f"Erreur lors de l'analyse "
                            f"(Code {test_res.status_code})."
                        )

    else:
        st.error(
            f"Erreur lors de la récupération des commandes "
            f"(Code {response.status_code})."
        )

except Exception as e:
    st.error(f"Impossible de joindre le serveur FastAPI : {e}")