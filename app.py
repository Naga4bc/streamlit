import streamlit as st
import pandas as pd
from collections import defaultdict
from google.oauth2 import service_account
import gspread
from datetime import datetime

st.set_page_config(layout="wide")

# Custom CSS for styling
st.markdown(
    """
    <style>
        /* Table container styling */
        .stDataFrame {
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            background-color: white;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# Month color mapping
MONTH_COLORS = {
    "January": "#FFB6C1",  # Light pink
    "February": "#FFE4E1",  # Misty rose
    "March": "#E6E6FA",  # Lavender
    "April": "#98FB98",  # Pale green
    "May": "#87CEEB",  # Sky blue
    "June": "#DDA0DD",  # Plum
    "July": "#F0E68C",  # Khaki
    "August": "#FFA07A",  # Light salmon
    "September": "#DEB887",  # Burlywood
    "October": "#F4A460",  # Sandy brown
    "November": "#BC8F8F",  # Rosy brown
    "December": "#B0C4DE",  # Light steel blue
}


def extract_month(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        return date_obj.strftime("%B %Y")
    except Exception:
        return None


def color_month_rows(df):
    colors = ["#f0f8ff", "#e6f3ff"]  # Alternating light blue shades
    styles = []
    current_color_idx = 0
    current_month = None

    for idx, month in enumerate(df["Month"]):
        if month != current_month:
            current_month = month
            current_color_idx = (current_color_idx + 1) % 2
        styles.append(f"background-color: {colors[current_color_idx]}")

    return styles


def load_google_sheet():
    try:
        # Define service account credentials directly
        credentials_info = {
            "type": "service_account",
            "project_id": "flask-447911",
            "private_key_id": "390f67d23fb0758562b61c3a5cd89bd73f5c4adc",
            "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCOodQwbZZHVbzL
ArvbGtTQC357GKGucwTE1hlx6gsovCW7EMF6e2fT2mCUN1/eY2sJx9u5xmjUHLcu
rmUjFVDab7pHkw5NWLMjsR5gpgGFsKJQ0DnGDxj9RSwu0/Xkp2F5gQh47b5sQyqH
7Ani4KbcVHyBYKbj4SodwqGle1yBt37ymnItvAnHg3n9rbeurlUl9AqiP0wSChzT
gZFmAvrycCaYUbMyNLvMdi5HhEh5y4b9/eSDVC1WUT8kwSqCXKNe89TLAfOspvsF
8l+YdNva41s98hu7tDzBnHU6UulO6vvdzXh1lfjMEF0aQslMTJymoMck6XnaK/cs
PaJvmyp3AgMBAAECggEAHQPmuoNQkupqIZJIzOXEbR4peLkmCurzCWfUfUvzQTIl
KszZzyTTllFSXFR3eDIZUEAL/trR8HR2/1QS1vQ7InSgHHdZ7Xoh1xzs5RRgMuYf
3vi9CAGCP+OWfWA5IW67cZBCPPeASV3QhR4LVNAGocO+IEOdL7ZabvttDtDtnKV9
uumBHDKkLABYQt6KjlAzOSi4SitEgDGKWr1Duc7t96PYEEVwLxNmwvH+4Mn9wXz7
U0tccZ34TR495JWN/JHt6pTY28sy13J7oC2wsLVvY3LnO8pHE4YIRXKO+gp4eqim
vQFRT5I0jmwr2ALRHmYHDFo8nfxzuybn8LtzW8EAgQKBgQC/IHqesB6rwadIEPu+
GQmCMi4UKboTaCM9BT8EEKFfnvdgCcBjjg+hkqjsp2lSZX55gLlxH6jAxZqMaYY+
/nW6eo7gOSaR2tnADCFj4snU02Y2+n6Vb40IXV+1t3fLBny87+/ZKHlIDBIp/ORE
/55Hd8CkhpGojFx2Tx23jOuL8QKBgQC/C4Os+jOYk491h8r8o/Q2swaHvEX1FVEM
4u21hZDFXglVVxVpXKUbBo54LqTIPDA78+I3/4r5crW3+hHHTEt65M1ZBZrjzdvr
Hx6efvCwrjG952gaHh/CHJkju9HGs1NCbjXUb2Cpq+6kGGcFUCdalzuEi0YyFtep
lCtIh4Ik5wKBgQCgZoiiDxreeJqEb8RmiKqjOqvTPiWszdPtDS8SoUZdcpMXZXex
1XKm3eepHOLWRNl87Rw0pSZCClSnDJSe3308MEkiQrRs6iee9k87fgR2+aep8lYz
4beR0pNVdREzMVGUWyWGsWH/pinEVTnZ8lEKl6T0Lv+lXY7nt4QwHDM+cQKBgB6v
HMEFlo/k81+vJb0aIDlA28WlSZ8pg1EMiZ1kDHKGvf0E9Z1skeAbV3qaE0FN2Xln
nGfeFVYnRGR+N6jI6j6czRaFPfFkuPO0ldhjDwlxkO+tYR0AxZ0Jttb0bab6Wl8L
EH5EPURDJxsYCEPkMc3tCFQrgmS9InpMH/+QNCj1AoGAQ/8Pg5dQqGlJGy3tkUDS
3AeMbNbJjk2khskxuw1LifJfJ+8wLzwVKiBTGIk++ZScUwcscfx1z6fk48ayc6an
TL01PnYPa1zmyzjRo3NgrN9cCfM2Ffi+u8mzRLHKr9eNxl6aDWoIErSyv9udW9DP
FjVtg/GklQnIg2+DHI+s/sU=
-----END PRIVATE KEY-----""",
            "client_email": "flask-20@flask-447911.iam.gserviceaccount.com",
            "client_id": "109120585063761435394",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/flask-20%40flask-447911.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com",
        }

        # Convert credentials into a service account object
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )

        # Authorize and access Google Sheets
        client = gspread.authorize(credentials)
        SPREADSHEET_ID = "1JCbBdLcO-erca0fQcadXkdzGxU58UvpD2uINJGlLkPE"
        sheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = sheet.worksheet("QC")
        data = worksheet.get_all_records()

        # Check if data is retrieved
        if not data:
            st.error("No data found in the worksheet")
            return None

        # Convert data to a Pandas DataFrame
        df = pd.DataFrame(data)
        return df

    except Exception as e:
        st.error(f"Error accessing Google Sheet: {str(e)}")
        return None


