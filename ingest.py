import json
import os
from dotenv import load_dotenv
import weaviate

load_dotenv()

client = weaviate.Client(
    url=os.getenv("WEAVIATE_URL"),
    auth_client_secret=weaviate.AuthApiKey(os.getenv("WEAVIATE_API_KEY")),
    additional_headers={
        "X-OpenAI-Api-Key": os.getenv("AZURE_OPENAI_API_KEY")
    }
)

# Define class name
class_name = "AUSTRACRule"

# Check if class exists
existing_classes = [cls["class"] for cls in client.schema.get()["classes"]]
if class_name not in existing_classes:
    schema = {
        "class": class_name,
        "description": "AUSTRAC rule entries",
        "vectorizer": "text2vec-openai",  # important for WCS!
        "properties": [
            {
                "name": "title",
                "dataType": ["text"],
            },
            {
                "name": "section",
                "dataType": ["text"],
            },
            {
                "name": "link",
                "dataType": ["text"],
            },
        ]
    }
    client.schema.create_class(schema)

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
with open("output.json") as f:
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

print("✅ Data ingested successfully.")
