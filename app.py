import streamlit as st
import pandas as pd
import chardet

st.set_page_config(page_title="Seasonal Spend Estimator", layout="wide")
st.title("📊 Seasonal Marketing Spend Estimator")

uploaded_file = st.file_uploader("Upload your Google Keyword Planner TSV", type=["csv", "tsv"])

MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
MONTH_LABELS = [m.capitalize() for m in MONTHS]

if uploaded_file:
    raw = uploaded_file.read()
    encoding = chardet.detect(raw)['encoding']
    uploaded_file.seek(0)
    df = pd.read_csv(uploaded_file, skiprows=2, sep="\t", encoding=encoding, encoding_errors="ignore")

    # Normalize column names
    df.columns = [col.strip().replace('\ufeff', '').lower() for col in df.columns]

    # Dynamically map monthly search columns
    monthly_map = {}
    for month in MONTHS:
        for col in df.columns:
            if f"searches: {month}" in col:
                monthly_map[month] = col
                break

    required_core = ['keyword', 'top of page bid (low range)', 'top of page bid (high range)', 'competition (indexed value)']
    if not all(col in df.columns for col in required_core) or len(monthly_map) < 12:
        st.error("❌ Missing required columns. Confirm export includes keyword, CPCs, competition index, and monthly search volume.")
        st.write("Detected columns:", list(df.columns))
        st.stop()

    # Inputs
    st.sidebar.header("🔧 Inputs")
    base_budget = st.sidebar.number_input("Total base monthly budget ($)", value=500.0, min_value=0.0)
    base_cvr = st.sidebar.number_input("Base conversion rate (%)", value=2.0, min_value=0.1, max_value=100.0) / 100
    product_price = st.sidebar.number_input("Product price ($)", value=100.0, min_value=0.0)
    cpc_power = st.sidebar.slider("CPC Power (sensitivity)", 0.0, 3.0, 1.5)
    cvr_power = st.sidebar.slider("CVR Power (sensitivity)", 0.0, 3.0, 1.3)
    spend_sensitivity = st.sidebar.slider("Spend Sensitivity (seasonal scaling)", 0.0, 2.0, 1.0, step=0.05)
    holiday_boost = st.sidebar.slider("Holiday Sensitivity (Nov/Dec)", 1.0, 2.0, 1.2, step=0.05)
    search_volume_sensitivity = st.sidebar.slider("Search Volume Sensitivity", 0.0, 2.0, 1.0, step=0.05)

    # Month selectors
    selected_month = st.sidebar.selectbox("Simulate a single month", MONTH_LABELS)
    selected_multi = st.sidebar.multiselect("Compare multiple months", MONTH_LABELS, default=MONTH_LABELS)

    # Rename and clean
    df.rename(columns={
        'top of page bid (low range)': 'low_cpc',
        'top of page bid (high range)': 'high_cpc',
        'competition (indexed value)': 'competition_index'
    }, inplace=True)

    all_month_cols = list(monthly_map.values())
    df = df[['keyword', 'low_cpc', 'high_cpc', 'competition_index'] + all_month_cols].dropna()
    df['low_cpc'] = pd.to_numeric(df['low_cpc'], errors='coerce')
    df['high_cpc'] = pd.to_numeric(df['high_cpc'], errors='coerce')
    df['competition_index'] = pd.to_numeric(df['competition_index'], errors='coerce')
    for col in all_month_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(inplace=True)

    df['competition_score'] = df['competition_index'] / 100
    df['base_weighted_cpc'] = df['low_cpc'] * (1 - df['competition_score']) + df['high_cpc'] * df['competition_score']

    # GLOBAL normalized volume across all keywords (based on mean)
    monthly_totals = df[all_month_cols].sum()
    for m in ['nov', 'dec']:
        monthly_totals[monthly_map[m]] *= holiday_boost  # dynamic holiday boost

    monthly_mean = monthly_totals.mean()
    raw_scalars = {
        month: monthly_totals[monthly_map[month]] / monthly_mean
        for month in MONTHS
    }

    # Apply volume sensitivity to create adjusted scalars
    monthly_scalars = {
        month: 1 + (raw_scalars[month] - 1) * search_volume_sensitivity
        for month in MONTHS
    }

    # Monthly simulations using adjusted scalars
    monthly_results = []
    for month in MONTHS:
        scalar = monthly_scalars[month]
        raw_volume = monthly_totals[monthly_map[month]]

        # Adjusted spend per month
        adjusted_budget = base_budget * (1 + (scalar - 1) * spend_sensitivity)

        # CPC scaling (flattened)
        adj_cpc = df['base_weighted_cpc'] * (1 + (scalar - 1) * cpc_power)
        adj_cpc = adj_cpc.clip(lower=0.01)  # ✅ prevent negative CPCs

        # CVR scaling (exponential)
        adj_cvr = base_cvr * (scalar ** cvr_power)

        avg_cpc = adj_cpc.mean()
        avg_cvr = adj_cvr.mean()
        clicks = adjusted_budget / avg_cpc if avg_cpc > 0 else 0
        conversions = clicks * avg_cvr
        revenue = conversions * product_price
        cpa = adjusted_budget / conversions if conversions > 0 else None
        roas = revenue / adjusted_budget if adjusted_budget > 0 else None

        monthly_results.append({
            'Month': month.capitalize(),
            'Search Volume': int(raw_volume),
            'Monthly Spend ($)': round(adjusted_budget, 2),
            'Avg CPC': round(avg_cpc, 2),
            'Avg CVR (%)': round(avg_cvr * 100, 2),
            'Estimated Clicks': round(clicks),
            'Estimated Conversions': round(conversions, 2),
            'Estimated CPA': round(cpa, 2) if cpa else None,
            'Estimated Revenue': round(revenue, 2),
            'Estimated ROAS': round(roas, 2) if roas else None
        })

    result_df = pd.DataFrame(monthly_results).set_index('Month')

    # Ensure correct calendar order
    result_df.index = pd.CategoricalIndex(result_df.index, categories=MONTH_LABELS, ordered=True)
    result_df.sort_index(inplace=True)

    # Single-month view
    if selected_month:
        st.subheader(f"📅 {selected_month} Simulation")
        row = result_df.loc[selected_month]
        for label, value in row.items():
            st.metric(label, f"{value:,}" if isinstance(value, (int, float)) else value)

    # Multi-month table in calendar order
    if selected_multi:
        st.subheader("📊 Selected Months Comparison")
        ordered_multi = [m for m in MONTH_LABELS if m in selected_multi]
        st.dataframe(result_df.loc[ordered_multi])

    # Chronologically ordered revenue chart
    st.subheader("📈 Projected Sales (Selected Months Only)")
    if selected_multi:
        ordered_multi = [m for m in MONTH_LABELS if m in selected_multi]
        chart_df = result_df.loc[ordered_multi].copy()
        chart_df.index = pd.CategoricalIndex(chart_df.index, categories=MONTH_LABELS, ordered=True)
        chart_df.sort_index(inplace=True)
        st.line_chart(chart_df[['Estimated Revenue']])

else:
    st.info("📄 Upload your Keyword Planner TSV export to begin.")