def process_qc_status(status):
    if pd.isna(status) or status == "":
        return "Fail"
    status = str(status).strip().upper()
    if "PASS" in status:
        return "Pass"
    elif "HOLD" in status:
        return "Hold"
    return "Fail"


def create_sample_type_analysis(results, sample_type):
    data = []

    for month, tests in results[sample_type].items():
        for test_name, status in tests.items():
            total = status["Pass"] + status["Hold"] + status["Fail"]
            pass_rate = (status["Pass"] / total * 100) if total > 0 else 0

            row = {
                "Month": month,
                "Test Name": test_name,
                "Pass": status["Pass"],
                "Hold": status["Hold"],
                "Fail": status["Fail"],
                "Total": total,
                "Pass Rate": f"{pass_rate:.1f}%",
            }
            data.append(row)

    df = pd.DataFrame(data)
    styled_df = df.style.apply(lambda x: color_month_rows(df), axis=0)

    return styled_df, df


def create_capturing_kit_analysis(df):
    # Process Capturing Kit data by sample type
    sample_types = ["sDNA", "cfDNA", "Blood", "RNA"]
    cap_kit_results = {sample_type: [] for sample_type in sample_types}

    for sample_type in sample_types:
        sample_df = df[df["Sample_Type"] == sample_type]

        for cap_kit, group in sample_df.groupby("Cap_Kit"):
            if pd.isna(cap_kit) or cap_kit == "":
                continue

            for month, month_group in group.groupby("Month"):
                total = len(month_group)

                # Use the appropriate QC status column based on sample type
                if sample_type == "RNA":
                    status_col = "QC_RNA_Status"
                else:
                    status_col = "DNA_QC_Status"

                passes = sum(month_group[status_col].apply(process_qc_status) == "Pass")
                holds = sum(month_group[status_col].apply(process_qc_status) == "Hold")
                fails = sum(month_group[status_col].apply(process_qc_status) == "Fail")

                pass_rate = (passes / total * 100) if total > 0 else 0

                row = {
                    "Month": month,
                    "Cap Kit": cap_kit,
                    "Sample Type": sample_type,
                    "Pass": passes,
                    "Hold": holds,
                    "Fail": fails,
                    "Total": total,
                    "Pass Rate": f"{pass_rate:.1f}%",
                }
                cap_kit_results[sample_type].append(row)

    # Create DataFrames for each sample type
    cap_kit_dfs = {}
    styled_cap_kit_dfs = {}

    for sample_type in sample_types:
        if cap_kit_results[sample_type]:
            cap_kit_dfs[sample_type] = pd.DataFrame(cap_kit_results[sample_type])
            styled_cap_kit_dfs[sample_type] = cap_kit_dfs[sample_type].style.apply(
                lambda x: color_month_rows(cap_kit_dfs[sample_type]), axis=0
            )
        else:
            cap_kit_dfs[sample_type] = pd.DataFrame()
            styled_cap_kit_dfs[sample_type] = None

    return styled_cap_kit_dfs, cap_kit_dfs


