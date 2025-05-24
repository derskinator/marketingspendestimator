import streamlit as st
import pandas as pd

st.set_page_config(page_title="Marketing Spend Estimator", layout="centered")
st.title("📊 Marketing Spend Estimator (No API)")

# Upload keyword CSV
uploaded_file = st.file_uploader("Upload your Google Ads keyword CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if 'Avg. CPC' not in df.columns:
        st.error("CSV must include a column named 'Avg. CPC'")
    else:
        # Input: Budget and Assumptions
        budget = st.number_input("Enter your total budget ($)", min_value=0.0, value=500.0, step=10.0)
        conv_rate = st.number_input("Assumed conversion rate (%)", min_value=0.1, value=2.0, step=0.1) / 100
        product_price = st.number_input("Product price (optional, for revenue)", min_value=0.0, value=0.0, step=1.0)

        # Calculate estimates
        df['Clicks'] = budget / df['Avg. CPC']
        df['Conversions'] = df['Clicks'] * conv_rate
        df['CPA'] = budget / df['Conversions']

        if product_price > 0:
            df['Revenue'] = df['Conversions'] * product_price
            df['ROAS'] = df['Revenue'] / budget
        else:
            df['Revenue'] = None
            df['ROAS'] = None

        # Show results
        st.subheader("📈 Results")
        st.dataframe(df[['Keyword', 'Avg. CPC', 'Clicks', 'Conversions', 'CPA', 'Revenue', 'ROAS']])

        # Show transparent formulas
        st.markdown("---")
        st.subheader("🧠 How It's Calculated")
        st.markdown("""
        - **Clicks** = Budget ÷ Avg. CPC  
        - **Conversions** = Clicks × Conversion Rate  
        - **CPA** = Budget ÷ Conversions  
        - **Revenue** = Conversions × Product Price (optional)  
        - **ROAS** = Revenue ÷ Budget (optional)
        """)
else:
    st.info("Upload a CSV to get started.")


