Tired of waiting for data reports? 😫 What if your team could just *ask* for the insights they need in plain English?

That's the idea behind **Cube Analyst**, a proof-of-concept conversational BI agent I've been building! 🤖 It uses an LLM to understand user questions, explore a semantic layer, and build structured queries for data analysis.

### Key Features:

- 🗣️ **Natural Language Interface:** No more SQL! Just ask questions and get answers.
- 🧠 **DIY Semantic Layer:** It's powered by a simple text file that defines business logic (cubes, measures, dimensions). This makes it a lightweight, build-it-yourself alternative to a full Metric Compute Protocol (MCP) server.
- 🚀 **AutoGen & Python:** Built with a modern, agentic stack using Microsoft's AutoGen framework. The agent generates queries compatible with data API tools like **Cube.js**.

### The Vision

The goal is to democratize data access and speed up decision-making. Our demo is tailored for the pharmacy industry 💊, but the architecture is domain-agnostic and can be adapted for finance, e-commerce, logistics, and more simply by changing the semantic layer file.


This project was built with the powerful **Microsoft AutoGen** library:
[https://github.com/microsoft/autogen](https://github.com/microsoft/autogen)

It's also inspired by the concepts in Microsoft's **Model Context Protocol (MCP) for Beginners** course, a great resource for building connected AI applications:
[https://microsoft.github.io/mcp-for-beginners/](https://microsoft.github.io/mcp-for-beginners/)

The project also builds on ideas about the new generation of analytic insights, similar to those discussed in this great post I read recently:

#AutoGen #LLM #DataAnalytics #BusinessIntelligence #Python #AI #ConversationalAI #SemanticLayer #MCP #CubeJS