def analyze_data(df):
    try:
        df["Month"] = df["Date_of_Batch_Received"].apply(extract_month)

        sample_types = ["sDNA", "cfDNA", "Blood", "RNA"]
        results = {
            sample_type: defaultdict(
                lambda: defaultdict(lambda: {"Pass": 0, "Fail": 0, "Hold": 0})
            )
            for sample_type in sample_types
        }

        for _, row in df.iterrows():
            sample_type = row["Sample_Type"]
            month = row["Month"]
            test_name = row["Shipment_Test_Name"]

            if sample_type == "RNA":
                qc_status = process_qc_status(row["QC_RNA_Status"])
            else:
                qc_status = process_qc_status(row["DNA_QC_Status"])

            if sample_type in sample_types:
                results[sample_type][month][test_name][qc_status] += 1

        return results

    except Exception as e:
        st.error(f"Error analyzing data: {str(e)}")
        return None


def main():
    st.title("🧬 Monthly Sample Analysis Dashboard")

    if st.button("🔄 Refresh Data"):
        st.session_state.data_loaded = False

    df = load_google_sheet()

    if df is not None:
        # Process dates and add month information
        df["Month"] = df["Date_of_Batch_Received"].apply(extract_month)

        # Add month filter at the top
        all_months = sorted(
            [m for m in df["Month"].unique() if pd.notna(m)],
            key=lambda x: (
                datetime.strptime(x, "%B %Y") if isinstance(x, str) else datetime.min
            ),
            reverse=True,
        )

        month_filter = st.multiselect(
            "Select Month(s)", ["All Months"] + all_months, default=["All Months"]
        )

        if "All Months" not in month_filter:
            df = df[df["Month"].isin(month_filter)]

        results = analyze_data(df)

        if results:
            tabs = st.tabs(["sDNA", "cfDNA", "Blood", "RNA", "Capturing Kit"])

            # Sample type analysis tabs
            for idx, sample_type in enumerate(["sDNA", "cfDNA", "Blood", "RNA"]):
                with tabs[idx]:
                    st.subheader(f"{sample_type} Analysis")
                    styled_df, raw_df = create_sample_type_analysis(
                        results, sample_type
                    )
                    st.dataframe(styled_df, use_container_width=True)

            # Capturing Kit Analysis
            with tabs[4]:
                st.subheader("Capturing Kit Analysis")

                # Create tabs for each sample type within the Capturing Kit tab
                cap_kit_tabs = st.tabs(["sDNA", "cfDNA", "Blood", "RNA"])

                # Get capturing kit analysis data
                styled_cap_kit_dfs, cap_kit_dfs = create_capturing_kit_analysis(df)

                # Display data for each sample type
                for idx, sample_type in enumerate(["sDNA", "cfDNA", "Blood", "RNA"]):
                    with cap_kit_tabs[idx]:
                        st.subheader(f"{sample_type} Capturing Kit Analysis")
                        if styled_cap_kit_dfs[sample_type] is not None:
                            st.dataframe(
                                styled_cap_kit_dfs[sample_type],
                                use_container_width=True,
                            )
                        else:
                            st.info(f"No capturing kit data found for {sample_type}")

            # Show raw data option at the bottom
            if st.checkbox("Show Raw Data"):
                st.subheader("Raw Data")
                st.dataframe(df)


