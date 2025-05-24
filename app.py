import streamlit as st
import pandas as pd

st.set_page_config(page_title="Marketing Spend Estimator", layout="centered")
st.title("📊 Marketing Spend Estimator")

uploaded_file = st.file_uploader("Upload your Google Ads keyword CSV", type=["csv"])

if uploaded_file:
    try:
        # Skip metadata rows and load the real data
        df = pd.read_csv(uploaded_file, skiprows=2, encoding="utf-8", encoding_errors="ignore")
    except Exception as e:
        st.error("❌ Could not read CSV. Ensure it's a valid Google Ads keyword export.")
        st.stop()

    # Validate required columns
    required_cols = ['Keyword', 'Avg. CPC']
    if not all(col in df.columns for col in required_cols):
        st.error(f"❌ Your CSV must include the following columns: {', '.join(required_cols)}")
    else:
        st.success("✅ CSV uploaded successfully!")

        # Inputs
        st.subheader("🔧 Set Your Assumptions")
        budget = st.number_input("Total budget ($)", min_value=0.0, value=500.0, step=10.0)
        conv_rate = st.number_input("Assumed conversion rate (%)", min_value=0.1, max_value=100.0, value=2.0, step=0.1) / 100
        product_price = st.number_input("Product price (optional)", min_value=0.0, value=0.0, step=1.0)

        # Calculations
        try:
            df['Clicks (est.)'] = budget / df['Avg. CPC']
            df['Conversions (est.)'] = df['Clicks (est.)'] * conv_rate
            df['Est. CPA'] = budget / df['Conversions (est.)']

            if product_price > 0:
                df['Est. Revenue'] = df['Conversions (est.)'] * product_price
                df['Est. ROAS'] = df['Est. Revenue'] / budget
            else:
                df['Est. Revenue'] = None
                df['Est. ROAS'] = None

            st.subheader("📈 Results")
            st.dataframe(df[['Keyword', 'Avg. CPC', 'Clicks (est.)', 'Conversions (est.)', 'Est. CPA', 'Est. Revenue', 'Est. ROAS']])

            st.markdown("---")
            st.subheader("🧠 Calculation Summary")
            st.markdown("""
            - **Clicks** = Budget ÷ Avg. CPC  
            - **Conversions** = Clicks × Conversion Rate  
            - **CPA** = Budget ÷ Conversions  
            - **Revenue** = Conversions × Product Price (optional)  
            - **ROAS** = Revenue ÷ Budget (optional)
            """)

        except Exception:
            st.error("⚠️ Error during calculation. Check that 'Avg. CPC' values are numeric.")
else:
    st.info("📄 Upload a Google Ads keyword CSV to begin.")

