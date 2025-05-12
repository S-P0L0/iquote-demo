import streamlit as st
import pandas as pd
import requests, io, time

# ─────────────────────────────────────────────────────────────────────────────
#  App – iQuote BTP  (option B : l’agent IA reste dans n8n)
# ─────────────────────────────────────────────────────────────────────────────
#  Ce Streamlit sert de vitrine pour la démo :
#    1. Collecte description, nom client, photos.
#    2. Envoie tout en multipart/form‑data vers le webhook n8n PUBLIC.
#    3. n8n renvoie un fichier Excel binaire.
#    4. L’app affiche le devis + bouton de téléchargement.
#
#  prerequisites (requirements.txt) :
#       streamlit==1.33.0
#       pandas
#       requests
#       openpyxl
# ─────────────────────────────────────────────────────────────────────────────

# 👉 IMPORTANT : `set_page_config` DOIT être le tout premier appel Streamlit.
st.set_page_config(page_title="iQuote BTP", page_icon=":abacus:", layout="centered")

# 🔗 URL HTTPS de ton webhook public (ngrok / Cloudflare Tunnel).  PAS localhost.
WEBHOOK_URL = "https://74ac-2a01-cb1c-699-2d00-9d3d-6d15-dce6-8ea.ngrok-free.app"

# ------------------------------  UI  ----------------------------------------
st.title("📑 iQuote BTP — Générateur de devis IA")

col1, col2 = st.columns([2, 1])
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
    files = {
        f"photos{idx}": (photo.name, photo.getvalue(), photo.type)
        for idx, photo in enumerate(photos)
    }

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
