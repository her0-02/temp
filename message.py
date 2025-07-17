import ast
import time
import traceback
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import streamlit as st
import re
from utils.api import query_rag, get_rag
from utils.grid_utils import create_and_display_grid
from components.horizontalbar import render_horizontal_filters
from utils.chroma_filter_builder import ChromaFilterBuilder

def is_non_empty(context):  # type: ignore
    """Helper function to check if the given context is non-empty."""
    if context is None:
        return False
    if isinstance(context, str):
        cleaned = context.strip().lower()
        return cleaned not in ["", "null", "none"]
    if isinstance(context, (dict, list)):
        return bool(context)  # type: ignore
    return True

def build_conversation(messages):  # type: ignore
    """Build the conversation list for the API call from session messages."""
    conversation = []
    for msg in messages:  # type: ignore
        if msg["role"] == "assistant":
            content = msg["content"].get("text", "")  # type: ignore
            if is_non_empty(msg["content"].get("context")):  # type: ignore
                content += f"\n ###Données retrouvées sur la base de vos paramètres d'entrées\n {msg['content']['context']}"  # type: ignore
            conversation.append({"role": msg["role"], "content": content})  # type: ignore
        elif msg["role"] == "user":
            conversation.append({"role": msg["role"], "content": msg["content"]})  # type: ignore
    return conversation  # type: ignore

def extract_context_data_and_llm(context_unified):  # type: ignore
    """
    Extract display context and LLM context from the unified context structure.
    """
    if not context_unified:
        return None, None

    context_data = {}
    context_llm = {}

    for key, value in context_unified.items():  # type: ignore
        if isinstance(value, dict) and "data" in value and "usage" in value:
            if value["usage"].get("display", False):  # type: ignore
                context_data[key] = value["data"]
            if value["usage"].get("llm", False):  # type: ignore
                context_llm[key] = value["data"]

    return context_data, context_llm  # type: ignore

