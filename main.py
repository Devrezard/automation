import json
import streamlit as st
import ollama
from ollama import Client
import httpx

# type :
url = st.text_input(
    "Enter Ollama server URL:", "", placeholder="http://localhost:11434"
)

model_list = []
if url != "":
    client = Client(host=url)
    ollama_list = httpx.get(f"{url}/api/tags").json()
    # get all name of all models
    model_list = [model["name"] for model in ollama_list["models"]]
else:
    client = Client()

st.selectbox("Select the model:", model_list)

uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
if uploaded_file is not None and client is not None:
    # Read the file content
    file_content = uploaded_file.read()
    # transform file xlsx to json
    import pandas as pd
    from io import BytesIO

    # Load the Excel file into a DataFrame
    df = pd.read_excel(BytesIO(file_content))
    # Convert the DataFrame to JSON
    json_data = df.to_json(orient="records")

    # mesage for display json
    st.markdown("**JSON FILE OUTPUT :**")

    # Display the JSON data
    st.json(json_data, expanded=False)

    # Convert JSON string to a format suitable for the prompt
    json_string = json.dumps(json.loads(json_data), indent=2, ensure_ascii=False)
    # prompt system:
    prompt = f"""
    Tu es un assistant chargé de produire une synthèse hebdomadaire professionnelle à partir de comptes-rendus individuels structurés en JSON.

    Voici le fichier en entrée (au format tableau JSON) :

    {json_string}

    ---

    Ta mission est de **générer un rapport hebdomadaire clair et structuré**, composé de 4 sections. Tu dois corriger, fusionner et reformuler les éléments en français professionnel.

    ### 1. Objectifs de la semaine
    - Regroupe les objectifs communs par thématique (SIGAP, API, monitoring, configuration, etc.).
    - Formule 4 à 6 bullet points synthétiques, clairs, sans doublons.

    ### 2. Travaux réalisés
    - Liste les actions réalisées avec un style homogène (ex. : infinitif ou participe passé).
    - Garde un format concis et sans répétition.

    ### 3. Prochaines étapes
    - Regroupe les prochaines étapes à venir, de façon synthétique, sans mention de nom.

    ### 4. Remarques et suggestions
    - Liste les remontées (techniques, logistiques, etc.) formulées dans les rapports.
    - Reformule pour plus de clarté si besoin.

    **Contraintes générales** :
    - Supprime les champs vides ou null.
    - Ne mentionne aucun nom ni email.
    - Utilise un style clair, professionnel et non redondant.
    - La sortie doit être en Markdown, bien structurée.

    Rends uniquement le contenu formaté du rapport, pas d’explication ou de commentaire autour.
    """
    # response
    response = client.chat(
        model=st.selectbox("Select the model:", ollama.list()),
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": json_string},
        ],
        temperature=0.5,
        max_tokens=4096,
    )
    # response in st markdown
    st.markdown("**Synthèse hebdomadaire générée :**")
    st.markdown(response.content, unsafe_allow_html=True)
else:
    st.info("Please upload an Excel file to proceed.")
