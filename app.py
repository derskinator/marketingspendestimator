import streamlit as st
import pandas as pd

st.set_page_config(page_title="Marketing Spend Estimator", layout="centered")
st.title("📊 Marketing Spend Estimator")

uploaded_file = st.file_uploader("Upload your Google Ads keyword CSV", type=["csv"])

def find_header_row(file, required_columns):
    """Search for the row that contains all required columns."""
    file.seek(0)
    for i, line in enumerate(file):
        decoded = line.decode("utf-8", errors="ignore")
        if all(col in decoded for col in required_columns):
            return i
    return None

if uploaded_file:
    required_columns = ['Keyword', 'Avg. CPC']
    header_row = find_header_row(uploaded_file, required_columns)

    if header_row is None:
        st.error(f"❌ Could not find a header row with: {', '.join(required_columns)}")
        st.stop()

    uploaded_file.seek(0)  # Reset file read position

    try:
        df = pd.read_csv(uploaded_file, skiprows=header_row)
    except Exception as e:
        st.error(f"❌ Failed to load CSV: {e}")
        st.stop()

    if not set(required_columns).issubset(df.columns):
        st.error(f"❌ Your CSV must include: {', '.join(required_columns)}")
    else:
        st.success("✅ CSV loaded successfully!")

        # Inputs
        st.subheader("🔧 Set Your Assumptions")
        budget = st.number_input("Total budget ($)", min_value=0.0, value=500.0, step=10.0)
        conv_rate = st.number_input("Conversion rate (%)", min_value=0.1, value=2.0, step=0.1) / 100
        product_price = st.number_input("Product price (optional)", min_value=0.0, value=0.0)

        try:
            df = df[['Keyword', 'Avg. CPC']].dropna()
            df['Avg. CPC'] = pd.to_numeric(df['Avg. CPC'], errors='coerce')
            df = df.dropna(subset=['Avg. CPC'])

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
