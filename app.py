import streamlit as st
import pandas as pd

st.set_page_config(page_title="Marketing Spend Estimator", layout="centered")
st.title("📊 Marketing Spend Estimator")

uploaded_file = st.file_uploader("Upload your Google Ads keyword CSV", type=["csv"])

if uploaded_file:
    try:
        # Google Ads export: header is always row 3, so we skip first 2 rows
        df = pd.read_csv(uploaded_file, skiprows=2)
    except Exception as e:
        st.error(f"❌ Failed to read CSV: {e}")
        st.stop()

    # Rename 'Search term' to 'Keyword'
    if 'Search term' in df.columns:
        df.rename(columns={'Search term': 'Keyword'}, inplace=True)

    # Check for required columns
    if 'Keyword' not in df.columns or 'Avg. CPC' not in df.columns:
        st.error("❌ Your file must include 'Search term' and 'Avg. CPC' columns.")
        st.stop()

    st.success("✅ File loaded successfully!")

    st.subheader("🔧 Set Your Assumptions")
    budget = st.number_input("Total budget ($)", min_value=0.0, value=500.0, step=10.0)
    conv_rate = st.number_input("Conversion rate (%)", min_value=0.1, value=2.0, step=0.1) / 100
    product_price = st.number_input("Product price (optional)", min_value=0.0, value=0.0)

    try:
        df = df[['Keyword', 'Avg. CPC']].dropna()
        df['Avg. CPC'] = pd.to_numeric(df['Avg. CPC'], errors='coerce')
        df.dropna(subset=['Avg. CPC'], inplace=True)

        df['Clicks (est.)'] = budget / df['Avg. CPC']
        df['Conversions (est.)'] = df['Clicks (est.)'] * conv_rate
        df['Est. CPA'] = budget / df['Conversions (est.)']

        if product_price > 0:
            df['Est. Revenue'] = df['Conversions (est.)'] * product_price
            df['Est. ROAS'] = df['Est. Revenue'] / budget
        else:
            df['Est. Revenue'] = None
            df['Est. ROAS'] = None

        st.subheader("📈 Estimated Results")
        st.dataframe(df[['Keyword', 'Avg. CPC', 'Clicks (est.)', 'Conversions (est.)', 'Est. CPA', 'Est. Revenue', 'Est. ROAS']])

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