def create_consolidated_capturing_kit_analysis(df):
    """
    Creates a consolidated capturing kit analysis table with all sample types
    in one view, using different colors for each sample type.
    """
    # Process Capturing Kit data for all sample types
    sample_types = ["sDNA", "cfDNA", "Blood", "RNA"]
    consolidated_results = []

    # Define sample type colors
    SAMPLE_TYPE_COLORS = {
        "sDNA": "#FFDD44",  # Soft Gold
        "cfDNA": "#B0E57C",  # Light Green
        "Blood": "#FF9999",  # Soft Pink-Red
        "RNA": "#89CFF0",  # Baby Blue
    }

    for sample_type in sample_types:
        sample_df = df[df["Sample_Type"] == sample_type]

        for cap_kit, group in sample_df.groupby("Cap_Kit"):
            if pd.isna(cap_kit) or cap_kit == "":
                continue

            for month, month_group in group.groupby("Month"):
                total = len(month_group)

                # Use the appropriate QC status column based on sample type
                if sample_type == "RNA":
                    status_col = "QC_RNA_Status"
                else:
                    status_col = "DNA_QC_Status"

                passes = sum(month_group[status_col].apply(process_qc_status) == "Pass")
                holds = sum(month_group[status_col].apply(process_qc_status) == "Hold")
                fails = sum(month_group[status_col].apply(process_qc_status) == "Fail")

                pass_rate = (passes / total * 100) if total > 0 else 0

                row = {
                    "Month": month,
                    "Cap Kit": cap_kit,
                    "Sample Type": sample_type,
                    "Pass": passes,
                    "Hold": holds,
                    "Fail": fails,
                    "Total": total,
                    "Pass Rate": f"{pass_rate:.1f}%",
                }
                consolidated_results.append(row)

    # Create consolidated DataFrame
    if consolidated_results:
        consolidated_df = pd.DataFrame(consolidated_results)

        # Define styling function to color rows by sample type
        def color_by_sample_type(row):
            sample_type = row["Sample Type"]
            return [
                f"background-color: {SAMPLE_TYPE_COLORS.get(sample_type, '#FFFFFF')}"
            ] * len(row)

        # Apply styling
        styled_consolidated_df = consolidated_df.style.apply(
            color_by_sample_type, axis=1
        )
        return styled_consolidated_df, consolidated_df
    else:
        return None, pd.DataFrame()


