# Shadow AI Discovery & Risk Intake — Demo

Governance-first demo dashboard to illustrate metadata-first Shadow AI discovery, risk triage, and an intake workflow for portfolio organizations.

Disclaimer: Demo uses simulated telemetry; metadata-first; no prompt/content inspection; privacy-aware.

Features
- Filters: Risk level, Department, Category
- Executive-friendly metrics: total tools detected, high-risk count (Critical + High), users affected, average risk score
- Visuals: risk distribution, department heatmap, discovery timeline
- High-risk table with recommended action and a detailed tool view
- Export: full report CSV, high-risk CSV, executive summary TXT

Data
The app loads CSVs from a local `data/` folder if present. Expected schema columns if using CSVs:

- `tool_name`, `domain`, `category`, `dept`, `user_count`, `usage_count`, `first_detected`, `last_seen`, `data_type`, `vendor_tier`, `risk_score`, `risk_level`

If CSVs are missing, the app generates a realistic demo dataset in-code so the app still runs.

Risk logic
- If `risk_score` is missing, it is computed using a simple rubric combining `data_type`, `vendor_tier`, `usage_count`, and inferred `controls_present`.
- Mapping:
  - 70–100: Critical
  - 50–69: High
  - 30–49: Medium
  - 0–29: Low

Run

Install dependencies and run the app:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Notes
- All discovery language in the UI is governance-first (enablement, policy-aligned).
- The demo explicitly does not inspect prompts or content; it uses metadata/telemetry only.

Footer
Built by Adarian Dewberry
