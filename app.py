import streamlit as st

from src.rag.answer import answer_question, format_context
from src.rag.retrieve import retrieve, retrieval_confidence

st.set_page_config(page_title="UniPath LK", page_icon="🎓", layout="wide")

st.title("UniPath LK")
st.caption("UGC Sri Lanka admission assistant — grounded in the 2025/26 Student Handbook")

st.warning(
    "Educational demo only. Not official UGC advice. "
    "Always verify with [UGC Sri Lanka](https://www.ugc.ac.lk/)."
)

question = st.text_input(
    "Ask a question",
    placeholder="e.g. What is the maximum number of A/L attempts allowed?",
)

if question:
    with st.spinner("Searching handbook..."):
        hits = retrieve(question)
        confident = retrieval_confidence(hits)
        answer = answer_question(question)

    st.subheader("Answer")
    st.write(answer)

    st.subheader("Retrieved sources")
    if not confident:
        st.info("Low retrieval confidence — answer may be refused.")

    for i, hit in enumerate(hits, start=1):
        m = hit["metadata"]
        label = (
            f"[{i}] {m.get('doc_type', 'content')} | "
            f"Section: {m.get('section') or 'N/A'} | "
            f"pp. {m['page_start']}-{m['page_end']} | "
            f"RRF: {hit.get('rrf_score', 0):.4f}"
        )
        with st.expander(label):
            st.text(hit["text"][:1200])