# Update the main function to include the consolidated view
def main():
    st.title("🧬 Monthly Sample Analysis Dashboard")

    # Add custom CSS for larger headers
    st.markdown(
        """
        <style>
            .big-header {
                font-size: 26px !important;
                font-weight: bold;
                padding: 10px 0;
                margin-bottom: 15px;
                border-bottom: 2px solid #ddd;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )

    if st.button("🔄 Refresh Data"):
        st.session_state.data_loaded = False

    df = load_google_sheet()

    if df is not None:
        # Process dates and add month information
        df["Month"] = df["Date_of_Batch_Received"].apply(extract_month)

        # Add month filter at the top
        all_months = sorted(
            [m for m in df["Month"].unique() if pd.notna(m)],
            key=lambda x: (
                datetime.strptime(x, "%B %Y") if isinstance(x, str) else datetime.min
            ),
            reverse=True,
        )

        month_filter = st.multiselect(
            "Select Month(s)", ["All Months"] + all_months, default=["All Months"]
        )

        if "All Months" not in month_filter:
            df = df[df["Month"].isin(month_filter)]

        results = analyze_data(df)

        if results:
            tabs = st.tabs(["sDNA", "cfDNA", "Blood", "RNA", "Capturing Kit"])

            # Sample type analysis tabs
            for idx, sample_type in enumerate(["sDNA", "cfDNA", "Blood", "RNA"]):
                with tabs[idx]:
                    st.markdown(
                        f'<div class="big-header">{sample_type} Analysis</div>',
                        unsafe_allow_html=True,
                    )
                    styled_df, raw_df = create_sample_type_analysis(
                        results, sample_type
                    )
                    st.dataframe(styled_df, use_container_width=True)

            # Capturing Kit Analysis
            with tabs[4]:
                st.markdown(
                    '<div class="big-header">Capturing Kit Analysis</div>',
                    unsafe_allow_html=True,
                )

                # Create tabs for the individual and consolidated views
                cap_kit_subtabs = st.tabs(
                    ["All Capturing Kit", "sDNA", "cfDNA", "Blood", "RNA"]
                )

                # Get capturing kit analysis data
                styled_cap_kit_dfs, cap_kit_dfs = create_capturing_kit_analysis(df)

                # Add the consolidated view as the first tab
                with cap_kit_subtabs[0]:
                    st.markdown(
                        '<div class="big-header">Consolidated Capturing Kit Analysis</div>',
                        unsafe_allow_html=True,
                    )
                    # Create legend for sample types
                    st.markdown(
                        '<div style="display: flex; gap: 15px; margin-bottom: 15px;">'
                        '<div style="display: flex; align-items: center;"><div style="width: 20px; height: 20px; background-color: #FFD700; margin-right: 5px;"></div>sDNA</div>'
                        '<div style="display: flex; align-items: center;"><div style="width: 20px; height: 20px; background-color: #98FB98; margin-right: 5px;"></div>cfDNA</div>'
                        '<div style="display: flex; align-items: center;"><div style="width: 20px; height: 20px; background-color: #FF6B6B; margin-right: 5px;"></div>Blood</div>'
                        '<div style="display: flex; align-items: center;"><div style="width: 20px; height: 20px; background-color: #87CEFA; margin-right: 5px;"></div>RNA</div>'
                        "</div>",
                        unsafe_allow_html=True,
                    )

                    styled_consolidated_df, _ = (
                        create_consolidated_capturing_kit_analysis(df)
                    )
                    if styled_consolidated_df is not None:
                        st.dataframe(styled_consolidated_df, use_container_width=True)
                    else:
                        st.info("No capturing kit data found")

                # Display individual sample type data in their respective tabs
                for idx, sample_type in enumerate(["sDNA", "cfDNA", "Blood", "RNA"]):
                    with cap_kit_subtabs[idx + 1]:
                        st.markdown(
                            f'<div class="big-header">{sample_type} Capturing Kit Analysis</div>',
                            unsafe_allow_html=True,
                        )
                        if styled_cap_kit_dfs[sample_type] is not None:
                            st.dataframe(
                                styled_cap_kit_dfs[sample_type],
                                use_container_width=True,
                            )
                        else:
                            st.info(f"No capturing kit data found for {sample_type}")

            # Show raw data option at the bottom
            if st.checkbox("Show Raw Data"):
                st.markdown(
                    '<div class="big-header">Raw Data</div>', unsafe_allow_html=True
                )
                st.dataframe(df)


if __name__ == "__main__":
    main()
