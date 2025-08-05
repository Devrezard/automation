import json
import streamlit as st
from jinja2 import Environment, FileSystemLoader, Template
import datetime
import locale
import weasyprint
import httpx
from jinja_markdown import MarkdownExtension

locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")  # Pour format français

# ollama client configuration
# type :
url = st.text_input(
    "Enter Ollama server URL:", "", placeholder="http://localhost:11434"
)

model_list = []
if url != "":
    ollama_list = httpx.get(f"{url}/api/tags").json()
    # get all name of all models
    model_list = [model["name"] for model in ollama_list["models"]]

model_selected = st.selectbox("Select the model:", model_list)


# Sélection de la plage de dates
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Date de début", datetime.date.today())
with col2:
    end_date = st.date_input("Date de fin", datetime.date.today())


def format_date_range(start, end):
    return f"{start.strftime('%d %B')} au {end.strftime('%d %B %Y')}"


uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
report = {}
objectif = []
travaux = []
next_steps = []
remarks = []
synthese = ""
if uploaded_file is not None and url != "":
    # Read the file content
    file_content = uploaded_file.read()
    # transform file xlsx to json
    import pandas as pd
    from io import BytesIO

    # Load the Excel file into a DataFrame
    df = pd.read_excel(BytesIO(file_content))
    # Convert the DataFrame to JSON
    json_data = df.to_json(orient="records")
    for data in json.loads(json_data):
        objectif.append(data.get("Objectifs de la semaine", ""))
        travaux.append(data.get("Travaux réalisés", ""))
        next_steps.append(data.get("Prochaines étapes", ""))
        remarks.append(data.get("Remarques et suggestions", ""))

    # Add the JSON data to the report
    report["Objectifs de la semaine"] = objectif
    report["Travaux réalisés"] = travaux
    report["Prochaines étapes"] = next_steps
    report["Remarques et suggestions"] = remarks

    st.json(report, expanded=False)
    # list of objectifs
    parse_objectifs = [" " + task for task in report["Objectifs de la semaine"] if task]
    # list of travaux
    parse_travaux = [" " + task for task in report["Travaux réalisés"] if task]
    # list of next steps
    parse_next_steps = [" " + task for task in report["Prochaines étapes"] if task]
    # list of remarks
    parse_remarks = [" " + task for task in report["Remarques et suggestions"] if task]

    # prompt for synthèse
    prompt = f"""
    Tu es un assistant chargé de produire une synthèse hebdomadaire professionnelle à partir de comptes-rendus individuels structurés en JSON.

    Voici le fichier en entrée (au format tableau JSON) :
    {parse_objectifs}
    {parse_travaux}
    {parse_next_steps}
    {parse_remarks}
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
    # Appel Ollama via httpx (chat, no streaming)
    ollama_url = f"{url}/api/chat"
    payload = {
        "model": str(model_selected),
        "messages": [
            {
                "role": "system",
                "content": "Tu es un assistant chargé de produire une synthèse hebdomadaire professionnelle à partir de comptes-rendus individuels structurés en JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }
    response = httpx.post(ollama_url, json=payload, timeout=500.0)
    if response.status_code == 200:
        result = response.json()
        # La réponse est généralement dans result["message"]["content"]
        synthese = result.get("message", {}).get("content", "")

    else:
        st.error(f"Erreur Ollama : {response.text}")

    # Convert JSON string to a format suitable for the prompt
    json_string = json.dumps(report, indent=2, ensure_ascii=False)
    # parse data to template.html
    # Charger le template avec Jinja Environment et activer MarkdownExtension
    jinja_env = Environment(loader=FileSystemLoader("."))  # dossier courant
    jinja_env.add_extension(MarkdownExtension)
    template = jinja_env.get_template("template.html")
    rendered_html = template.render(
        date=format_date_range(start_date, end_date),
        synthese=synthese,
    )
    # render pdf
    pdf = weasyprint.HTML(string=rendered_html).write_pdf()
    st.components.v1.html(rendered_html, height=800, scrolling=True)
    st.download_button("Download PDF", pdf, "rapport.pdf")
else:
    st.info("Please upload an Excel file to proceed.")
