import streamlit as st
import pandas as pd
from scraper import fetch_page_content, extract_text_from_html
from parser import extract_tender_data
from exporter import to_excel, to_csv

st.set_page_config(
    page_title="Tender Data Extractor",
    page_icon="🏗️",
    layout="centered"
)

st.title("Data Extractor")
st.markdown("Paste a tender or commercial project URL and extract structured data instantly.")

# Sidebar
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
    st.markdown("---")
    st.markdown("**💡 If the site needs JavaScript:**")
    st.markdown("Use the *Paste HTML* tab below as a fallback.")

# Validate secret exists at startup
try:
    _ = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ Gemini API key not configured. Please add GEMINI_API_KEY to Streamlit Secrets.")
    st.stop()

# Two input modes
tab1, tab2 = st.tabs(["🔗 Paste URL", "📋 Paste HTML (for JS-heavy sites)"])

content = None
source_url = ""

with tab1:
    st.markdown("#### Enter the tender page URL")
    url = st.text_input(
        label="URL",
        placeholder="https://example.com/tender/project-123",
        label_visibility="collapsed",
        key="url_input"
    )
    extract_url_btn = st.button("🚀 Extract from URL", type="primary", use_container_width=True, key="btn_url")

    if extract_url_btn:
        if not url.strip():
            st.error("⚠️ Please enter a URL.")
        else:
            with st.spinner("📡 Fetching page..."):
                fetched, error = fetch_page_content(url.strip())

            if error == "JS_BLOCKED":
                st.warning(
                    "⚠️ This site loads data using JavaScript — the URL method can't see its content.\n\n"
                    "**👉 Use the 'Paste HTML' tab instead:**\n"
                    "1. Open the tender page in your browser\n"
                    "2. Press `Ctrl+U` (or right-click → View Page Source)\n"
                    "3. Select all (`Ctrl+A`), copy (`Ctrl+C`)\n"
                    "4. Paste it in the 'Paste HTML' tab"
                )
            elif error:
                st.error(f"Could not retrieve the page: {error}")
            else:
                content = fetched
                source_url = url.strip()
                st.success("✅ Page fetched!")

with tab2:
    st.markdown("#### Paste the full HTML source of the tender page")
    st.caption("Open the page in browser → Ctrl+U (View Source) → Select All → Copy → Paste here")
    raw_html = st.text_area(
        label="HTML",
        placeholder="Paste full page HTML here...",
        height=200,
        label_visibility="collapsed",
        key="html_input"
    )
    manual_url = st.text_input(
        "Page URL (optional, for reference)",
        placeholder="https://up-rera.in/projects/...",
        key="manual_url"
    )
    extract_html_btn = st.button("🚀 Extract from HTML", type="primary", use_container_width=True, key="btn_html")

    if extract_html_btn:
        if not raw_html.strip():
            st.error("⚠️ Please paste the page HTML.")
        else:
            with st.spinner("🔍 Parsing HTML..."):
                parsed, error = extract_text_from_html(raw_html.strip())
            if error:
                st.error(f"Failed to parse HTML: {error}")
            else:
                content = parsed
                source_url = manual_url.strip() if manual_url.strip() else "Pasted HTML"
                st.success("✅ HTML parsed!")

# Run AI extraction if content is ready
if content:
    st.markdown("---")
    with st.status("🤖 AI is extracting tender fields...", expanded=True) as status:
        st.write("Sending to Gemini AI... (may take up to 60s if rate-limited, please wait)")
        api_key = st.secrets["GEMINI_API_KEY"]
        data, error = extract_tender_data(content, api_key, source_url)

        if error:
            status.update(label="Extraction failed", state="error")
            st.error(f"AI extraction error: {error}")
            st.stop()

        status.update(label="✅ Extraction complete!", state="complete")

    # Display results
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
    display_df = display_df[
        display_df["Value"].notna() &
        (display_df["Value"] != "null") &
        (display_df["Value"] != "None") &
        (display_df["Value"] != "")
    ]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Download
    st.markdown("### ⬇️ Download")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Download Excel (.xlsx)",
            data=to_excel(df),
            file_name="tender_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with col2:
        st.download_button(
            label="📥 Download CSV (.csv)",
            data=to_csv(df),
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
