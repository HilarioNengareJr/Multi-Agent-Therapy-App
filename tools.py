import logging
from langchain.tools import Tool
from datetime import datetime
from typing import List, Dict
import re

# Setup logging
logging.basicConfig(level=logging.INFO)

# In-memory storage for simplicity (replace with DB later)
expense_log: List[Dict] = []

# --- Tool Functions --- #

def log_expense(input: str) -> str:
    logging.info(f"LogExpense tool called with input: {input}")
    try:
        # Use regex to extract amount, category, and date from user input
        amount_match = re.search(r"(?:R|r)(\d+(?:\.\d{1,2})?)", input)
        category_match = re.search(r"(?i)(groceries|food|transport|bills|entertainment|shopping|fuel|rent|misc)\b", input)
        date_match = re.search(r"(?i)on\s+([A-Za-z]+\s+\d{1,2})", input)

        if not amount_match:
            raise ValueError("Amount not found")
        if not category_match:
            category = "misc"
        else:
            category = category_match.group(1).lower()

        amount = float(amount_match.group(1))

        if date_match:
            date_obj = datetime.strptime(date_match.group(1), "%B %d")
            date = date_obj.strftime("%Y-%m-%d")
        else:
            date = datetime.today().strftime("%Y-%m-%d")

        expense = {
            "date": date,
            "amount": amount,
            "category": category,
            "description": input
        }
        expense_log.append(expense)
        return f"✅ Logged: R{amount} for {category} on {date}"
    except Exception as e:
        logging.error(f"Failed to log expense: {e}")
        return "❌ Sorry, I couldn't log that expense. Please make sure to include an amount (e.g. R100), a category (e.g. groceries), and optionally a date (e.g. on July 10)."

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
log_expense_tool = Tool(
    name="LogExpense",
    func=log_expense,
    description="Logs a user expense by extracting date, amount, and category from the input."
)

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

# Exportable list of tools
expense_tools = [
    log_expense_tool,
    summarize_expenses_tool,
    generate_report_tool
]
