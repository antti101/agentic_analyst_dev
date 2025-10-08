import os
import json
from openai import AzureOpenAI

class EnhancedDataPlatformApp:
    """Handles LLM interactions for both conversational and strict-JSON modes, enriched by the full semantic layer."""

    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            azure_endpoint="https://ahava-agentic-fbp-mini.cognitiveservices.azure.com/",
            api_version="2024-12-01-preview",
        )
        self.semantic_layer = self._load_semantic_layer("assets/semantic_layer.txt")

    # -------------------------------------------------------------------------
    # Load and include the full semantic layer
    # -------------------------------------------------------------------------
    def _load_semantic_layer(self, file_path):
        """Load full semantic layer JSONL and render it in a structured readable format."""
        if not os.path.exists(file_path):
            return "Semantic layer file not found."

        try:
            measures, dimensions, facts = [], [], []
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    entry = f"- {data['name']} ({data.get('group','')}): {data.get('hint','')}"
                    group = data.get("group", "")
                    if group == "measures":
                        measures.append(entry)
                    elif group == "dimensions":
                        dimensions.append(entry)
                    elif group == "facts":
                        facts.append(entry)

            semantic_text = [
                "Finance Semantic Layer",
                "-----------------------",
                "",
                "FACT TABLES:",
                *facts,
                "",
                "MEASURES:",
                *measures,
                "",
                "DIMENSIONS:",
                *dimensions,
                "",
            ]
            return "\n".join(semantic_text)
        except Exception as e:
            return f"Semantic layer could not be loaded: {e}"

    # -------------------------------------------------------------------------
    # Build prompt (conversation vs strict JSON)
    # -------------------------------------------------------------------------
    def _build_prompt(self, force_json: bool = False):
        if force_json:
            # STRICT JSON MODE
            return (
                "You are a financial semantic query generator for the Finance cube.\n"
                "You must output only valid JSON defining analytic queries.\n"
                "Use measure and dimension names exactly as listed in the semantic layer below.\n\n"
                f"{self.semantic_layer}\n\n"
                "Follow this schema:\n"
                "{\n"
                '  "intent": "variance" | "trend" | "composition" | "ranking" | "detail",\n'
                '  "measures": ["Finance.VAR SG&A Expenses"],\n'
                '  "dimensions": ["Finance.Region", "Finance.Period"],\n'
                '  "filters": [\n'
                '    {"member": "Finance.Region", "operator": "equals", "values": ["APAC"]},\n'
                '    {"member": "Finance.Period", "operator": "equals", "values": ["Q3 2025"]}\n'
                '  ]\n'
                "}\n"
                "Output JSON only — no explanations or commentary."
            )

        else:
            # CONVERSATIONAL ANALYST MODE
            return (
                "You are a **Senior Business Intelligence Analyst** specialized in FP&A and semantic data modeling.\n"
                "You interpret financial questions and translate them into structured analytic queries.\n"
                "You understand measures, dimensions, and hierarchies, and you use the Finance semantic layer "
                "to ensure correct terminology and definitions.\n\n"
                "Behavior:\n"
                "- If greeted, introduce yourself politely as a Finance Analyst.\n"
                "- If asked a question, clarify and confirm what the user means before providing your JSON.\n"
                "- Always enclose the structured JSON query in triple backticks with a `json` tag.\n"
                "- Base your reasoning on the semantic layer definitions below — use the provided hints to choose the most accurate measure or dimension.\n\n"
                f"{self.semantic_layer}\n\n"
                "Example format:\n"
                "You want to analyze SG&A variance by Function for EMEA in Q3 2025 — is that correct?\n\n"
                "```json\n"
                "{\n"
                '  \"intent\": \"variance\",\n'
                '  \"measures\": [\"Finance.VAR SG&A Expenses\"],\n'
                '  \"dimensions\": [\"Finance.Function\"],\n'
                '  \"filters\": [\n'
                '    {\"member\": \"Finance.Region\", \"operator\": \"equals\", \"values\": [\"EMEA\"]},\n'
                '    {\"member\": \"Finance.Period\", \"operator\": \"equals\", \"values\": [\"Q3 2025\"]}\n'
                '  ]\n'
                "}\n"
                "```"
            )

    # -------------------------------------------------------------------------
    # Send chat to Azure OpenAI
    # -------------------------------------------------------------------------
    def chat_with_bi_analyst(self, prompt, history=None, force_json=False):
        system_prompt = self._build_prompt(force_json)
        messages = [{"role": "system", "content": system_prompt}]

        if history:
            for m in history[-5:]:
                messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": prompt})

        completion = self.client.chat.completions.create(
            model="agentic-fbp-mini",
            messages=messages,
            temperature=0.2 if force_json else 0.4,
            max_tokens=800,
        )
        return completion.choices[0].message.content.strip()
