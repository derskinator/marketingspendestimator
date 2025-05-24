import streamlit as st
import pandas as pd

st.set_page_config(page_title="Marketing Spend Estimator", layout="centered")
st.title("📊 Marketing Spend Estimator")

uploaded_file = st.file_uploader("Upload your Google Ads keyword CSV", type=["csv"])

# Adjusted for your exact export format
def find_header_row(file, required_columns):
    """Search for the row that contains required columns (or their known aliases)."""
    file.seek(0)
    for i, line in enumerate(file):
        decoded = line.decode("utf-8", errors="ignore").lower()
        if all(any(alt in decoded for alt in [col.lower(), 'search term'] if col == 'Keyword') if col == 'Keyword' else col.lower() in decoded for col in required_columns):
            return i
    return None

if uploaded_file:
    required_columns = ['Keyword', 'Avg. CPC']  # we'll remap Search term → Keyword

    header_row = find_header_row(uploaded_file, required_columns)

    if header_row is None:
        st.error("❌ Could not find a header row with required columns (e.g., 'Search term', 'Avg. CPC').")
        st.stop()

    uploaded_file.seek(0)

    try:
        df = pd.read_csv(uploaded_file, skiprows=header_row)
    except Exception as e:
        st.error(f"❌ Failed to read CSV: {e}")
        st.stop()

    # Rename 'Search term' to 'Keyword' if present
    if 'Search term' in df.columns:
        df.rename(columns={'Search term': 'Keyword'}, inplace=True)

    if not {'Keyword', 'Avg. CPC'}.issubset(df.columns):
        st.error("❌ Your file must include 'Search term' or 'Keyword' and 'Avg. CPC'.")
        st.stop()
    else:
        st.success("✅ File loaded and formatted!")

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