def render_message_input():
    """
    Interface Streamlit pour poser une question spécifique, avec sélection des paramètres avancés.
    """
    # Initialisation de la session
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("messages_llm", [])
    st.session_state.setdefault("interface_locked", False)

    # -- Sélection du nombre de résultats (sliders)
    render_horizontal_filters ()

    col1, col2, col3, col4,col5 = st.columns([1, 1, 1, 1,1])  # 5 colonnes égales
 
    with col3:
       
        n_results_reranker = st.slider(
            "📊 Nombre de résultats à afficher",
            min_value=1,
            max_value=100,
            value=10,
            step=1,
            help="Nombre de documents à réévaluer pour la réponse finale."
        )

    # Enregistre dans la session
    st.session_state["n_results_embedder"] = 200
    st.session_state["n_results_reranker"] = n_results_reranker

    # if st.session_state.get("interface_locked"):
    #     st.markdown(
    #         """
    #         <script>
    #             const disableInputs = () => {
    #                 const chatInputs = document.querySelectorAll('.stChatInput textarea, .stChatInput button');
    #                 if (chatInputs.length > 0) {
    #                     chatInputs.forEach(el => {
    #                         el.disabled = true;
    #                         if (el.tagName === 'TEXTAREA') {
    #                             el.style.backgroundColor = '#F4F4F4'; // gris clair
    #                             el.style.color = '#00A9E0'; // bleu foncé
    #                             el.placeholder = '⏳ Traitement en cours...';
    #                             el.style.border = '2px solid #FF6A13'; // orange Safran
    #                         }
    #                         if (el.tagName === 'BUTTON') {
    #                             el.style.backgroundColor = '#FF6A13';
    #                             el.style.color = 'white';
    #                             el.style.border = 'none';
    #                         }
    #                     });
    #                     return true;
    #                 }
    #                 return false;
    #             };
    #             if (!disableInputs()) {
    #                 const observer = new MutationObserver(() => {
    #                     if (disableInputs()) {
    #                         observer.disconnect();
    #                     }
    #                 });
    #                 observer.observe(document, { childList: true, subtree: true });
    #             }
    #         </script>
    #         """,
    #         unsafe_allow_html=True,
    #     )
        


        
    # Ajout de style pour les badges
    st.markdown("""
        <style>
        .sidebar-badge {
            background-color: #e0e0e0;
            color: #333;
            padding: 4px 10px;
            border-radius: 12px;
            display: inline-block;
            margin: 2px 4px 2px 0;
            font-size: 0.85em;
        }
        </style>
    """, unsafe_allow_html=True)

    # Disposition en colonnes : filtres à gauche, champ à droite
    col1, col2 = st.columns([1, 5])  # Ajuste les proportions selon ton besoin
    with col1:
        filters_displayed = False

        st.markdown("""
            <style>
            .sidebar-badge {
                background-color: #007BFF;  /* Bleu */
                color: white;
                padding: 4px 10px;
                border-radius: 12px;
                display: inline-block;
                margin: 0px 0px 2px 0;
                font-size: 0.85em;
            }
            </style>
        """, unsafe_allow_html=True)
        if st.session_state.get("active_filters"):
            for k in st.session_state.active_filters:
                st.markdown(f"<span class='sidebar-badge'>{k}</span>", unsafe_allow_html=True)
            filters_displayed = True

        if st.session_state.get("contains_terms"):
            st.markdown("**Texte contient**")
            for t in st.session_state.contains_terms:
                st.markdown(f"<span class='sidebar-badge'>{t}</span>", unsafe_allow_html=True)
            filters_displayed = True

        if st.session_state.get("not_contains_terms"):
            st.markdown("**Texte exclut**")
            for t in st.session_state.not_contains_terms:
                st.markdown(f"<span class='sidebar-badge'>{t}</span>", unsafe_allow_html=True)
            filters_displayed = True

        if not filters_displayed:
            st.info("Aucun filtre actif.", icon="ℹ️")

    with col2:
       # Injecter du CSS personnalisé
        st.markdown("""
            <style>
            div[data-testid="stChatInput"] {
                background-color: #ffff !important;
                border-radius: 8px;
                padding: 10px;
            }
            div[data-testid="stChatInput"] textarea {
                background-color: #0000 !important;
                color: black !important;
                
            }
            </style>
        """, unsafe_allow_html=True)

        # Champ de saisie avec fond personnalisé
        prompt = st.chat_input(
            "Entrez un problème… Ex : ressuage, coup, pièce sale",
            disabled=st.session_state.get("interface_locked", False)
        )


    if prompt:
        if st.session_state.get("interface_locked"):
            st.warning("Veuillez patienter le temps du traitement de la requête en cours.")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages_llm.append({"role": "user", "content": prompt})
        st.session_state.needs_processing = True
        st.session_state.query_to_process = prompt
        st.session_state.interface_locked = True
        st.session_state.query_type_to_process = "Specific Question"
        st.rerun()  # type: ignore

    if st.session_state.get("needs_processing", False):
        try:
            st.session_state.needs_processing = False
            prompt = st.session_state.query_to_process
            query_type = "Specific Question"
            st.session_state.processing_query = True

            with st.chat_message("assistant"):
                thinking_placeholder = st.empty()
                thinking_message = "Recherche dans la base de connaissances…"
                thinking_placeholder.markdown(thinking_message)

                conversation = build_conversation(st.session_state["messages_llm"])  # type: ignore

                # Utilisation des valeurs choisies par l'utilisateur
                n_embedder = st.session_state.get("n_results_embedder", 50)
                n_reranker = st.session_state.get("n_results_reranker", 10)

                try: 
                    
                        
                   
                    if prompt in ["*","all documents","tout"] :
                        with st.spinner("Tous les documents..."):
                            response_data = get_rag(
                                conversation=conversation,  # type: ignore
                                where_filter=st.session_state.get("metadata_filters"),
                                where_document_filter=st.session_state.get(
                                    "where_document"
                                ),
                            )
                    elif "DA-" in prompt.strip():
                        match = re.search(r"(DA-\d+)", prompt)
                        if match:
                            code_da = match.group(1)

                            # Connexion à la base Chroma
                            client = chromadb.PersistentClient(path="/config/workspace/Traitementda/data/chroma.sqlite3")
                            collection = client.get_collection(name="chroma.sqlite3")
                            # Récupération du document unique
                            results = collection.get(
                                where={"Code DA": code_da + "_1"}
                            )
                            
                            if results and results['metadatas']:
                                
                                
                                row = results['metadatas'][0]
                                contexte = results['documents'][0]
                                new_conversation = st.session_state.messages_llm + [
                                    {"role": "user", "content": contexte }
                                ]
                                filter_PN = ChromaFilterBuilder.eq(field="PN", value=row.get("PN", ""))
                                if "active_filters" not in st.session_state:
                                    st.session_state.active_filters = {}
                                else :
                                    st.session_state.active_filters["PN"] = filter_PN
                                
                                if  st.session_state.metadata_filters == None :
                                    st.session_state.metadata_filters = {}
                                    st.session_state.metadata_filters = filter_PN
                                
                                else:
                                    
                                    # Convertit les filtres existants en liste de conditions
                                    existing = [
                                        {key: value}
                                        for key, value in st.session_state.metadata_filters.items()
                                    ]
                                    st.session_state.metadata_filters = {"$and": existing}

                                    # Ajoute le nouveau filtre s'il n'est pas déjà présent
                                    if filter_PN not in st.session_state.metadata_filters["$and"]:
                                        st.session_state.metadata_filters["$and"].append(filter_PN)

                                with st.spinner(f"Recherche pour la {code_da}..."):
                                    response_data = query_rag(
                                        conversation=build_conversation(new_conversation),
                                        n_results_embedder=n_embedder,
                                        n_results_reranker=n_reranker,
                                        where_filter=st.session_state.get("metadata_filters"),
                                        where_document_filter=st.session_state.get("where_document"),
                                    )
                        else:
                            st.warning(f"Aucune donnée trouvée pour {code_da}")
                            response_data = None
   
                    else :
                        with st.spinner("Recherche...") :
                            response_data = query_rag(
                                conversation=conversation,  # type: ignore
                                n_results_embedder=n_embedder,
                                n_results_reranker=n_reranker,
                                where_filter=st.session_state.get("metadata_filters"),
                                where_document_filter=st.session_state.get("where_document"),
                            )

                    if not response_data:
                        response_data = {"error": "Empty response from API."}

                    if "error" in response_data:
                        assistant_response = f"Erreur : {response_data['error']}"
                        context_data = None
                        context_llm = None
                    else:
                        context_unified = response_data.get("context_unified", {})
                        context_data, context_llm = extract_context_data_and_llm(context_unified)
                        assistant_response = response_data.get("answer", "Aucune réponse reçue.")

                    #Header unique
                    # source_indicator = (
                        # '<div style="padding: 10px; border-radius: 5px; background-color: #e6f3ff; margin-bottom: 10px;">'
                        # "<strong>📚 Réponse enrichie depuis la base :</strong> Cette réponse s'appuie sur les données de la base et la similarité avec votre question."
                        # "</div>"
                    # )
                    # formatted_response = f"{source_indicator}\n\n{assistant_response}"
                    # thinking_placeholder.markdown(
                        # formatted_response, unsafe_allow_html=True
                    # )

                    # Affichage du grid si contexte
                    grid_key = None
                    if is_non_empty(context_data):
                        st.markdown("### Données retrouvées selon vos paramètres d'entrées")
                        st.session_state.setdefault("grid_counter", 0)
                        st.session_state.grid_counter += 1
                        grid_key = f"input_{st.session_state.grid_counter}"
                        try:
                            create_and_display_grid(
                                context_data=context_data,  # type: ignore
                                key_suffix=grid_key,
                            )
                        except Exception as e:
                            st.error(f"Erreur lors de l'affichage du tableau : {str(e)}")
                            st.exception(e)
                            traceback.print_exc()

                    # Stockage du message assistant
                    response_content = {  # type: ignore
                        "text": assistant_response,
                        "context": context_data if is_non_empty(context_data) else None,
                        "grid_key": grid_key,
                        "query_type": query_type,
                    }
                    response_content_llm = {  # type: ignore
                        "text": assistant_response,
                        "context": context_llm if is_non_empty(context_llm) else None,
                        "grid_key": grid_key,
                        "query_type": query_type,
                    }

                    st.session_state.messages.append(
                        {"role": "assistant", "content": response_content}
                    )
                    st.session_state.messages_llm.append(
                        {"role": "assistant", "content": response_content_llm}
                    )

                except Exception as api_err:
                    error_message = (
                        f"Une erreur est survenue lors du traitement : {str(api_err)}"
                    )
                    st.error(error_message)
                    st.exception(api_err)
                    traceback.print_exc()
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": {"text": error_message, "context": None},
                        }
                    )
                    st.session_state.messages_llm.append(
                        {
                            "role": "assistant",
                            "content": {"text": error_message, "context": None},
                        }
                    )

        except Exception as ex:
            st.error(f"Erreur inattendue : {str(ex)}")
            st.exception(ex)
            traceback.print_exc()
        finally:
            time.sleep(0.5)
            st.session_state.interface_locked = False
            st.session_state.processing_query = False
            st.session_state.pop("query_to_process", None)
            st.session_state.pop("query_type_to_process", None)
            st.rerun()  # type: ignore
