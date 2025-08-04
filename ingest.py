import json
import streamlit as st
import weaviate

# Initialize Weaviate client using Streamlit secrets
client = weaviate.Client(
    url=st.secrets["WEAVIATE_URL"],
    auth_client_secret=weaviate.AuthApiKey(st.secrets["WEAVIATE_API_KEY"])
)

# Define class name
class_name = "AUSTRACRule"

# 🔁 Delete class if it already exists (to remove vectorizer)
if client.schema.exists(class_name):
    print(f"⚠️ Deleting existing class '{class_name}' to reset schema without vectorizer.")
    client.schema.delete_class(class_name)

# ✅ Recreate class with vectorizer: none
schema = {
    "class": class_name,
    "description": "AUSTRAC rule entries",
    "vectorizer": "none",  # Important for Azure OpenAI
    "properties": [
        {"name": "title", "dataType": ["text"]},
        {"name": "section", "dataType": ["text"]},
        {"name": "link", "dataType": ["text"]},
    ]
}
client.schema.create_class(schema)
print(f"✅ Class '{class_name}' created successfully without vectorizer.")

# Insert static sample
client.data_object.create(
    data_object={
        "title": "About AUSTRAC",
        "section": "AUSTRAC (Australian Transaction Reports and Analysis Centre) is Australia’s anti-money laundering and counter-terrorism financing regulator and financial intelligence unit. AUSTRAC collects, analyzes, and shares financial intelligence to detect and prevent financial crime and protect the Australian community.",
        "link": "https://www.austrac.gov.au/about-us/austrac-overview"
    },
    class_name=class_name
)

# Insert from output.json
try:
    with open("output.json", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        client.data_object.create(
            data_object={
                "title": item["title"],
                "section": item["section"],
                "link": item["link"]
            },
            class_name=class_name
        )
    print("✅ Data from output.json ingested successfully.")

except FileNotFoundError:
    print("⚠️ File 'output.json' not found. Skipping file ingestion.")

