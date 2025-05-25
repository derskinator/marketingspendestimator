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

    df.rename(columns={
        'top of page bid (low range)': 'low_cpc',
        'top of page bid (high range)': 'high_cpc',
        'competition (indexed value)': 'competition_index'
    }, inplace=True)

    # Ensure all required columns
    search_cols = [f'searches: {m} 2025' for m in MONTH_LABELS]
    required_cols = ['keyword', 'low_cpc', 'high_cpc', 'competition_index'] + search_cols

    if not all(col in df.columns for col in required_cols):
        st.error("Missing columns. Ensure export includes keyword, CPCs, competition, and 2025 monthly searches.")
        st.write("Found columns:", list(df.columns))
        st.stop()

    # Inputs
    st.sidebar.header("🔧 Inputs")
    budget = st.sidebar.number_input("Total budget ($)", value=500.0, min_value=0.0)
    base_cvr = st.sidebar.number_input("Base conversion rate (%)", value=2.0, min_value=0.1, max_value=100.0) / 100
    product_price = st.sidebar.number_input("Product price ($)", value=100.0, min_value=0.0)
    cpc_scale = st.sidebar.slider("CPC sensitivity", 0.0, 1.0, 0.5)
    cvr_scale = st.sidebar.slider("CVR sensitivity", 0.0, 1.0, 0.3)

    # Month selectors
    selected_month = st.sidebar.selectbox("Simulate a single month", MONTH_LABELS)
    selected_multi = st.sidebar.multiselect("Compare multiple months", MONTH_LABELS, default=["May", "Nov", "Dec"])

    # Prepare data
    df = df[['keyword', 'low_cpc', 'high_cpc', 'competition_index'] + search_cols].dropna()
    df['low_cpc'] = pd.to_numeric(df['low_cpc'], errors='coerce')
    df['high_cpc'] = pd.to_numeric(df['high_cpc'], errors='coerce')
    df['competition_index'] = pd.to_numeric(df['competition_index'], errors='coerce')
    for col in search_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(inplace=True)

    df['competition_score'] = df['competition_index'] / 100
    df['base_weighted_cpc'] = df['low_cpc'] * (1 - df['competition_score']) + df['high_cpc'] * df['competition_score']

    # Normalize volumes
    monthly_cols = [f'searches: {m} 2025' for m in MONTH_LABELS]
    df['peak_volume'] = df[monthly_cols].max(axis=1)
    for month in MONTHS:
        col = f'searches: {month.capitalize()} 2025'
        df[f'norm_{month}'] = df[col] / df['peak_volume']

    # Optional boost for Nov/Dec (holiday traffic)
    for holiday_month in ['nov', 'dec']:
        df[f'norm_{holiday_month}'] *= 1.2  # 20% bonus

    # Calculate monthly projections
    monthly_results = []
    for month in MONTHS:
        norm = df[f'norm_{month}']
        adj_cpc = df['base_weighted_cpc'] * (1 + (norm - 1) * cpc_scale)
        adj_cvr = base_cvr * (1 + (norm - 1) * cvr_scale)

        avg_cpc = adj_cpc.mean()
        avg_cvr = adj_cvr.mean()
        clicks = budget / avg_cpc
        conversions = clicks * avg_cvr
        revenue = conversions * product_price
        cpa = budget / conversions if conversions > 0 else None
        roas = revenue / budget if budget > 0 else None

        monthly_results.append({
            'Month': month.capitalize(),
            'Avg CPC': round(avg_cpc, 2),
            'Avg CVR (%)': round(avg_cvr * 100, 2),
            'Estimated Clicks': round(clicks),
            'Estimated Conversions': round(conversions, 2),
            'Estimated CPA': round(cpa, 2) if cpa else None,
            'Estimated Revenue': round(revenue, 2),
            'Estimated ROAS': round(roas, 2)
        })

    result_df = pd.DataFrame(monthly_results).set_index('Month')

    # Display single-month view
    if selected_month:
        st.subheader(f"📅 {selected_month} Simulation")
        row = result_df.loc[selected_month]
        for label, value in row.items():
            st.metric(label, f"{value:,}" if isinstance(value, (int, float)) else value)

    # Multi-month table
    if selected_multi:
        st.subheader("📊 Selected Months Comparison")
        st.dataframe(result_df.loc[selected_multi])

    # Line chart of year
    st.subheader("📈 Year-Long Projection")
    st.line_chart(result_df[['Estimated Clicks', 'Estimated Conversions', 'Estimated Revenue', 'Estimated ROAS']])

else:
    st.info("📄 Upload your Keyword Planner TSV export to begin.")



