import json
import requests


def analyser_texte(texte_utilisateur: str) -> dict:
    """Envoie un texte à l'IA et récupère une analyse au format Dictionnaire Python."""
    url = "http://localhost:11434/api/generate"

    # 1. On donne les instructions précises sur la structure attendue
    prompt = f"""
    Analyse le texte suivant et réponds STRICTEMENT au format JSON avec ces clés :
    - "sentiment": (string: "positif", "neutre" ou "negatif")
    - "resume": (string: résumé en une phrase)
    - "mots_cles": (array: liste de 3 mots-clés)

    Texte à analyser : "{texte_utilisateur}"
    """

    payload = {
        "model": "qwen2.5-coder:3b",
        "prompt": prompt,
        "format": "json",  # <-- LA MAGIE EST ICI : force le mode JSON d'Ollama
        "stream": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=60)

        if response.status_code == 200:
            # Réponse brute du serveur sous forme de texte JSON
            texte_json_brut = response.json().get("response", "{}")

            # 2. Conversion du texte JSON en VRAI Dictionnaire Python !
            donnees_structurees = json.loads(texte_json_brut)
            return donnees_structurees
        else:
            print(f"⚠️ Erreur API : {response.status_code}")
            return {}

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion : {e}")
        return {}


# --- TEST D'ANALYSIS ---
if __name__ == "__main__":
    texte_test = "J'ai installé Python et Ollama aujourd'hui. Au début j'avais peur de ne rien comprendre, mais finalement c'est super gratifiant de voir le script fonctionner !"

    print("⏳ Analyse du texte par l'IA en cours...\n")
    resultat = analyser_texte(texte_test)

    # On vérifie qu'on a bien reçu un dictionnaire exploitable
    if resultat:
        print("✅ Données extraites avec succès (Type Python : dict) :\n")
        print(f"• Sentiment : {resultat.get('sentiment')}")
        print(f"• Résumé    : {resultat.get('resume')}")
        print(f"• Mots-clés : {', '.join(resultat.get('mots_cles', []))}")