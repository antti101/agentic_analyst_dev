import streamlit as st
from src.main import EnhancedDataPlatformApp
from src.data_agent_duckdb import DataAgentDuckDB
import nest_asyncio, concurrent.futures, json, re, pandas as pd

nest_asyncio.apply()

# ---- Page setup ----
st.set_page_config(
    page_title="Ahava Finance Business Partner",
    page_icon="assets/Color logo with background.png",
    layout="wide",
)

# ---- Global Styling ----
st.markdown(
    """
    <style>
    :root {
        --ahava-blue: #1e90a0;
        --ahava-lightblue: #eaf4fb;
        --ahava-bg: #f6f9fb;
        --ahava-text: #1b2b42;
    }

    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        color: var(--ahava-text) !important;
        border-right: 1px solid #e1e5ea;
        box-shadow: 0 0 8px rgba(0,0,0,0.04);
    }

    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #f9fbfc 0%, #f3f7f9 100%);
        color: var(--ahava-text);
    }

    div[data-testid="stChatMessage"][data-testid*="assistant"] {
        background-color: var(--ahava-lightblue);
        border-radius: 12px;
        padding: 12px 18px;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background-color: #f8f9fa;
        border-radius: 12px;
        padding: 12px 18px;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }

    div[data-testid='stChatMessage'] p {
        font-size: 15.5px !important;
        line-height: 1.55;
        color: var(--ahava-text);
    }

    ul {
        margin: 0;
        padding-left: 20px;
        list-style-type: disc;
    }

    li {
        margin-bottom: 6px;
        font-size: 15.2px;
        line-height: 1.55;
        color: #1a1a1a;
    }

    hr {
        border: none;
        height: 1px;
        background-color: #e1e5ea;
        margin: 1rem 0;
    }

    .stDataFrame {
        background-color: white !important;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---- Sidebar ----
with st.sidebar:
    st.image("assets/Color logo with background.png", use_container_width=True)
    st.markdown("### Ahava Consulting")
    st.caption("Enabling intelligent finance through AI and semantics.")
    st.markdown("---")
    st.header("About 💡")
    st.markdown("""
    **Ahava’s Finance Intelligence Layer (FIL)**  
    interprets natural language finance questions and delivers structured, data-driven insights.
    """)
    st.markdown("---")
    st.subheader("Try asking:")
    st.markdown("""
    1️⃣ *Show SG&A variance by Function for EMEA in Q3 2025*  
    2️⃣ *How has SG&A trended for Marketing across regions over the last four quarters?*
    3️⃣ *How efficient is EMEA in converting Net Revenue into Operating Profit compared to APAC?*
    """)
    st.markdown("---")
    st.caption("Built with Streamlit, powered by OpenAI, using Ahava’s Finance Intelligence Layer (FIL).")

# ---- Header ----
st.markdown(
    """
    <div style="
        text-align: center;
        margin-top: -5px;
        margin-bottom: 15px;
    ">
        <h1 style="color: #1b2b42; font-family: 'Segoe UI', Roboto, sans-serif; font-weight: 600; margin-bottom: 6px;">
            Ahava Finance Business Partner
        </h1>
        <p style="color: #4a4a4a; font-size: 16px; margin-top: 0;">
            Your intelligent finance partner for analysis, planning, and performance insights.
        </p>
    </div>
    <hr style="border: none; height: 1px; background-color: #e1e5ea; margin: 1rem 0;">
    """,
    unsafe_allow_html=True
)

# ---- Initialize core components ----
if "app" not in st.session_state:
    st.session_state.app = EnhancedDataPlatformApp()

if "data_agent" not in st.session_state:
    st.session_state.data_agent = DataAgentDuckDB("assets/finance_sample_dataset.csv")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I’m your Ahava Finance Business Partner — powered by FIL. How can I help you today?",
        }
    ]

# ---- Display chat history ----
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---- Handle user input ----
if prompt := st.chat_input("Ask about your financials, planning, or performance..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # ---------- STEP 1: Intent detection ----------
    if "pending_json" not in st.session_state:
        with st.chat_message("assistant"):
            st.write("Analyzing your request...")
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    result = executor.submit(
                        st.session_state.app.chat_with_bi_analyst,
                        prompt,
                        st.session_state.messages,
                    ).result()

                response = result.get("content", str(result)) if isinstance(result, dict) else str(result)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

                # --- STEP 1a: Detect if model is clarifying ---
                if re.search(r"is that correct|confirm|clarify|would you like", response.lower()) and "{" not in response:
                    pass

                # --- STEP 1b: Extract JSON if provided ---
                match = re.search(r"```json\s*({[\s\S]*?})\s*```|(\{[\s\S]*?\})", response)
                if match:
                    json_text = match.group(1) or match.group(2)
                    st.session_state.pending_json = json_text
                    st.session_state.confirmation_needed = True
                else:
                    if not re.search(r"confirm|clarify|variance|compare|analyze", response.lower()):
                        st.warning("I couldn’t find a structured query. Could you rephrase that slightly?")

            except Exception as e:
                st.error(f"Error interpreting your question: {str(e)}")

    # ---------- STEP 2: Execute confirmed query ----------
    elif "pending_json" in st.session_state and st.session_state.confirmation_needed:
        try:
            json_text = st.session_state.pending_json
            query_json = json.loads(json_text)

            with st.chat_message("assistant"):
                st.write("📊 **Finance Cube Query**")
                df, sql = st.session_state.data_agent.execute_json_query(query_json)
                st.code(sql, language="sql")

                numeric_cols = df.select_dtypes(include=["number"]).columns
                if not df.empty and len(numeric_cols) > 0:
                    df = df[(df[numeric_cols] != 0).any(axis=1)]

                if not df.empty:
                    st.dataframe(df, use_container_width=True)

                    # Get summary with clean HTML formatting
                    summary = st.session_state.data_agent.summarize_results(query_json, df)
                    safe_summary = summary.strip()

                    st.markdown(
                        f"""
                        <div style="
                            background-color: #e8f6f0;
                            border-left: 6px solid #27ae60;
                            border-radius: 10px;
                            padding: 16px 20px;
                            margin-top: 15px;
                            font-family: 'Segoe UI', Roboto, sans-serif;
                            font-size: 15.5px;
                            line-height: 1.55;
                            color: #1a1a1a;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                        ">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                                <span style="font-size: 22px;">🧠</span>
                                <span style="font-weight: 600; font-size: 17px; color: #1b4332;">Summary Insight</span>
                            </div>
                            {safe_summary}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    assistant_text = (
                        f"#### 📊 Finance Cube Query\n"
                        f"```sql\n{sql}\n```\n\n"
                        f"{df.head().to_markdown(index=False)}\n\n"
                        f"#### 🧠 Summary Insight\n\n{summary}"
                    )
                    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
                else:
                    st.warning("No data available for this selection.")

            del st.session_state.pending_json
            st.session_state.confirmation_needed = False

        except Exception as e:
            st.error(f"Error executing query: {str(e)}")
