import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
import requests

st.set_page_config(page_title="EduHelper AI Bot", page_icon="🎓", layout="wide")

st.title("🎓 EduHelper AI Chatbot")
st.caption("Belajar lebih mudah dengan AI yang santai, Kamu semangat? aku juga semangat!!!")

with st.sidebar:
    st.subheader("⚙️ Pengaturan")
    google_api_key = st.text_input("Google AI API Key", type="password")
    reset_button = st.button("🔄 Reset Chat")

    st.markdown("### ℹ️ Tentang Bot")
    st.info("""
    **EduHelper AI** membantu belajar dengan cara:
    - Menjawab pertanyaan pelajaran
    - Memberikan Informasi yang jelas dan lengkap
    - Memberikan penjelasan dengan santai
    """)

EXA_API_KEY = "49f8d839-10d5-44cb-8293-db7ce63e3fc0"

if not google_api_key:
    st.info("Silakan masukkan Google AI API Key di sidebar untuk mulai chatting.", icon="🗝️")
    st.stop()

if ("agent" not in st.session_state) or (getattr(st.session_state, "_last_key", None) != google_api_key):
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.7
        )

        st.session_state.agent = create_react_agent(
            model=llm,
            tools=[],
            prompt=(
                "Kamu adalah EduHelper AI, asisten belajar yang santai dan jelas. "
                "Bisa menjawab pertanyaan dan mengambil referensi dari web jika diperlukan."
            )
        )

        st.session_state._last_key = google_api_key
        st.session_state.pop("messages", None)
    except Exception as e:
        st.error(f"Invalid API Key atau konfigurasi salah: {e}")
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

if reset_button:
    st.session_state.pop("agent", None)
    st.session_state.pop("messages", None)
    st.rerun()

def search_exa(query):
    try:
        headers = {"Authorization": f"Bearer {EXA_API_KEY}"}
        url = f"https://api.exa.ai/search?q={query}&numResults=3"
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            results = [f"- [{r['title']}]({r['url']})" for r in data.get("results", [])]
            return "\n".join(results) if results else "Tidak ada hasil dari Exa."
        else:
            return f"Gagal fetch data Exa: {res.status_code}"
    except Exception as e:
        return f"Error Exa API: {e}"

for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🧑"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(msg["content"])

prompt = st.chat_input("Tanyakan sesuatu seperti materi pelajaran atau hanya ingin ngobrol santai...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        bot_placeholder = st.empty()
        bot_placeholder.markdown("⏳ Sedang mencari jawaban...")

    answer = ""
    try:
        if "cari" in prompt.lower():
            exa_results = search_exa(prompt)
            prompt += f"\n\n📚 Hasil pencarian web (Exa):\n{exa_results}"

        messages = []
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        response = st.session_state.agent.invoke({"messages": messages})
        if "messages" in response and len(response["messages"]) > 0:
            answer = response["messages"][-1].content
        else:
            answer = "Hmm, aku belum bisa menjawab itu."
    except Exception as e:
        answer = f"Terjadi error: {e}"

    bot_placeholder.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
