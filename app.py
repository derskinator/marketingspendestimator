import streamlit as st
import pandas as pd
import chardet

st.set_page_config(page_title="Marketing Spend Estimator", layout="centered")
st.title("📊 Marketing Spend Estimator (Averaged Across Keywords)")

uploaded_file = st.file_uploader("Upload your Google Keyword Planner TSV file", type=["csv", "tsv"])

if uploaded_file:
    # Detect encoding
    raw_data = uploaded_file.read()
    detected = chardet.detect(raw_data)
    encoding = detected['encoding'] or 'utf-8'
    uploaded_file.seek(0)

    try:
        # Read as TSV, skip header junk
        df = pd.read_csv(uploaded_file, skiprows=2, sep="\t", encoding=encoding, encoding_errors="ignore")
    except Exception as e:
        st.error(f"❌ Failed to read file: {e}")
        st.stop()

    # Normalize column names
    df.columns = [col.strip().replace('\ufeff', '').lower() for col in df.columns]

    # Rename required columns
    df.rename(columns={
        'top of page bid (low range)': 'low_cpc',
        'top of page bid (high range)': 'high_cpc',
        'competition (indexed value)': 'competition_index'
    }, inplace=True)

    # Check required columns
    required = ['keyword', 'low_cpc', 'high_cpc', 'competition_index']
    if not all(col in df.columns for col in required):
        st.error("❌ File must include: 'keyword', 'top of page bid (low range)', 'top of page bid (high range)', and 'competition (indexed value)'")
        st.write("Detected columns:", list(df.columns))
        st.stop()

    st.success("✅ File loaded and formatted!")

    # Inputs
    st.subheader("🔧 Set Your Assumptions")
    budget = st.number_input("Total budget ($)", min_value=0.0, value=500.0, step=10.0)
    conv_rate = st.number_input("Conversion rate (%)", min_value=0.1, value=2.0, step=0.1) / 100
    product_price = st.number_input("Product price ($)", min_value=0.0, value=100.0, step=1.0)

    try:
        # Clean and convert
        df = df[['keyword', 'low_cpc', 'high_cpc', 'competition_index']].dropna()
        df['low_cpc'] = pd.to_numeric(df['low_cpc'], errors='coerce')
        df['high_cpc'] = pd.to_numeric(df['high_cpc'], errors='coerce')
        df['competition_index'] = pd.to_numeric(df['competition_index'], errors='coerce')
        df.dropna(inplace=True)

        # Normalize competition index
        df['competition_score'] = df['competition_index'] / 100.0

        # Weighted CPC formula
        df['weighted_cpc'] = df['low_cpc'] * (1 - df['competition_score']) + df['high_cpc'] * df['competition_score']

        # Split budget equally across keywords
        keyword_count = len(df)
        df['budget_per_keyword'] = budget / keyword_count

        # Per-keyword calculations
        df['clicks'] = df['budget_per_keyword'] / df['weighted_cpc']
        df['conversions'] = df['clicks'] * conv_rate
        df['cpa'] = df['budget_per_keyword'] / df['conversions']
        df['revenue'] = df['conversions'] * product_price
        df['roas'] = df['revenue'] / df['budget_per_keyword']

        # Averages across all keywords
        avg_weighted_cpc = df['weighted_cpc'].mean()
        avg_clicks = df['clicks'].mean()
        avg_conversions = df['conversions'].mean()
        avg_cpa = df['cpa'].mean()
        avg_revenue = df['revenue'].mean()
        avg_roas = df['roas'].mean()

        st.subheader("📊 Averaged Estimates (Per Keyword)")
        st.metric("Avg Weighted CPC", f"${avg_weighted_cpc:.2f}")
        st.metric("Avg Clicks", f"{avg_clicks:,.0f}")
        st.metric("Avg Conversions", f"{avg_conversions:.2f}")
        st.metric("Avg CPA", f"${avg_cpa:.2f}")
        st.metric("Avg Revenue", f"${avg_revenue:.2f}")
        st.metric("Avg ROAS", f"{avg_roas:.2f}x")

        st.markdown("---")
        st.subheader("🧠 Formula Summary")
        st.markdown("""
        - **Competition Score** = Competition (indexed value) ÷ 100  
        - **Weighted CPC** = Low CPC × (1 - Score) + High CPC × Score  
        - **Clicks** = Budget per keyword ÷ Weighted CPC  
        - **Conversions** = Clicks × Conversion Rate  
        - **CPA** = Budget per keyword ÷ Conversions  
        - **Revenue** = Conversions × Product Price  
        - **ROAS** = Revenue ÷ Budget per keyword
        """)

    except Exception as e:
        st.error(f"⚠️ Error during calculations: {e}")

else:
    st.info("📄 Upload your Google Keyword Planner TSV to begin.")

