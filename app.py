import streamlit as st
import pandas as pd
import chardet

st.set_page_config(page_title="Marketing Spend Estimator", layout="centered")
st.title("📊 Marketing Spend Estimator")

uploaded_file = st.file_uploader("Upload your Google Ads keyword CSV", type=["csv"])

if uploaded_file:
    # Read raw bytes and detect encoding
    raw_data = uploaded_file.read()
    detected = chardet.detect(raw_data)
    encoding = detected['encoding'] or 'utf-8'

    uploaded_file.seek(0)

    try:
        # Skip metadata rows, load CSV
        df = pd.read_csv(uploaded_file, skiprows=2, encoding=encoding, encoding_errors="ignore")
    except Exception as e:
        st.error(f"❌ Failed to read CSV: {e}")
        st.stop()

    # 🧼 Normalize column names
    df.columns = [col.strip().replace('\ufeff', '').lower() for col in df.columns]

    # 🪄 Rename 'search term' → 'keyword'
    if 'search term' in df.columns:
        df.rename(columns={'search term': 'keyword'}, inplace=True)
    if 'avg. cpc' in df.columns:
        df.rename(columns={'avg. cpc': 'avg_cpc'}, inplace=True)

    # ❌ Check if required columns exist
    if 'keyword' not in df.columns or 'avg_cpc' not in df.columns:
        st.error("❌ Your file must include a 'Search term' and 'Avg. CPC' column (case insensitive).")
        st.write("Detected columns:", list(df.columns))
        st.stop()

    st.success("✅ File loaded successfully!")

    st.subheader("🔧 Set Your Assumptions")
    budget = st.number_input("Total budget ($)", min_value=0.0, value=500.0, step=10.0)
    conv_rate = st.number_input("Conversion rate (%)", min_value=0.1, value=2.0, step=0.1) / 100
    product_price = st.number_input("Product price (optional)", min_value=0.0, value=0.0)

    try:
        df = df[['keyword', 'avg_cpc']].dropna()
        df['avg_cpc'] = pd.to_numeric(df['avg_cpc'], errors='coerce')
        df.dropna(subset=['avg_cpc'], inplace=True)

        df['Clicks (est.)'] = budget / df['avg_cpc']
        df['Conversions (est.)'] = df['Clicks (est.)'] * conv_rate
        df['Est. CPA'] = budget / df['Conversions (est.)']

        if product_price > 0:
            df['Est. Revenue'] = df['Conversions (est.)'] * product_price
            df['Est. ROAS'] = df['Est. Revenue'] / budget
        else:
            df['Est. Revenue'] = None
            df['Est. ROAS'] = None

        st.subheader("📈 Estimated Results")
        st.dataframe(df[['keyword', 'avg_cpc', 'Clicks (est.)', 'Conversions (est.)', 'Est. CPA', 'Est. Revenue', 'Est. ROAS']])

        st.markdown("---")
        st.subheader("🧠 Formulas Used")
        st.markdown("""
        - **Clicks** = Budget ÷ Avg. CPC  
        - **Conversions** = Clicks × Conversion Rate  
        - **CPA** = Budget ÷ Conversions  
        - **Revenue** = Conversions × Product Price  
        - **ROAS** = Revenue ÷ Budget
        """)
    except Exception as e:
        st.error(f"⚠️ Error during calculations: {e}")
else:
    st.info("📄 Upload your exported Google Ads keyword CSV to begin.")
