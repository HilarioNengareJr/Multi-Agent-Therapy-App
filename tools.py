import logging
from langchain.tools import Tool
from datetime import datetime
from typing import List, Dict

# Setup logging
logging.basicConfig(level=logging.INFO)

# In-memory storage for simplicity (replace with DB later)
expense_log: List[Dict] = []

# --- Debug Utilities --- #
def log_llm_output(raw_output: str):
    logging.info("LLM RAW OUTPUT:\n" + raw_output)

def log_parsing_error(raw_output: str, error: Exception):
    logging.error(f"Failed to parse structured expense:\n{raw_output}\nError: {error}")

# --- Tool Functions --- #

def summarize_expenses(_: str) -> str:
    logging.info("SummarizeExpenses tool called")
    if not expense_log:
        return "You haven't logged any expenses yet."
    summary = {}
    for entry in expense_log:
        cat = entry["category"]
        summary[cat] = summary.get(cat, 0) + entry["amount"]
    summary_lines = [f"{cat.capitalize()}: R{amount:.2f}" for cat, amount in summary.items()]
    return "Here's your spending summary by category:\n" + "\n".join(summary_lines)

def generate_report(_: str) -> str:
    logging.info("GenerateReport tool called")
    if not expense_log:
        return "No expenses available to generate a report."
    sorted_expenses = sorted(expense_log, key=lambda x: x['date'])
    report_lines = [f"{e['date']} - R{e['amount']:.2f} ({e['category']})" for e in sorted_expenses]
    total = sum(e['amount'] for e in sorted_expenses)
    return "Expense Report:\n" + "\n".join(report_lines) + f"\n\nTotal: R{total:.2f}"

# --- Tool Wrappers --- #
summarize_expenses_tool = Tool(
    name="SummarizeExpenses",
    func=summarize_expenses,
    description="Summarizes expenses grouped by category."
)

generate_report_tool = Tool(
    name="GenerateReport",
    func=generate_report,
    description="Generates a chronological report of all logged expenses."
)

# Exportable list of tools (LogExpense is now LLM-driven and handled in the main pipeline)
expense_tools = [
    summarize_expenses_tool,
    generate_report_tool
]  # LogExpense removed — handled via LLM parsing pipeline
