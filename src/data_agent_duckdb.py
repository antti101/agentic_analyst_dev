import duckdb
import pandas as pd
import json
import os
import numpy as np
from openai import AzureOpenAI


class DataAgentDuckDB:
    def __init__(self, csv_path="assets/finance_sample_dataset.csv"):
        self.csv_path = csv_path
        self.con = duckdb.connect(database=":memory:")
        self._load_data()

    # -------------------------------------------------------------------------
    def _load_data(self):
        """Load CSV and create Finance cube view with all key measures."""
        self.con.execute(f"""
            CREATE OR REPLACE TABLE finance_raw AS
            SELECT * FROM read_csv_auto('{self.csv_path}', header=True);
        """)

        # ===== Finance Cube View =====
        self.con.execute("""
            CREATE OR REPLACE VIEW Finance AS
            SELECT
                Year,
                Quarter,
                Period,
                Brand,
                Region,
                Function,

                -- ===== Net Revenue =====
                COALESCE(SUM(CASE WHEN Scenario='ACT' AND Account='Net Revenue' THEN Value END), 0) AS ACT_Net_Revenue,
                COALESCE(SUM(CASE WHEN Scenario='BUD' AND Account='Net Revenue' THEN Value END), 0) AS BUD_Net_Revenue,
                COALESCE(
                    (SUM(CASE WHEN Scenario='ACT' AND Account='Net Revenue' THEN Value END)
                     - SUM(CASE WHEN Scenario='BUD' AND Account='Net Revenue' THEN Value END)), 0
                ) AS VAR_Net_Revenue,
                CASE WHEN SUM(CASE WHEN Scenario='BUD' AND Account='Net Revenue' THEN Value END) <> 0
                     THEN ROUND(
                         (SUM(CASE WHEN Scenario='ACT' AND Account='Net Revenue' THEN Value END)
                          - SUM(CASE WHEN Scenario='BUD' AND Account='Net Revenue' THEN Value END))
                          * 100.0 / SUM(CASE WHEN Scenario='BUD' AND Account='Net Revenue' THEN Value END), 2)
                END AS VAR_PCT_Net_Revenue,

                -- ===== SG&A Expenses =====
                COALESCE(SUM(CASE WHEN Scenario='ACT' AND Account='SG&A Expenses' THEN Value END), 0) AS ACT_SGandA_Expenses,
                COALESCE(SUM(CASE WHEN Scenario='BUD' AND Account='SG&A Expenses' THEN Value END), 0) AS BUD_SGandA_Expenses,
                COALESCE(
                    (SUM(CASE WHEN Scenario='ACT' AND Account='SG&A Expenses' THEN Value END)
                     - SUM(CASE WHEN Scenario='BUD' AND Account='SG&A Expenses' THEN Value END)), 0
                ) AS VAR_SGandA_Expenses,
                CASE WHEN SUM(CASE WHEN Scenario='BUD' AND Account='SG&A Expenses' THEN Value END) <> 0
                     THEN ROUND(
                         (SUM(CASE WHEN Scenario='ACT' AND Account='SG&A Expenses' THEN Value END)
                          - SUM(CASE WHEN Scenario='BUD' AND Account='SG&A Expenses' THEN Value END))
                          * 100.0 / SUM(CASE WHEN Scenario='BUD' AND Account='SG&A Expenses' THEN Value END), 2)
                END AS VAR_PCT_SGandA_Expenses,

                -- ===== Operating Profit =====
                COALESCE(SUM(CASE WHEN Scenario='ACT' AND Account='Operating Profit' THEN Value END), 0) AS ACT_Operating_Profit,
                COALESCE(SUM(CASE WHEN Scenario='BUD' AND Account='Operating Profit' THEN Value END), 0) AS BUD_Operating_Profit,
                COALESCE(
                    (SUM(CASE WHEN Scenario='ACT' AND Account='Operating Profit' THEN Value END)
                     - SUM(CASE WHEN Scenario='BUD' AND Account='Operating Profit' THEN Value END)), 0
                ) AS VAR_Operating_Profit,
                CASE WHEN SUM(CASE WHEN Scenario='BUD' AND Account='Operating Profit' THEN Value END) <> 0
                     THEN ROUND(
                         (SUM(CASE WHEN Scenario='ACT' AND Account='Operating Profit' THEN Value END)
                          - SUM(CASE WHEN Scenario='BUD' AND Account='Operating Profit' THEN Value END))
                          * 100.0 / SUM(CASE WHEN Scenario='BUD' AND Account='Operating Profit' THEN Value END), 2)
                END AS VAR_PCT_Operating_Profit

            FROM finance_raw
            GROUP BY Year, Quarter, Period, Brand, Region, Function
            HAVING 
                COALESCE(SUM(CASE WHEN Scenario='ACT' THEN Value END), 0) <> 0 OR
                COALESCE(SUM(CASE WHEN Scenario='BUD' THEN Value END), 0) <> 0
            ;
        """)

        # Cache column names for fuzzy matching
        self.columns = [
            c for c in self.con.execute("DESCRIBE Finance").df()["column_name"].tolist()
        ]
        print("✅ Finance cube initialized successfully with all measures (zeros filtered)")

    # -------------------------------------------------------------------------
    def execute_json_query(self, query_json: dict):
        """Translate structured JSON query into SQL and execute on the Finance cube."""
        intent = query_json.get("intent", "").lower()
        measures = query_json.get("measures", [])
        dimensions = query_json.get("dimensions", [])
        filters = query_json.get("filters", [])

        # --- Normalize field names ---
        def normalize(name: str) -> str:
            if not name:
                return ""
            name = name.split(".")[-1] if "." in name else name
            name = (
                name.replace(" ", "_")
                    .replace("&", "and")
                    .replace("-", "_")
                    .replace("__", "_")
                    .strip()
            )
            for c in self.columns:
                if c.lower() == name.lower():
                    return c
            return name

        measures = [normalize(m) for m in measures]
        dimensions = [normalize(d) for d in dimensions]

        # --- Normalize Period filters ---
        def normalize_period(val: str):
            import re
            # Case 1: Q3 2025 → 2025-Q3
            match = re.match(r"Q([1-4])\s*(\d{4})", val)
            if match:
                q, y = match.groups()
                return f"{y}-Q{q}"
            # Case 2: 2025 → all quarters
            match_year = re.match(r"(\d{4})", val)
            if match_year:
                y = match_year.group(1)
                return [f"{y}-Q1", f"{y}-Q2", f"{y}-Q3", f"{y}-Q4"]
            return val

        normalized_filters = []
        for f in filters:
            member = f.get("member", "")
            if "Period" in member:
                new_values = []
                for v in f.get("values", []):
                    p = normalize_period(v)
                    if isinstance(p, list):
                        new_values.extend(p)
                    else:
                        new_values.append(p)
                f["values"] = new_values
            normalized_filters.append(f)
        filters = normalized_filters

        # --- Default to Year 2025 if no Period filter is present ---
        period_exists = any("Period" in f.get("member", "") for f in filters)
        if not period_exists:
            filters.append({
                "member": "Finance.Period",
                "operator": "equals",
                "values": ["2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4"]
            })

        # --- Build SELECT clause ---
        select_fields = [f'"{d}"' for d in dimensions] + [
            f'SUM("{m}") AS "{m}"' for m in measures
        ]
        select_sql = ", ".join(select_fields)
        group_sql = ", ".join([f'"{d}"' for d in dimensions]) if dimensions else ""

        # --- Build WHERE clause ---
        where_clauses = []
        for f in filters:
            member = normalize(f.get("member", ""))
            vals = ", ".join([f"'{v}'" for v in f.get("values", [])])
            where_clauses.append(f'"{member}" IN ({vals})')
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # --- Build and execute SQL ---
        sql = f"""
        SELECT {select_sql}
        FROM Finance
        {where_sql}
        {"GROUP BY " + group_sql if group_sql else ""}
        ;
        """

        try:
            df = self.con.execute(sql).df()
        except Exception as e:
            raise Exception(f"[ERROR] SQL failed: {e}\n\n{sql}")

        return df, sql

    # -------------------------------------------------------------------------
    def summarize_results(self, query_json: dict, df: pd.DataFrame):
        """Generate a grounded executive summary using Azure OpenAI with dynamic data inclusion."""
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            azure_endpoint="https://ahava-agentic-fbp-mini.cognitiveservices.azure.com/",
            api_version="2024-12-01-preview",
        )

        if df.empty:
            return "⚠️ No data found for the selected filters. Please check your query parameters."

        # --- Remove zero-only rows before summarization ---
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if not df.empty and len(numeric_cols) > 0:
            df = df[(df[numeric_cols] != 0).any(axis=1)]

        # --- Intelligent Data Inclusion Strategy ---
        num_rows = len(df)
        if num_rows <= 30:
            df_md = df.to_markdown(index=False)
            context_desc = f"Full dataset included ({num_rows} rows)."
        elif num_rows <= 200:
            df_md = df.head(30).to_markdown(index=False)
            stats_md = df.describe(include=[np.number]).to_markdown()
            df_md += f"\n\nSummary Statistics:\n{stats_md}"
            context_desc = f"Showing top 30 rows and summary stats from {num_rows} total rows."
        else:
            stats_md = df.describe(include=[np.number]).to_markdown()
            df_md = f"(Dataset truncated for size — {num_rows} rows total)\n\nSummary Statistics:\n{stats_md}"
            context_desc = "Large dataset truncated — showing summary statistics only."

        # --- Token-safe truncation ---
        def truncate_for_llm(text, max_tokens=1500):
            approx_char_limit = max_tokens * 4
            if len(text) > approx_char_limit:
                return text[:approx_char_limit] + "\n\n... (truncated for context)"
            return text

        df_md = truncate_for_llm(df_md)

        # --- Add default year note if assumed ---
        filters = query_json.get("filters", [])
        period_exists = any("Period" in f.get("member", "") for f in filters)
        assumed_note = ""
        if not period_exists:
            assumed_note = "(Assumed full year 2025 as no specific period was mentioned.)\n\n"

        # --- Prompt Construction ---
        prompt = f"""
        You are a **Finance Business Partner** summarizing results for leadership.

        {assumed_note}
        Context:
        - {context_desc}
        - Use actual numeric values and focus on the key measure(s) requested.
        - Exclude zero-only rows from discussion.
        - Be concise (4–6 sentences), analytical, and fact-based.
        - Highlight key findings, potential interesting facts, and segment by bulletpoints

        User Query JSON:
        {json.dumps(query_json, indent=2)}

        Data Preview:
        {df_md}
        """

        completion = client.chat.completions.create(
            model="agentic-fbp-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.25,
            max_tokens=350,
        )

        summary = completion.choices[0].message.content.strip()
        summary = summary.replace("_", " ").replace("*", "")  # clean artifacts
        return summary
