import streamlit as st
import os
import base64

from components.conversation import clear_conversation, render_conversation
from components.message_input import render_message_input
from utils.config import load_config


from datetime import datetime

def get_data_last_update(data_file_path):
    if os.path.exists(data_file_path):
        timestamp = os.path.getmtime(data_file_path)
        return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y à %H:%M")
    else:
        return "Inconnue"
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def main():
    st.set_page_config(
        page_title="ResearchDA",
        page_icon="🔎",
        layout="wide",
    )

    load_config()
    img_base64_1 = get_base64_of_bin_file('utils/fond_app.png')
    img_base64_2 = get_base64_of_bin_file('utils/fond_ciel.png')
    img_base64_logo = get_base64_of_bin_file('utils/logo.png')
    st.markdown(f"""
    <style>
    /* Fond général blanc avec bordure arrondie */
    .stApp {{
        background:url("data:image/png;base64,{img_base64_2}") center/cover no-repeat;
        border-radius: 26px !important;
        color: #1C1C1C;
        padding-bottom: 58px !important; /* Hauteur du footer + marge */
        font-family: "Segoe UI", "Inter", sans-serif;
        padding: 24px 0 24px 0 !important;
        min-height: 100vh;
        box-shadow: 0 2px 28px 0 rgba(0,32,91,0.08);
    }}
    /* La barre de recherche */
    .search-bar-wide {{
        background:url("data:image/png;base64,{img_base64_1}") center/cover no-repeat;
        padding: 34px 0 22px 0;
        border-radius: 16px;
        margin-bottom: 28px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.08);
        text-align: center;
        position: sticky;
        top: 0;
        z-index: 100;
        width: 100%;
    }}
    .search-bar-wide h1 {{
        color: #0F4E97;
        font-size: 2.1em;
        font-weight: 800;
        margin: 0 0 8px 0;
        letter-spacing: 1.1px;
    }}
    .large-search-container {{
        display: flex;
        justify-content: center;
        margin-top: 16px;
        margin-bottom: 0;
    }}
    .large-search-box {{
        width: 84vw;
        max-width: 1100px;
        display: flex;
        align-items: center;
        gap: 0.5em;
        background: rgba(255,255,255,0.95);
        border-radius: 13px;
        box-shadow: 0 2px 8px #00205B15;
        padding: 0.8em 1.2em;
    }}
    .large-search-box input[type="text"] {{
        font-size: 1.15em;
        width: 100%;
        border: none;
        outline: none;
        background: transparent;
        color: #1C1C1C;
        padding: 0.7em 0.6em;
    }}
    .objectives {{
        background:url("data:image/png;base64,{img_base64_2}") center/cover no-repeat;
        border-radius: 12px;
        padding: 18px 28px;
        margin-bottom: 20px;
        color: #00205B;
        box-shadow: 0 1px 5px rgba(0,0,0,0.07);
    }}
    .stButton>button {{
        background: linear-gradient(90deg,#1976D2, #00A9E0 90%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6em 1.4em;
        font-weight: bold;
        font-size: 1em;
    }}
    .stButton>button:hover {{
        background: #1976D2;
    }}
   
    /* Overlay traitement */
    .overlay {{
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0,0,0,0.18);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .overlay-content {{
        background: #fff;
        border-radius: 14px;
        padding: 40px 60px;
        box-shadow: 0 8px 32px rgba(0,32,91,0.21);
        text-align: center;
    }}
     .custom-logo-container {{
        position: fixed;
        top: 75px;      
        right: 35px;     /
        z-index: 3000;
        background: white;  
        border-radius: 10px; 
        padding: 4px;  
        box-shadow: 0 2px 8px rgba(0,32,91,0.09); 
        display: flex;  
        align-items: center;
    }}

    .custom-logo {{
        height: 54px;
        width: auto;
        border-radius: 10px; 
        /* Pas de box-shadow ici si déjà présent sur le container */
    }}
    </style>
    """, unsafe_allow_html=True)

    for key, default in {
        "messages": [],
        "messages_llm": [],
        "filters": [],
        "interface_locked": False,
        "processing_query": False,
        "needs_processing": False,
        "query_to_process": "",
        "current_query_type": "Specific Question"
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default
    st.markdown(f"""
        <div class="custom-logo-container">
            <img src="data:image/png;base64,{img_base64_logo}" class="custom-logo" />
        </div>
        """, unsafe_allow_html=True)
    user = st.session_state.get('user', {})

    st.markdown(f"""
        <style>
        .user-info-container {{
            position: fixed;
            top: 75px;
            left: 35px;
            z-index: 0;
            background: white;  
            border-radius: 10px; 
            padding: 4px;  
            box-shadow: 0 2px 8px rgba(0,32,91,0.09); 
           
            align-items: center;
            }}
        .user-info-container strong {{
            color: #0F4E97;
            
        }}
        </style>

        <div class="user-info-container">
            <div><strong>Utilisateur :</strong> {user.get('name') or user.get('email')} </div>
        </div>
    """, unsafe_allow_html=True)

    # --- LARGE SEARCH BAR ALWAYS ON TOP ---
    # st.markdown("""
    # <div class="search-bar-wide">
        # <h1>Recherche intelligente d'anomalies (DA)</h1>
    # """, unsafe_allow_html=True)
    render_message_input()
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- CONVERSATION / RESULTATS ---
    with st.container():
        if st.session_state.get("messages", False):
            st.markdown("#### 💬 Résultats")
        render_conversation()

    # --- OBJECTIFS EN BAS ---
    st.markdown("""
        <style>
        div[data-testid="stExpander"] {
            background: #f7f7fa !important;
            border-radius: 16px !important;
            border: 1.5px solid #e0e2e8;
            margin-bottom: 12px;
            box-shadow: 0 2px 8px rgba(0,32,91,0.07);
            /* Tu peux ajouter du padding si tu veux plus d'espace autour du contenu */
        }
        </style>
        """, unsafe_allow_html=True)
    with st.expander("🎯 Objectifs de l’outil", expanded=False):
        st.markdown("""
        <ul>
            <li>🔍 <strong>Recherche rapide</strong> de cas similaires dans les <strong>déclarations d'anomalies (DA)</strong>.</li>
            <li>🧠 <strong>Inspiration via cas déjà résolus</strong> pour accélérer le diagnostic.</li>
            <li>🗂️ <strong>Exploration historique</strong> via filtres (Programme, PN, date...).</li>
            <li>✏️ <strong>Recherche libre</strong> sur toute la base depuis 2020.</li>
            <li>⏳ <strong>Réduction des délais</strong> d’analyse grâce à l’IA.</li>
        </ul>
        """,unsafe_allow_html=True)

    # --- BOUTON FLOTTANT REINITIALISER LA CONVERSATION ---
    st.markdown("""
    <style>
    /* Sélectionne le dernier bouton Streamlit*/
    div[data-testid="stButton"] > button {
        position: fixed;
        bottom: 20px;
        right: 30px;
        z-index: 9999;
        background: linear-gradient(90deg,##0D206D,#958CCA 80%);
        color: #fff !important;
        border: none;
        border-radius: 11px;
        font-weight: bold;
        font-size: 0.7em;
        padding: 0.8em 2.1em;
        box-shadow: 0 2px 12px rgba(0,32,91,0.13);
        transition: box-shadow 0.2s, background 0.15s;
        cursor: pointer;
    }
    div[data-testid="stButton"] > button:hover {
        background: #958CCA !important;
        color: #fff !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("🧹 Réinitialiser la conversation", key="clear_btn", disabled=st.session_state.interface_locked):
        clear_conversation()
    # # Overlay de “traitement en cours”
    # if st.session_state.interface_locked:
    #     st.markdown("""
    #         <div class="overlay">
    #             <div class="overlay-content">
    #                 <h3>⏳ Traitement en cours</h3>
    #                 <p>Merci de patienter pendant le traitement de votre requête...</p>
    #             </div>
    #         </div>
    #     """, unsafe_allow_html=True)

    # Rafraîchissement si déverrouillage
    if st.session_state.get("_previous_lock_state", False) and not st.session_state.interface_locked:
        st.session_state._previous_lock_state = False
        st.rerun()
    st.session_state._previous_lock_state = st.session_state.interface_locked
    
    # --- FOOTER ---
    data_file_path = "../../data/source/d_keys/DA - ADAM Vincent programmee.csv"  # Remplace par le nom réel du fichier
    last_update = get_data_last_update(data_file_path)
    mailto = "mailto:yenam.dossou@safrangroup.com?subject=Problème%20avec%20ResearchDA"
    
    st.markdown(f"""
    <div style="
        width: 100vw;
        max-width: 100%;
        margin-left: -2.5vw;
        background: #f7f7fa;
        border-top: 1.5px solid #e0e2e8;
        padding: 12px 0 8px 0;
        text-align: center;
        font-size: 1.02em;
        color: #7D8590;
        position: fixed;
        left: 0;
        bottom: 0;
        z-index: 999;
    ">
        <span>Dernières mises à jour le <b>{last_update}</b></span>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <a href="{mailto}" style="text-decoration: none; color: #1976d2;" title="Signaler un problème">
            <span style="vertical-align: middle;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="#1976d2" xmlns="http://www.w3.org/2000/svg" style="display: inline-block; vertical-align: middle;">
                    <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 2v.01L12 13 4 6.01V6h16zM4 18V8.24l7.76 6.99c.38.34.97.34 1.35 0L20 8.24V18H4z"/>
                </svg>
                <b>Support</b>
            </span>
        </a>
    </div>
    """, unsafe_allow_html=True)
if __name__ == "__main__":
    main()
    
    


