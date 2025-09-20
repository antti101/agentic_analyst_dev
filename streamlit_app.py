import streamlit as st
from src.main import EnhancedDataPlatformApp
import nest_asyncio
import concurrent.futures

nest_asyncio.apply()

st.title("Cube Analyst Chat")

# Initialize the app
if 'app' not in st.session_state:
    st.session_state.app = EnhancedDataPlatformApp()

# Initialize chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What is your question?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Run the chat in a separate thread to avoid blocking Streamlit
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    st.session_state.app.chat_with_bi_analyst, 
                    prompt, 
                    st.session_state.messages
                )
                response = future.result()  # Get the result from the future

            if response:
                if isinstance(response, dict):
                    assistant_message = response.get("content", str(response))
                else:
                    assistant_message = str(response)
            else:
                assistant_message = "Sorry, I couldn't get a response from the BI Analyst."
            
            st.markdown(assistant_message)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_message})
