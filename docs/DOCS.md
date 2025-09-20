# Building a Conversational BI Analyst with Python and AutoGen

*A deep dive into creating a smart data chatbot that understands your business.* 

---

In today's data-driven world, the ability to quickly query and understand business metrics is crucial. However, this power is often locked away, accessible only to those who can write complex SQL queries or navigate intricate BI dashboards. What if you could simply *ask* for the data you need in plain English?

This project, **Cube Analyst**, is a proof-of-concept that does just that. It's a conversational AI agent, powered by Python and Microsoft's AutoGen framework, that acts as a personal Business Intelligence analyst. It allows users to ask questions about their data, clarifies their intent, and provides structured, actionable insights.

This article documents the architecture, challenges, and business value of this project, providing a roadmap for anyone looking to build a similar system.

## The Vision: A Domain-Agnostic BI Analyst

The core business value of Cube Analyst is the **democratization of data**. It empowers non-technical users to get complex data insights through simple conversation. While this project can be adapted to any business domain, we've tailored our example for a **pharmacy retail chain** to demonstrate a concrete business case.

### A Business Case: Pharmacy Chain Analytics

Imagine a manager for a chain of pharmacies. They need to make quick, data-informed decisions but don't have the time or SQL skills to dig into the data warehouse. With Cube Analyst, they can get answers instantly:

-   **Inventory Management:** A store manager could ask, *"Show me the current quantity and turnover days for prescription drugs in the Goods cube."* This helps them optimize stock levels and prevent shortages.
-   **Sales & Performance:** A regional director might ask, *"I need a report of net sales and gross margin for the top 5 selling products last month, grouped by store name."* This allows for quick performance comparisons.
-   **Patient Demographics:** A marketing analyst could ask, *"What is the age and gender distribution of Buyers for our new promotional campaign?"* This helps in targeting marketing efforts more effectively.

In each case, the agent understands the user's intent, helps them select the right metrics from the semantic layer (`Orders.net_sales`, `Goods.turnover_days`, `Buyer.customer_age`), and generates a structured query.

### Beyond the Pharmacy

The pharmacy example is just a starting point. Because the agent's knowledge is entirely defined by the `semantic_layer.txt` file, this architecture is highly adaptable. You could replace the pharmacy data with a semantic layer for e-commerce, logistics, finance, or any other domain, and the agent would instantly become an expert in that area. The core logic remains the same; only the metadata changes.

## Core Architecture

The system is composed of a clean `src` layout for code, an `assets` directory for data and configuration, and a Streamlit UI as the entry point.

```mermaid
graph TD
    A[User] --> B{Streamlit UI (streamlit_app.py)};
    
    subgraph Project Root
        B
    end

    B --> C{src/main.py};

    subgraph src
        C --> D[AutoGen Agent (BIAnalystAgent)];
        C --> E[config_loader.py];
        D --> F[semantic_layer_mcp.py];
    end

    subgraph assets
        G[config.yaml];
        H[semantic_layer.txt];
        I[prompts/bi_analyst_prompt.txt];
    end

    E --> G;
    F --> H;
    D --> I;
    D --> J[OpenAI LLM];
```

1.  **`streamlit_app.py`:** The entry point for the application. This simple, chat-based web interface remains in the project root.
2.  **`src` Directory:** Contains all Python source code, promoting a clean and scalable project structure.
3.  **`assets` Directory:** Contains all non-code files, including the semantic layer definition and configuration.
4.  **`prompts` Directory:** Contains the agent's system prompt, externalized for easy editing.

## The Semantic Layer: The Brains of the Operation

The most important concept in this architecture is the **semantic layer**. It's a business-friendly representation of your data. Instead of tables and columns, it defines concepts like:

-   **Cubes:** Functional areas of the business (e.g., `Orders`, `Goods`, `Buyer`).
-   **Measures:** Quantitative metrics (e.g., `Orders.net_sales`, `Goods.quantity`).
-   **Dimensions:** Attributes to group and filter by (e.g., `Orders.product_brand`, `Buyer.customer_city`).

By giving the agent access to tools that can query this layer, we ensure it is grounded in the actual data model and can intelligently suggest relevant metrics to the user.

## Motivation: A Lightweight, DIY Semantic Layer

While many in the data world talk about the Metric Compute Protocol (MCP), what if you could build a similar experience yourself with lightweight tools? This project explores that idea.

Here’s how this project differs from a "real" MCP server (like Cube or dbt Semantic Layer):

