import os
import weaviate
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from langchain_openai import AzureChatOpenAI

# Load environment variables from .env
load_dotenv()

# Azure OpenAI settings
AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT", "gpt-4o-sandbox-deployment")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_VERSION = os.getenv("AZURE_OPENAI_VERSION", "2024-12-01-preview")

# Initialize Weaviate client (for v3.x)
client = weaviate.Client("http://localhost:8080")

def query_weaviate(query_text):
    try:
        response = client.query.get("AUSTRACRule", ["title", "section", "link"]) \
            .with_near_text({"concepts": [query_text]}) \
            .with_limit(5) \
            .do()

        docs = response.get("data", {}).get("Get", {}).get("AUSTRACRule", []) or []

        if not docs:
            print("⚠️ No semantic matches found for:", query_text)
            # Optional BM25 fallback (if enabled in your setup)
            response = client.query.get("AUSTRACRule", ["title", "section", "link"]) \
                .with_bm25(query=query_text) \
                .with_limit(3) \
                .do()
            docs = response.get("data", {}).get("Get", {}).get("AUSTRACRule", []) or []

        return docs

    except Exception as e:
        print("❌ Weaviate query error:", str(e))
        return []

def get_answer_with_context(query):
    docs = query_weaviate(query)

    if not docs:
        return (
            "Sorry, I couldn’t find anything relevant in the AUSTRAC rules for your query.",
            "No relevant documents found."
        )

    # Compose context from matched documents
    context = "\n\n".join(
        [f"[{doc['title']}] {doc['section']}\n(Source: {doc['link']})" for doc in docs]
    )

    prompt = f"""You are an AUSTRAC compliance assistant. Answer the following user query using only the context provided below. Always cite the section title and include source links when possible.

Context:
{context}

User Query: {query}

Answer:"""

    try:
        llm = AzureChatOpenAI(
            openai_api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_VERSION,
            deployment_name=AZURE_DEPLOYMENT,
            temperature=0,
            model="gpt-4o",  # or "gpt-35-turbo"
        )

        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)

        return response.content.strip(), context

    except Exception as e:
        print("❌ GPT-4 response error:", str(e))
        return (
            "Sorry, an internal error occurred while generating the answer.",
            context,
        )
