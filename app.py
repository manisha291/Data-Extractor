import streamlit as st
import pandas as pd
from scraper import fetch_page_content
from parser import extract_tender_data
from exporter import to_excel, to_csv

st.set_page_config(
    page_title="Tender Data Extractor",
    page_icon="🏗️",
    layout="centered"
)

st.title("Data Extractor")
st.markdown("Paste a tender or commercial project URL and extract structured data instantly.")

# Sidebar - Info only (no API key input)
with st.sidebar:
    st.header("📋 Fields Extracted")
    st.markdown("""
    - 📋 Title & Tender ID
    - 🏢 Issuing Authority
    - 📁 Category
    - 📅 Deadline
    - 💰 Budget
    - 📍 Location
    - 🔄 Status
    - 📝 Description
    """)
    st.markdown("---")
    st.info("ℹ️ Works best on public tender pages. Pages behind login walls cannot be accessed.")

# Validate secret exists at startup
try:
    _ = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ Gemini API key not configured. Please add GEMINI_API_KEY to Streamlit Secrets.")
    st.stop()

# Main Input
st.markdown("### 🔗 Enter Tender URL")
url = st.text_input(
    label="URL",
    placeholder="https://example.com/tender/project-123",
    label_visibility="collapsed"
)

extract_btn = st.button("🚀 Extract Data", type="primary", use_container_width=True)

if extract_btn:
    if not url.strip():
        st.error("⚠️ Please enter a URL.")
    else:
        # Step 1: Fetch
        with st.status("Fetching webpage content...", expanded=True) as status:
            st.write("📡 Connecting to URL...")
            content, error = fetch_page_content(url.strip())

            if error:
                status.update(label="Failed to fetch page", state="error")
                st.error(f"Could not retrieve the page: {error}")
                st.info("💡 Tip: Some sites block automated access. Try a different tender URL.")
                st.stop()

            st.write("✅ Page fetched successfully!")

            # Step 2: Extract with AI
            st.write("🤖 AI is reading and extracting tender fields...")
            api_key = st.secrets["GEMINI_API_KEY"]
            data, error = extract_tender_data(content, api_key, url.strip())

            if error:
                status.update(label="Extraction failed", state="error")
                st.error(f"AI extraction error: {error}")
                st.stop()

            status.update(label="Extraction complete!", state="complete")

        # Step 3: Display Results
        st.markdown("---")
        st.markdown("### 📊 Extracted Data")

        df = pd.DataFrame([data])

        col_rename = {
            "title": "Project Title",
            "tender_id": "Tender ID",
            "issuing_authority": "Issuing Authority",
            "category": "Category",
            "deadline": "Deadline",
            "budget": "Budget / Value",
            "location": "Location",
            "status": "Status",
            "description": "Description",
            "source_url": "Source URL"
        }
        df.rename(columns=col_rename, inplace=True)

        display_df = df.T.reset_index()
        display_df.columns = ["Field", "Value"]
        display_df = display_df[display_df["Value"].notna() & (display_df["Value"] != "null") & (display_df["Value"] != "")]

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Step 4: Download
        st.markdown("### ⬇️ Download")
        col1, col2 = st.columns(2)

        with col1:
            excel_data = to_excel(df)
            st.download_button(
                label="📥 Download Excel (.xlsx)",
                data=excel_data,
                file_name="tender_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col2:
            csv_data = to_csv(df)
            st.download_button(
                label="📥 Download CSV (.csv)",
                data=csv_data,
                file_name="tender_data.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.success("✅ Done! Your data is ready to download.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:gray; font-size:12px;'>Powered by Google Gemini AI · Built with Streamlit</div>",
    unsafe_allow_html=True
)