-   **What is Served:** A true MCP server connects to a data warehouse and serves *computed metric data* via an API. This project's `DataPlatformSemanticServer` doesn't compute anything. Instead, it serves *metadata* from a text file to an LLM agent. The agent reasons about what metrics are needed, and its final output is a structured request (a JSON object) that a downstream system could use to actually fetch the data.
-   **Simplicity & Speed:** Our semantic layer is a simple `JSONL` text file. It's incredibly fast to set up and can be version-controlled with Git. This is a stark contrast to the complex infrastructure required for a full MCP server.
-   **Use Case:** This project is ideal for rapid prototyping or for teams that want to build a natural language front-end without committing to heavy backend infrastructure.

In essence, Cube Analyst simulates the *discovery and query-building* part of a metrics platform, offloading the reasoning to an LLM. The final JSON output is designed to be compatible with the query format used by data API tools like Cube.js, effectively acting as a natural language layer on top of them.

## Building the Agent with AutoGen

We defined a `BIAnalystAgent` class that encapsulates the agent's setup. The core of this is the `ConversableAgent` from AutoGen, which is given its persona and instructions via an external prompt file.

```python
# From src/semantic_layer_mcp.py

# Load the prompt from an external file
with open("prompts/bi_analyst_prompt.txt", "r") as f:
    system_message = f.read()

self.bi_analyst = ConversableAgent(
    name="BIAnalyst",
    system_message=system_message,
    llm_config=self.llm_config,
    human_input_mode="NEVER",
The power of this approach lies in the `system_message`, which is loaded from `prompts/bi_analyst_prompt.txt`. This prompt gives the agent its personality, its capabilities, and its rules of engagement, including the instruction to generate JSON reports.

### Understanding AutoGen's Agents

To understand how our `BIAnalystAgent` works, it's helpful to know the roles of the two core AutoGen agent types we use:

-   **[`ConversableAgent`](https://microsoft.github.io/autogen/docs/reference/agentchat/conversable_agent):** This is the standard, general-purpose agent. It can have a conversation, use tools, and has a system prompt that defines its persona and skills. Our `bi_analyst` is a `ConversableAgent`. It's the "expert" that has the knowledge of the semantic layer and the tools to query it.

-   **[`UserProxyAgent`](https://microsoft.github.io/autogen/docs/reference/agentchat/user_proxy_agent):** This agent acts as a proxy for the human user. In a typical AutoGen setup, it's responsible for soliciting input from the user and, importantly, **executing code or tool calls** on the user's behalf. In our project, the `user_proxy` serves a more subtle but critical role. Since our `BIAnalystAgent` is not allowed to execute code itself for security reasons, it tells the `user_proxy` which tool to run. The `user_proxy` then executes the tool (like `get_cubes`) and sends the result back to the `BIAnalystAgent`.

This separation of "thinking" (the `ConversableAgent`) and "doing" (the `UserProxyAgent`) is a fundamental concept in AutoGen that enables safe and powerful agentic workflows.
)
```

## Technical Deep Dive: Overcoming Integration Hurdles

Integrating a conversational agent framework with a web framework like Streamlit required solving several common challenges.

#### Challenge 1: The Stateless Web

**Problem:** The agent had no memory between user messages.
**Solution:** We re-architected the chat logic to be stateful. Instead of using AutoGen's `initiate_chat` for every message, we switched to `generate_reply` and passed the full conversation history (stored in Streamlit's session state) with every turn.

#### Challenge 2: The Frozen UI

**Problem:** The app froze while waiting for the LLM to respond.
**Solution:** We moved the agent call to a separate thread using Python's `concurrent.futures.ThreadPoolExecutor`. This allows the UI to remain responsive and show a spinner while the agent works in the background.

## How to Run This Project

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Set Environment Variable:** Create a `.env` file and add your OpenAI API key:
    ```
    OPENAI_API_KEY="your-key-here"
    ```
3.  **Configure:** Review `assets/config.yaml` to ensure the settings are to your liking.
4.  **Run the App:**
    ```bash
    streamlit run streamlit_app.py
    ```

## Developer Tools: Testing the Semantic Layer

For developers, the project includes a simple command-line tool for inspecting the semantic layer directly: `src/main_simple.py`. This is the best way to verify that your `assets/semantic_layer.txt` file is correctly structured and that the data is what you expect the agent to see.

For example, to get all the details for the "Orders" cube, run this command from your project root:

```bash
python -m src.main_simple --cube "Orders"
```

This will print a clean JSON object to your terminal describing the cube's measures and dimensions, allowing you to debug the agent's knowledge base directly.

## Conclusion

This project demonstrates a powerful and flexible architecture for building conversational data assistants. By separating the UI, the agent logic (`src`), and the data/config (`assets`), we've created a system that is both capable and easy to maintain. The journey also highlighted key technical challenges and solutions that are critical for anyone building real-world agentic applications.