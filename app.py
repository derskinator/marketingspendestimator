import streamlit as st
import pandas as pd
import chardet

st.set_page_config(page_title="Marketing Spend Estimator", layout="centered")
st.title("📊 Marketing Spend Estimator")

uploaded_file = st.file_uploader("Upload your Google Keyword Planner TSV file", type=["csv", "tsv"])

if uploaded_file:
    # Detect encoding
    raw_data = uploaded_file.read()
    detected = chardet.detect(raw_data)
    encoding = detected['encoding'] or 'utf-8'
    uploaded_file.seek(0)

    try:
        # Read as TSV, skip first 2 metadata lines
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

    required = ['keyword', 'low_cpc', 'high_cpc', 'competition_index']
    if not all(col in df.columns for col in required):
        st.error("❌ Missing required columns: 'keyword', 'top of page bid (low range)', 'top of page bid (high range)', and 'competition (indexed value)'")
        st.write("Detected columns:", list(df.columns))
        st.stop()

    st.success("✅ File loaded successfully!")

    # Inputs
    st.subheader("🔧 Set Your Assumptions")
    budget = st.number_input("Total budget ($)", min_value=0.0, value=500.0, step=10.0)
    conv_rate = st.number_input("Conversion rate (%)", min_value=0.1, value=2.0, step=0.1) / 100
    product_price = st.number_input("Product price ($)", min_value=0.0, value=100.0, step=1.0)

    try:
        # Drop and clean rows
        df = df[['keyword', 'low_cpc', 'high_cpc', 'competition_index']].dropna()
        df['low_cpc'] = pd.to_numeric(df['low_cpc'], errors='coerce')
        df['high_cpc'] = pd.to_numeric(df['high_cpc'], errors='coerce')
        df['competition_index'] = pd.to_numeric(df['competition_index'], errors='coerce')
        df.dropna(inplace=True)

        # Normalize competition and compute weighted CPC per keyword
        df['competition_score'] = df['competition_index'] / 100.0
        df['weighted_cpc'] = df['low_cpc'] * (1 - df['competition_score']) + df['high_cpc'] * df['competition_score']

        # Average inputs across all keywords
        avg_weighted_cpc = df['weighted_cpc'].mean()

        # Use average CPC in core calculations
        clicks = budget / avg_weighted_cpc
        conversions = clicks * conv_rate
        cpa = budget / conversions if conversions > 0 else None
        revenue = conversions * product_price
        roas = revenue / budget if budget > 0 else None

        st.subheader("📊 Calculated Results (using average CPC across keywords)")
        st.metric("Avg Weighted CPC", f"${avg_weighted_cpc:.2f}")
        st.metric("Estimated Clicks", f"{clicks:,.0f}")
        st.metric("Estimated Conversions", f"{conversions:.2f}")
        st.metric("Estimated CPA", f"${cpa:.2f}" if cpa else "N/A")
        st.metric("Estimated Revenue", f"${revenue:.2f}")
        st.metric("Estimated ROAS", f"{roas:.2f}x" if roas else "N/A")

        st.markdown("---")
        st.subheader("🧠 Formula Summary")
        st.markdown("""
        - **Avg Weighted CPC** = Average of per-keyword weighted CPC  
        - **Weighted CPC** = Low CPC × (1 - Competition) + High CPC × Competition  
        - **Clicks** = Budget ÷ Avg Weighted CPC  
        - **Conversions** = Clicks × Conversion Rate  
        - **CPA** = Budget ÷ Conversions  
        - **Revenue** = Conversions × Product Price  
        - **ROAS** = Revenue ÷ Budget
        """)

    except Exception as e:
        st.error(f"⚠️ Error during calculations: {e}")

else:
    st.info("📄 Upload your Google Keyword Planner TSV export to begin.")


