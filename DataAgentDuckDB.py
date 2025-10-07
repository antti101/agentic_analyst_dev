import duckdb
import re
import pandas as pd


class DataAgentDuckDB:
    def __init__(self, csv_path="assets/finance_sample_dataset.csv"):
        self.csv_path = csv_path
        self.con = duckdb.connect(database=":memory:")
        self._load_data_and_create_view()

    # ---------- INITIAL LOAD ----------
    def _load_data_and_create_view(self):
        # Load dataset
        self.con.execute(f"""
            CREATE TABLE finance_raw AS
            SELECT * FROM read_csv_auto('{self.csv_path}', header=True);
        """)

        # Create cube-like view (adds ACT, BUD, Variance, VariancePct)
        self.con.execute("""
                    CREATE OR REPLACE VIEW finance_view AS
                    SELECT
                        Year,
                        Quarter,
                        Period,
                        Brand,
                        Region,
                        Function,
                        Account,
                        SUM(CASE WHEN Scenario = 'ACT' THEN Value END) AS ACT,
                        SUM(CASE WHEN Scenario = 'BUD' THEN Value END) AS BUD,
                        (SUM(CASE WHEN Scenario = 'ACT' THEN Value END)
                        - SUM(CASE WHEN Scenario = 'BUD' THEN Value END)) AS VAR,
                        CASE 
                            WHEN SUM(CASE WHEN Scenario = 'BUD' THEN Value END) <> 0 THEN
                                ROUND(
                                    (SUM(CASE WHEN Scenario = 'ACT' THEN Value END)
                                    - SUM(CASE WHEN Scenario = 'BUD' THEN Value END))
                                    * 100.0 / SUM(CASE WHEN Scenario = 'BUD' THEN Value END), 2)
                        END AS VAR_PCT
                    FROM finance_raw
                    GROUP BY Year, Quarter, Period, Brand, Region, Function, Account;

        """)
        print("✅ finance_view created successfully")

    # ---------- MAIN EXECUTOR ----------
    def execute_query(self, plan: dict):
        """
        plan example:
        {
          "intent": "variance",
          "metric": "SG&A Expenses",
          "dimension": "Region",
          "period": "Q3",
          "filters": {"Region": ["APAC", "NA"]}
        }
        """
        intent = (plan.get("intent") or "variance").lower()
        metric = self._clean(plan.get("metric", ""))
        dimension = plan.get("dimension", "Region")
        period = plan.get("period", "")
        filters = plan.get("filters", {})

        sql = self._build_sql(intent, metric, dimension, period, filters)
        df = self.con.execute(sql).df()

        totals = {
            "ACT": df["ACT"].sum() if "ACT" in df else None,
            "BUD": df["BUD"].sum() if "BUD" in df else None,
            "Variance": df["Variance"].sum() if "Variance" in df else None,
            "VariancePct": (
                round((df["Variance"].sum() / df["BUD"].sum()) * 100, 2)
                if "BUD" in df and df["BUD"].sum() != 0 else None
            )
        }

        return {
            "plan": plan,
            "sql_used": sql.strip(),
            "totals": totals,
            "rows": df.to_dict(orient="records")
        }

    # ---------- BUILD SQL ----------
    def _build_sql(self, intent, metric, dimension, period, filters):
        where = []
        if metric:
            where.append(f"LOWER(Account) LIKE LOWER('%{metric}%')")
        if period:
            where.append(f"LOWER(Period) LIKE LOWER('%{period}%')")
        for dim, vals in filters.items():
            vals_sql = ", ".join([f"'{v}'" for v in vals])
            where.append(f"{dim} IN ({vals_sql})")
        where_clause = "WHERE " + " AND ".join(where) if where else ""

        group_by = "Quarter" if intent == "trend" else dimension

        sql = f"""
        SELECT {group_by},
               SUM(ACT) AS ACT,
               SUM(BUD) AS BUD,
               SUM(Variance) AS Variance,
               ROUND(AVG(VariancePct), 2) AS VariancePct
        FROM finance_view
        {where_clause}
        GROUP BY {group_by}
        ORDER BY Variance DESC;
        """
        return sql

    def _clean(self, s):
        return re.sub(r"[^a-zA-Z0-9 &'’]", "", s).strip()


# ---------- DEMO QUERIES ----------
if __name__ == "__main__":
    agent = DataAgentDuckDB("assets/finance_sample_dataset.csv")

    # Question 1 — SG&A variance by Region
    q1 = {
        "intent": "variance",
        "metric": "SG&A Expenses",
        "dimension": "Region",
        "period": "Q3"
    }
    result1 = agent.execute_query(q1)
    print("\n🧠 Question 1: SG&A variance by Region in Q3")
    print(result1, "\n")

    # Question 2 — Net Revenue trend
    q2 = {
        "intent": "trend",
        "metric": "Net Revenue"
    }
    result2 = agent.execute_query(q2)
    print("📈 Question 2: Net Revenue trend by Quarter")
    print(result2)
