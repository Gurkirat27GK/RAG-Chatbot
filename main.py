import streamlit as st
from vector_store import get_vector_store
import config
from langchain_core.prompts import PromptTemplate
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers.multi_query import MultiQueryRetriever
import time


# -------------------------------------------------
# STEP 1: Set up Streamlit Page Configuration
# -------------------------------------------------
st.set_page_config(
    page_title="RAG Chatbot", 
    page_icon="💬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------
# STEP 2: Define custom CSS for styling UI
# -------------------------------------------------
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-style: italic;
    }
    
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        margin: 0.5rem 0;
        margin-left: 20%;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 20px 5px;
        margin: 0.5rem 0;
        margin-right: 20%;
        box-shadow: 0 2px 10px rgba(240, 147, 251, 0.3);
    }
    
    .thinking-spinner {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 15px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    
    .sidebar-info {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .feature-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
    
    .stat-box {
        text-align: center;
        padding: 1rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        min-width: 100px;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #667eea;
    }
    
    .stat-label {
        color: #666;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# STEP 3: Build Sidebar (Info, Stats, Features, Clear button)
# -------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-info">
        <h3>🤖 RAG Chatbot</h3>
        <p>Powered by AI and your PDF knowledge base</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Chat Statistics")

    # ✅ compute directly from session_state (always up-to-date)
    total_messages = len(st.session_state.get("messages", []))
    user_messages = len([msg for msg in st.session_state.get("messages", []) if msg["role"] == "user"])

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{total_messages}</div>
            <div class="stat-label">Total Messages</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{user_messages}</div>
            <div class="stat-label">Questions Asked</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### ✨ Features")
    st.markdown("""
    <div class="feature-box">
        <strong>🔍 Smart Search</strong><br>
        Finds relevant information from your PDFs
    </div>
    <div class="feature-box">
        <strong>🧠 AI-Powered</strong><br>
        Uses advanced language models
    </div>
    <div class="feature-box">
        <strong>💬 Context-Aware</strong><br>
        Maintains conversation history
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

# -------------------------------------------------
# STEP 4: Display App Header and Sub-title
# -------------------------------------------------
st.markdown('<h1 class="main-header">💬 RAG Chatbot</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Chat with your PDF knowledge base using AI</p>', unsafe_allow_html=True)

# -------------------------------------------------
# STEP 5: Initialize Chat Container + History
# -------------------------------------------------
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if not st.session_state["messages"]:
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                color: white; border-radius: 15px; margin: 1rem 0;">
        <h3>👋 Welcome to RAG Chatbot!</h3>
        <p>Ask me anything about your PDF documents. I'll search through your knowledge base to provide accurate answers.</p>
        <p><em>Try asking: "What is the main topic?" or "Can you summarize the key points?"</em></p>
    </div>
    """, unsafe_allow_html=True)

# Display chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(f'<div class="user-message">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-message">{msg["content"]}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------
# STEP 6: Take User Input (Chat Box at Bottom)
# -------------------------------------------------
if user_question := st.chat_input("💭 Type your question here..."):
    # Add user message to chat history
    st.session_state["messages"].append({"role": "user", "content": user_question})

    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(f'<div class="user-message">{user_question}</div>', unsafe_allow_html=True)


    # -------------------------------------------------
    # STEP 7: Generate Assistant Response
    # -------------------------------------------------
    with st.chat_message("assistant"):
        with st.spinner(""):
            # (7a) Show temporary "thinking" spinner
            thinking_placeholder = st.empty()
            thinking_placeholder.markdown("""
                <div class="thinking-spinner">
                    <div style="margin-right: 10px;">🤔</div>
                    <div>Analyzing your question and searching through documents...</div>
                </div>
            """, unsafe_allow_html=True)        
            
            # (7b) Load retriever + LLM
            vector_store = get_vector_store()
            llm = config.llm

            # Use Multi Query Retriever (expands question into variations)
            retriever = MultiQueryRetriever.from_llm(
                retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
                llm=llm
            )

            # (7c) Define the Prompt Template
            prompt = PromptTemplate(
                template="""
                  You are a helpful assistant.
                  Use the conversation history and the provided document context to answer.
                  Answer ONLY from the provided transcript context.
                  If the context is insufficient, just say you don't know.

                  Conversation so far:
                  {chat_history}

                  Context from documents:
                  {context}

                  Now answer the latest question:
                  {question}
                """,
                input_variables=['chat_history', 'context', 'question']
            )

            # (7d) Prepare chat history string
            chat_history = ""
            for msg in st.session_state["messages"]:
                role = "User" if msg["role"] == "user" else "Assistant"
                chat_history += f"{role}: {msg['content']}\n"

            # (7e) Retrieve documents from Vector Store
            retrieved_docs = retriever.invoke(user_question)
            context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)

            # (7f) Fill prompt with actual values
            final_prompt = prompt.invoke({
                "chat_history": chat_history,
                "context": context_text,
                "question": user_question
            })

            # (7g) Stream the Assistant Response (word-by-word typing effect)
            response_placeholder = st.empty()   # placeholder for live updates
            bot_reply = ""                      # accumulate tokens here

            for chunk in llm.stream(final_prompt):
                if chunk.content:
                    # Clear the spinner once first token arrives
                    if thinking_placeholder:
                        thinking_placeholder.empty()
                        thinking_placeholder = None  
                    bot_reply += chunk.content   # append new token(s)
                    response_placeholder.markdown(
                        f'<div class="assistant-message">{bot_reply}</div>', 
                        unsafe_allow_html=True
                    )
                    time.sleep(.2)  # adjust typing speed (0.05s = ~20 chars/sec)

            # Final message stored in history
            st.session_state["messages"].append({"role": "assistant", "content": bot_reply})
