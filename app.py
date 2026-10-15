from pathlib import Path
import pandas as pd
import streamlit as st

from analysis import prepare_data, overall_kpis, segment_summary, geography_risk

st.set_page_config(page_title="European Banking Churn Explorer", page_icon="🏦", layout="wide")
st.markdown("<style>.block-container{padding-top:1.5rem}.metric-card{border-radius:12px}</style>", unsafe_allow_html=True)
st.title("Customer Segmentation & Churn Pattern Analytics")
st.caption("European Banking | Use the synthetic demo or upload the project CSV")

uploaded = st.sidebar.file_uploader("Upload churn CSV", type=["csv"])
demo_path = Path(__file__).parent / "data" / "demo_bank_churn_synthetic.csv"
provided_path = Path(__file__).parent / "data" / "European_Bank.csv"
if uploaded is not None:
    try:
        raw = pd.read_csv(uploaded)
        data_label = "Uploaded dataset"
    except Exception as exc:
        st.error(f"Could not read CSV: {exc}"); st.stop()
else:
    if provided_path.exists():
        raw = pd.read_csv(provided_path)
        data_label = "User-provided dataset"
    elif demo_path.exists():
        raw = pd.read_csv(demo_path)
        data_label = "Synthetic demonstration data"
    else:
        st.warning("No data file found. Upload a CSV in the sidebar or run `python generate_demo_data.py`."); st.stop()

try:
    df = prepare_data(raw)
except Exception as exc:
    st.error(f"Dataset validation failed: {exc}")
    st.info("Expected columns include CreditScore, Geography, Gender, Age, Tenure, Balance, NumOfProducts, HasCrCard, IsActiveMember, EstimatedSalary and Exited.")
    st.stop()

if data_label.startswith("Synthetic"):
    st.warning("Demo data is synthetic and only tests the dashboard. Replace it with the source CSV before reporting project findings.")
else:
    st.success(f"Loaded {len(df):,} valid customer rows from {data_label.lower()}.")

st.sidebar.header("Filters")
def multi_filter(label, col):
    choices = sorted(df[col].dropna().astype(str).unique().tolist())
    return st.sidebar.multiselect(label, choices, default=choices)

geo = multi_filter("Geography", "Geography")
age_groups = multi_filter("Age group", "AgeGroup")
tenure_groups = multi_filter("Tenure group", "TenureGroup")
status = st.sidebar.multiselect("Customer status", ["Retained", "Churned"], default=["Retained", "Churned"])
positive_balances = df.loc[df["Balance"] > 0, "Balance"]
high_balance_cut = float(positive_balances.quantile(.75)) if not positive_balances.empty else float("inf")
high_balance_only = st.sidebar.checkbox("Higher-balance customers (top quartile)", value=False)
view = df[df["Geography"].astype(str).isin(geo) & df["AgeGroup"].astype(str).isin(age_groups)
          & df["TenureGroup"].astype(str).isin(tenure_groups) & df["CustomerStatus"].isin(status)]
if high_balance_only:
    view = view[view["Balance"] >= high_balance_cut]
if view.empty:
    st.warning("No customers match these filters."); st.stop()

k = overall_kpis(view)
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Customers", f"{k['customers']:,}")
c2.metric("Churn rate", f"{k['churn_rate']:.1%}")
c3.metric("Churned customers", f"{k['churners']:,}")
c4.metric("High balance churn", f"{k['high_balance_churn_rate']:.1%}")
c5.metric("Churned balance exposure", f"€{k['balance_exposure']:,.0f}")
st.caption("Balance exposure is the sum of recorded balances among churned customers. It is not lost revenue or profit.")

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Segments", "Geography & demographics", "Customer explorer"])
with tab1:
    left,right = st.columns(2)
    status_counts = view["CustomerStatus"].value_counts().reindex(["Retained", "Churned"], fill_value=0)
    left.subheader("Retained vs churned")
    left.bar_chart(status_counts, color="#3767e8")
    age_stats = segment_summary(view, "AgeGroup")
    right.subheader("Churn rate by age")
    right.bar_chart(age_stats.set_index("AgeGroup")["ChurnRate"], color="#ef7d42")
    st.subheader("Engagement and product profile")
    a,b = st.columns(2)
    a.bar_chart(segment_summary(view, "IsActiveMember").set_index("IsActiveMember")["ChurnRate"], color="#7e57c2")
    b.bar_chart(segment_summary(view, "NumOfProducts").set_index("NumOfProducts")["ChurnRate"], color="#14a38b")
with tab2:
    dimension = st.selectbox("Choose a segment", ["AgeGroup", "TenureGroup", "CreditScoreBand", "BalanceSegment", "NumOfProducts", "Gender", "IsActiveMember", "HasCrCard"])
    summary = segment_summary(view, dimension)
    st.bar_chart(summary.set_index(dimension)["ChurnRate"], color="#ef7d42")
    st.dataframe(summary.style.format({"ChurnRate":"{:.1%}","ChurnShare":"{:.1%}","MeanBalance":"€{:,.0f}","ChurnedBalance":"€{:,.0f}"}), use_container_width=True, hide_index=True)
with tab3:
    g = geography_risk(view)
    left,right = st.columns(2)
    left.subheader("Geography churn rate")
    left.bar_chart(g.set_index("Geography")["ChurnRate"], color="#ef7d42")
    right.subheader("Risk index (overall = 1.0)")
    right.bar_chart(g.set_index("Geography")["GeographicRiskIndex"], color="#3767e8")
    st.dataframe(g[["Geography","Customers","Churners","ChurnRate","ChurnShare","GeographicRiskIndex","ChurnedBalance"]].style.format({"ChurnRate":"{:.1%}","ChurnShare":"{:.1%}","GeographicRiskIndex":"{:.2f}x","ChurnedBalance":"€{:,.0f}"}), use_container_width=True, hide_index=True)
with tab4:
    st.caption("Identifiers and surname are excluded from analytical filters. Use customer rows only for internal review; do not infer causation from this snapshot.")
    options = [c for c in ["CustomerId","Geography","Gender","Age","AgeGroup","CreditScore","CreditScoreBand","Tenure","TenureGroup","Balance","BalanceSegment","NumOfProducts","IsActiveMember","Exited"] if c in view]
    st.dataframe(view[options], use_container_width=True, hide_index=True, height=450)
    st.download_button("Download filtered customer data", view[options].to_csv(index=False).encode(), "filtered_churn_customers.csv", "text/csv")

with st.expander("Definitions and data quality"):
    st.markdown("""
    - **Churn rate:** customers with `Exited = 1` divided by customers in the current view.
    - **High-balance churn:** churn rate for customers at or above the 75th percentile of positive balances in the current view.
    - **Geographic risk index:** geography churn rate divided by overall churn rate; 1.0 means equal to the selected population.
    - **Engagement drop indicator:** inactive-member churn rate divided by active-member churn rate.
    - Age groups: under 30, 30–45, 46–60, and 61+ (age 60 stays in 46–60 to avoid overlap). Tenure groups: 0–2, 3–6, 7–10 years.
    - The source dataset is cross-sectional. “Churn pattern” means differences associated with recorded fields, not a causal explanation or future churn prediction.
    """)
st.caption("Project prepared by Sourav Kumar")
