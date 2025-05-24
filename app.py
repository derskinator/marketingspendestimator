import streamlit as st
import pandas as pd
import chardet

st.set_page_config(page_title="Marketing Spend Estimator", layout="centered")
st.title("📊 Keyword Planner Spend Estimator")

uploaded_file = st.file_uploader("Upload your Google Keyword Planner TSV file", type=["csv", "tsv"])

if uploaded_file:
    # Detect encoding
    raw_data = uploaded_file.read()
    detected = chardet.detect(raw_data)
    encoding = detected['encoding'] or 'utf-8'
    uploaded_file.seek(0)

    try:
        # Keyword Planner exports are tab-delimited
        df = pd.read_csv(uploaded_file, skiprows=2, sep="\t", encoding=encoding, encoding_errors="ignore")
    except Exception as e:
        st.error(f"❌ Failed to read file: {e}")
        st.stop()

    # Normalize column names
    df.columns = [col.strip().replace('\ufeff', '').lower() for col in df.columns]

    # Rename and map
    if 'top of page bid (low range)' in df.columns:
        df.rename(columns={'top of page bid (low range)': 'avg_cpc'}, inplace=True)
    if 'keyword' not in df.columns or 'avg_cpc' not in df.columns:
        st.error("❌ This file must include 'keyword' and 'top of page bid (low range)' columns.")
        st.write("Detected columns:", list(df.columns))
        st.stop()

    st.success("✅ Keyword Planner file loaded successfully!")

    st.subheader("🔧 Set Your Assumptions")
    budget = st.number_input("Total budget ($)", min_value=0.0, value=500.0, step=10.0)
    conv_rate = st.number_input("Conversion rate (%)", min_value=0.1, value=2.0, step=0.1) / 100
    product_price = st.number_input("Product price (optional)", min_value=0.0, value=0.0)

    try:
        df = df[['keyword', 'avg_cpc']].dropna()
        df['avg_cpc'] = pd.to_numeric(df['avg_cpc'], errors='coerce')
        df = df.dropna(subset=['avg_cpc'])

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
        - **Clicks** = Budget ÷ Avg CPC  
        - **Conversions** = Clicks × Conversion Rate  
        - **CPA** = Budget ÷ Conversions  
        - **Revenue** = Conversions × Product Price  
        - **ROAS** = Revenue ÷ Budget
        """)
    except Exception as e:
        st.error(f"⚠️ Error during calculations: {e}")
else:
    st.info("📄 Upload your Google Keyword Planner export to begin.")

