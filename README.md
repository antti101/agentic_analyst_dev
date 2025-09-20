# Cube Analyst

A semantic layer analysis tool that provides intelligent access to cube-based data models through natural language queries and AI-powered business intelligence assistance.

## Features

- **Semantic Layer Parsing**: Reads JSONL semantic layer files containing measures and dimensions.
- **AI-Powered BI Analyst**: Chat with an AutoGen-powered agent for intelligent data analysis using a simple Streamlit interface.
- **Externalized Configuration**: All prompts, model settings, and file paths are managed in configuration files, not hardcoded.
- **Interactive CLI**: A simple command-line interface for directly testing and exploring your semantic layer without the agent.

## Project Structure

```
cube_analyst/
├── assets/
│   ├── config.yaml             # Main configuration for the application
│   └── semantic_layer.txt      # JSONL file with semantic layer data
├── docs/
│   └── DOCS.md                 # Project documentation
├── prompts/
│   └── bi_analyst_prompt.txt   # The system prompt for the agent
├── src/
│   ├── __init__.py
│   ├── main.py                 # Main application with the agent
│   ├── main_simple.py          # CLI for direct semantic layer testing
│   ├── config_loader.py        # Configuration management
│   └── semantic_layer_mcp.py   # Core semantic layer and agent logic
├── .env.example                # Environment variables template
├── .env                        # Your local environment variables
├── requirements.txt            # Python dependencies
└── streamlit_app.py            # The entry point for the web application
```

## Installation

1.  **Clone the repository**

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    Create a `.env` file from the example and add your OpenAI API key.
    ```bash
    cp .env.example .env
    # Edit .env with your OpenAI API key
    ```

## Usage

### Main Application (Web UI)

The primary way to use the application is through the Streamlit web interface.

```bash
streamlit run streamlit_app.py
```

### Command-Line Usage

*Note: Run all `src` scripts as modules from the project root directory.*

#### Agent CLI (Interactive Chat)

To have a stateful, multi-turn conversation with the AI agent directly in your terminal, run the main application:

```bash
python -m src.main
```
This will start an interactive session where the agent remembers the context of your conversation.

#### Semantic Layer CLI (Direct Testing)

To test the semantic layer directly without the AI agent, you can use `main_simple.py`. This is useful for verifying that your `assets/semantic_layer.txt` file is structured correctly.

```bash
# List all available cubes
python -m src.main_simple --cubes

# Get details for a specific cube
python -m src.main_simple --cube "Orders"

# Search for items
python -m src.main_simple --search "net_sales"
```

## Configuration

-   **`assets/config.yaml`**: The main configuration file. You can change the LLM model, temperature, and file paths here. You can also set `autogen.bi_analyst.agent_silent` to `false` to see the agent's full thought process and tool calls printed in your console for debugging. Set it to `true` for a cleaner output.
-   **`prompts/bi_analyst_prompt.txt`**: Contains the entire system prompt for the AI agent. You can edit this file to change the agent's persona, instructions, or capabilities.
-   **`.env`**: Used for storing secrets, primarily the `OPENAI_API_KEY`.