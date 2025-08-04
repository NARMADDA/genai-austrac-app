import streamlit as st
from langchain.schema import HumanMessage
from langchain_openai import AzureChatOpenAI
import weaviate

@st.cache_resource
def get_weaviate_client():
    return weaviate.Client(
        url=st.secrets["WEAVIATE_URL"],
        auth_client_secret=weaviate.AuthApiKey(st.secrets["WEAVIATE_API_KEY"])
    )

client = get_weaviate_client()

def query_weaviate(query_text):
    try:
        response = client.query.get("AUSTRACRule", ["title", "section", "link"]) \
            .with_near_text({"concepts": [query_text]}) \
            .with_limit(5) \
            .do()

        docs = response.get("data", {}).get("Get", {}).get("AUSTRACRule", []) or []

        if not docs:
            response = client.query.get("AUSTRACRule", ["title", "section", "link"]) \
                .with_bm25(query=query_text) \
                .with_limit(3) \
                .do()
            docs = response.get("data", {}).get("Get", {}).get("AUSTRACRule", []) or []

        return docs
    except Exception as e:
        st.error(f"❌ Weaviate query error: {str(e)}")
        return []

def get_answer_with_context(query):
    docs = query_weaviate(query)

    if not docs:
        return (
            "Sorry, I couldn’t find anything relevant in the AUSTRAC rules for your query.",
            "No relevant documents found."
        )

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
            openai_api_key=st.secrets["AZURE_OPENAI_API_KEY"],
            azure_endpoint=st.secrets["AZURE_OPENAI_ENDPOINT"],
            api_version=st.secrets["AZURE_OPENAI_VERSION"],
            deployment_name=st.secrets["AZURE_OPENAI_DEPLOYMENT"],
            temperature=0
            # Don't set model explicitly unless you're sure it matches the deployment
        )

        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip(), context

    except Exception as e:
        st.error(f"❌ GPT-4 response error: {str(e)}")
        return (
            "Sorry, an internal error occurred while generating the answer.",
            context,
        )
