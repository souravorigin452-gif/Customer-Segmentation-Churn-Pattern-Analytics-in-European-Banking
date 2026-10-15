# Customer Segmentation & Churn Pattern Analytics

**Project by Sourav Kumar**

A Streamlit dashboard for exploring customer churn patterns, customer segments, and geography-level risk in a European banking dataset.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

The dashboard opens with a clearly labeled synthetic demonstration dataset. To analyze the project dataset, use **Upload churn CSV** in the sidebar. The CSV needs fields such as `CreditScore`, `Geography`, `Gender`, `Age`, `Tenure`, `Balance`, `NumOfProducts`, `HasCrCard`, `IsActiveMember`, `EstimatedSalary`, and `Exited`.

## Deploy on Streamlit Community Cloud

1. Open [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
2. Choose **Create app** and select this repository on branch `main`.
3. Set **Main file path** to `app.py`, then deploy.

The supplied CSV is not included in this public repository. Upload it through the dashboard after deployment if you have permission to use it there. The demo data is synthetic and should not be used as a source for project findings.

## Dashboard

- Overview of customer count and churn KPIs
- Churn comparisons by age, activity, product count, and geography
- Segment-level summaries and a customer explorer
- Filters for geography, age, tenure, customer status, and balance

## Files

- `app.py` — Streamlit interface
- `analysis.py` — validation, segmentation, and KPI calculations
- `requirements.txt` — Python dependencies
- `data/demo_bank_churn_synthetic.csv` — synthetic sample for a safe online preview
- `generate_demo_data.py` — script to create synthetic sample data
