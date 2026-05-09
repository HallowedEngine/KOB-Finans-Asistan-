# KOBI Finans Asistani

KOBI Finans Asistani is a Streamlit app for small business owners in Turkey. It helps users read expense documents, categorize costs, track recurring payments, and ask basic accounting questions through an AI-assisted interface.

## Product Focus

The project is designed around a common small-business workflow: collect invoices and receipts, turn them into structured expense records, understand monthly spending patterns, and get plain-language guidance before speaking with an accountant.

## Core Features

- Document reader for invoices, receipts, bank slips, and expense documents
- GPT-4o Vision-assisted OCR and structured field extraction
- Manual expense entry and searchable expense history
- Automatic expense category suggestions
- Budget and recurring expense pages
- Category, trend, and period-comparison reports
- Turkish accounting knowledge base for question-answer support
- Excel export for offline review or accountant handoff

## Tech Stack

- Python, Streamlit
- OpenAI GPT-4o
- SQLite
- Pandas, Plotly
- Pillow, python-dotenv

## Getting Started

```bash
git clone https://github.com/HallowedEngine/KOB-Finans-Asistan-.git
cd KOB-Finans-Asistan-
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

Run the app:

```bash
streamlit run app.py
```

## Project Structure

```text
app.py                 Main Streamlit entry point
pages/                 Feature pages
  1_belge_okuyucu.py   Document OCR workflow
  2_giderlerim.py      Expense list and filtering
  3_raporlar.py        Reporting dashboard
  4_soru_cevap.py      Accounting Q&A assistant
  5_butce.py           Budget tracking
  6_tekrar_giderler.py Recurring expenses
utils/                 OCR, categorization, database, and export helpers
config.py              Application settings
requirements.txt       Python dependencies
```

## Portfolio Notes

This repository demonstrates a practical AI workflow for a local market: document understanding, structured extraction, expense analytics, and a simple business-facing interface. The next production steps would be user accounts, stronger validation for extracted document fields, audit logs, and accountant-approved knowledge sources.

## Disclaimer

This app is for educational and informational use. It is not a replacement for professional accounting, tax, or legal advice.
