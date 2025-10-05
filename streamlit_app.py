import streamlit as st
from src.main import EnhancedDataPlatformApp
import nest_asyncio
import concurrent.futures

# Allow async loops (important for notebooks / Streamlit concurrency)
nest_asyncio.apply()

# ---- App Header ----
st.set_page_config(
    page_title="Ahava Finance Business Partner",
    page_icon="💬",
    layout="wide",
)

st.title("💬 Ahava Finance Business Partner")
st.caption("A proof-of-concept digital finance partner built on Ahava’s Finance Intelligence Layer (FIL).")

# ---- Sidebar ----
with st.sidebar:
    st.header("About 💡")
    st.markdown("""
    **Ahava’s Finance Intelligence Layer (FIL)** is an AI-driven semantic and analytics engine  
    that interprets natural-language finance questions and delivers structured insights.

    This proof-of-concept demonstrates how FIL can analyze and explain performance using  
    **sample financial data**, simulating the connection to enterprise systems such as  
    **Power BI, Databricks, OneStream, and SAP Datasphere**.

    FIL understands financial context — accounts, periods, scenarios, and organizational  
    dimensions — to provide narrative insights on **revenue, costs, and profitability trends**.

    **Try asking:**
    - “Show SG&A variance by Function for Actual vs Budget in Q3.”
    - “Compare Operating Profit Actual vs Budget for Wilson by Quarter.”
    - “How is Net Revenue trending year-to-date vs Budget?”

    ---
    **About this PoC**
    - Demonstrates how semantic finance logic and AI reasoning come together  
      to support business partnering and decision-making.
    - Built with **Streamlit** for demonstration purposes; future versions will  
      integrate directly with enterprise finance systems.
    ---
    """)
    st.markdown("Built by **Ahava Consulting** — enabling intelligent finance through AI and semantics.")

# ---- Initialize Core App ----
if "app" not in st.session_state:
    st.session_state.app = EnhancedDataPlatformApp()

# ---- Initialize Chat History ----
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I’m your Ahava Finance Business Partner. How can I assist you with your financial insights today?"}
    ]

# ---- Display Chat History ----
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---- Handle User Input ----
if prompt := st.chat_input("Ask about your financials, planning, or performance..."):
    # Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking like a finance partner..."):
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        st.session_state.app.chat_with_bi_analyst,
                        prompt,
                        st.session_state.messages
                    )
                    response = future.result()

                if response:
                    assistant_message = response.get("content", str(response)) if isinstance(response, dict) else str(response)
                else:
                    assistant_message = "Sorry, I couldn’t get a response from the analyst."

            except Exception as e:
                assistant_message = f"⚠️ Error: {str(e)}"

            st.markdown(assistant_message)

    # Save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": assistant_message})
