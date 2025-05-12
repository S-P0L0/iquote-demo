import streamlit as st
import pandas as pd
import requests, io, time

"""
App – iQuote BTP  (option B : l’agent IA reste dans n8n)
--------------------------------------------------------
▶ Ce Streamlit sert juste de vitrine pour la démo :
   – Il collecte la description, le nom client et les photos.
   – Il envoie le tout en multipart/form‑data vers ton webhook n8n PUBLIC.
   – n8n renvoie un fichier Excel (binaire) contenant le devis.
   – L’app affiche le devis et propose le téléchargement.

À préparer :
1. Ouvre ton n8n en public via Cloudflare Tunnel ou ngrok et remplace WEBHOOK_URL ci‑dessous.
2. Assure‑toi que le dernier nœud n8n renvoie « Content‑Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet »
   et le contenu du devis en binaire.
3. requirements.txt minimal :
      streamlit==1.33.0
      pandas
      requests
      openpyxl
"""

# 🔗 Indique ici l’URL HTTPS de ton webhook public (PAS localhost)
WEBHOOK_URL = "https://74ac-2a01-cb1c-699-2d00-9d3d-6d15-dce6-8ea.ngrok-free.app"

st.set_page_config(page_title="iQuote BTP", page_icon="🧮", layout="centered")

# ------------------------------  UI  ---------------------------------------
st.title("📑 iQuote BTP — Générateur de devis IA")

col1, col2 = st.columns([2,1])
with col1:
    description = st.text_area(
        "Description des travaux",
        placeholder="Ex : Démolir cloison, refaire peinture 2 chambres…",
        height=200,
    )
with col2:
    client = st.text_input("Nom du client", placeholder="Entreprise Martin")

photos = st.file_uploader(
    "📷 Photos chantier (optionnel)",
    accept_multiple_files=True,
    type=["jpg", "jpeg", "png"],
)

if st.button("🚀 Générer le devis"):
    if not description or not client:
        st.warning("Merci de saisir la description ET le nom du client.")
        st.stop()

    # --- construction du payload multipart ---------------------------------
    data = {
        "demande_client": description,
        "client_id": client,
    }
    files = {}
    for idx, photo in enumerate(photos):
        files[f"photos{idx}"] = (photo.name, photo.getvalue(), photo.type)

    # --- appel du webhook ---------------------------------------------------
    with st.spinner("Envoi au moteur IA…"):
        try:
            start = time.time()
            resp = requests.post(WEBHOOK_URL, data=data, files=files, timeout=120)
            duration = round(time.time() - start, 1)
        except requests.exceptions.RequestException as e:
            st.error(f"Erreur réseau : {e}")
            st.stop()

    if resp.status_code != 200:
        st.error(f"Erreur API : {resp.status_code} — {resp.text[:200]}")
        st.stop()

    devis_bytes = resp.content

    try:
        devis_df = pd.read_excel(io.BytesIO(devis_bytes))
    except Exception as e:
        st.error("Le fichier reçu n’est pas un Excel valide. Vérifie le nœud de sortie n8n.")
        st.exception(e)
        st.stop()

    # --- affichage ----------------------------------------------------------
    st.success(f"✅ Devis généré en {duration} s !")
    st.dataframe(devis_df, use_container_width=True)

    st.download_button(
        label="📥 Télécharger l’Excel",
        data=devis_bytes,
        file_name=f"devis_{client.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# -----------------------------  Footer  ------------------------------------
st.markdown("<hr style='margin-top:3rem;margin-bottom:1rem'>", unsafe_allow_html=True)
st.caption("© 2025 iQuote BTP • Prototype Streamlit (agent IA via n8n)")
