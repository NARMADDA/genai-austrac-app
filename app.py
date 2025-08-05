import streamlit as st
from rag_chain import get_answer_with_context
st.set_page_config(page_title="AUSTRAC Compliance Assistant")

st.title("AUSTRAC GenAI Compliance Assistant")

query = st.chat_input("Ask a question related to AUSTRAC guidelines")  # Better UX than st.text_input

if query:
    with st.spinner("Thinking..."):
        answer, context = get_answer_with_context(query)
        st.subheader("Answer")
        st.write(answer)
        with st.expander("Sources Used"):
            st.markdown(context)
