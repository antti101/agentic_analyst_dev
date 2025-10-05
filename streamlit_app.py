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
st.caption("Your AI-powered FP&A co-pilot for financial insights, planning, and variance analysis.")

# ---- Sidebar ----
with st.sidebar:
    st.header("About 💡")
    st.markdown("""
    This assistant helps finance teams analyze and interpret performance across  
    **Accounts, Scenarios, Periods, Business Units, and Functions** — powered by  
    OneStream-style data and Ahava’s semantic finance layer.

    **Example questions:**
    - “Compare OPEX by Function for Actual vs Budget in Q3.”
    - “What’s the EBIT margin for Wilson in FY2024?”
    - “Show SG&A variance for EMEA by Function.”
    """)
    st.markdown("---")
    st.markdown("Built by **Ahava Consulting** — powered by Databricks, Streamlit, and OpenAI.")

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
                    if isinstance(response, dict):
                        assistant_message = response.get("content", str(response))
                    else:
                        assistant_message = str(response)
                else:
                    assistant_message = "Sorry, I couldn't get a response from the analyst."

            except Exception as e:
                assistant_message = f"⚠️ Error: {str(e)}"

            st.markdown(assistant_message)

    # Save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": assistant_message})
