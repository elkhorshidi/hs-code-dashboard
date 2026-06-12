import html
import re

import pandas as pd
import streamlit as st


BAND_1_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vTKBka52Hm8m0XAuHN4rmMMn2Z86h8ieagHsf7nCQGpviH9q1GvvTilOw8D3EG49eAZr4XP_UrTCtwQ/"
    "pub?gid=1155786559&single=true&output=csv"
)

BAND_2_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vTKBka52Hm8m0XAuHN4rmMMn2Z86h8ieagHsf7nCQGpviH9q1GvvTilOw8D3EG49eAZr4XP_UrTCtwQ/"
    "pub?gid=1196592761&single=true&output=csv"
)

DISPLAY_COLUMNS = [
    "HS Code",
    "نوع کالا",
    "شرح تعرفه",
    "محصول",
    "گروه محصولی",
    "صنعت",
]

DIGIT_TRANSLATION = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)


def normalize_hs_code(value) -> str:
    if pd.isna(value):
        return ""

    code = str(value).strip().translate(DIGIT_TRANSLATION)
    code = re.sub(r"\.0$", "", code)
    return re.sub(r"\D", "", code)


@st.cache_data(ttl=300)
def load_band_data(url: str, band_name: str) -> pd.DataFrame:
    df = pd.read_csv(url, dtype={"HS Code": "string"})

    if "HS Code" not in df.columns:
        raise ValueError(f'ستون "HS Code" در فایل {band_name} وجود ندارد.')

    df = df.copy()
    df["کد نرمال‌شده"] = df["HS Code"].apply(normalize_hs_code)
    df["بند"] = band_name
    return df


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    band_1_df = load_band_data(BAND_1_CSV_URL, "بند ۱")
    band_2_df = load_band_data(BAND_2_CSV_URL, "بند ۲")
    return band_1_df, band_2_df


def available_display_columns(df: pd.DataFrame) -> list[str]:
    return [column for column in DISPLAY_COLUMNS if column in df.columns]


def display_matched_rows(title: str, matches: pd.DataFrame) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    columns = available_display_columns(matches)
    rows_html = []

    for _, row in matches[columns].fillna("").astype(str).iterrows():
        cells = []
        for column in columns:
            value = html.escape(row[column])
            cell_class = ' class="code-cell"' if column == "HS Code" else ""
            cells.append(f"<td{cell_class}>{value}</td>")
        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    headers_html = "".join(f"<th>{html.escape(column)}</th>" for column in columns)
    body_html = "".join(rows_html)

    st.markdown(
        f"""
        <div class="details-table-wrap">
            <table class="details-table">
                <thead>
                    <tr>{headers_html}</tr>
                </thead>
                <tbody>
                    {body_html}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_metrics(band_1_df: pd.DataFrame, band_2_df: pd.DataFrame) -> None:
    band_1_codes = set(band_1_df["کد نرمال‌شده"].dropna()) - {""}
    band_2_codes = set(band_2_df["کد نرمال‌شده"].dropna()) - {""}
    unique_codes = band_1_codes | band_2_codes

    col_1, col_2, col_3 = st.columns(3)
    with col_1:
        st.metric("تعداد کدهای بند ۱", f"{len(band_1_codes):,}")
    with col_2:
        st.metric("تعداد کدهای بند ۲", f"{len(band_2_codes):,}")
    with col_3:
        st.metric("مجموع کدهای یکتا", f"{len(unique_codes):,}")


def show_result_card(message: str, style: str) -> None:
    st.markdown(
        f"""
        <div class="result-card result-{style}">
            <div class="result-text">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def check_hs_code(entered_code: str, band_1_df: pd.DataFrame, band_2_df: pd.DataFrame) -> None:
    normalized_code = normalize_hs_code(entered_code)

    if not normalized_code:
        show_result_card("لطفاً یک کد تعرفه معتبر وارد کنید.", "warning")
        return

    band_1_matches = band_1_df[band_1_df["کد نرمال‌شده"] == normalized_code]
    band_2_matches = band_2_df[band_2_df["کد نرمال‌شده"] == normalized_code]

    exists_in_band_1 = not band_1_matches.empty
    exists_in_band_2 = not band_2_matches.empty

    if exists_in_band_1 and exists_in_band_2:
        show_result_card(
            f"کد {normalized_code} در هر دو بند وجود دارد و دیتابیس نیاز به بررسی دارد.",
            "warning",
        )
        display_matched_rows("جزئیات بند ۱", band_1_matches)
        display_matched_rows("جزئیات بند ۲", band_2_matches)
    elif exists_in_band_1:
        show_result_card(
            f"""
            کد {normalized_code} مشمول بند ۱ است و امکان بررسی مسیرهای زیر جهت رفع تعهد صادراتی وجود دارد:
            <br>۱- عرضه در تالار دوم
            <br>۲- واردات در مقابل صادرات
            """,
            "info",
        )
        display_matched_rows("جزئیات کد", band_1_matches)
    elif exists_in_band_2:
        show_result_card(
            f"""
            کد {normalized_code} مشمول بند ۲ است و امکان بررسی مسیرهای زیر جهت رفع تعهد صادراتی وجود دارد:
            <br>۱- تحویل کش به بانک ملی <strong>(گزینه پیشنهادی)</strong>
            <br>۲- واردات در مقابل صادرات
            <br>۳- عرضه در تالار دوم
            """,
            "success",
        )
        display_matched_rows("جزئیات کد", band_2_matches)
    else:
        show_result_card(f"کد {normalized_code} در دیتابیس فعلی یافت نشد.", "error")


def show_database_preview(band_1_df: pd.DataFrame, band_2_df: pd.DataFrame) -> None:
    with st.expander("نمایش و جست‌وجو در دیتابیس", expanded=False):
        search_text = st.text_input("جست‌وجو در دیتابیس", key="database_preview_search")
        database = pd.concat([band_1_df, band_2_df], ignore_index=True)
        preview_columns = ["بند"] + available_display_columns(database)

        if search_text:
            normalized_search = normalize_hs_code(search_text)
            text_search = search_text.strip()

            text_mask = database[preview_columns].astype(str).apply(
                lambda column: column.str.contains(text_search, case=False, na=False, regex=False)
            ).any(axis=1)

            if normalized_search:
                code_mask = database["کد نرمال‌شده"].str.contains(
                    normalized_search,
                    na=False,
                    regex=False,
                )
                database = database[text_mask | code_mask]
            else:
                database = database[text_mask]

        st.caption(f"{len(database):,} ردیف قابل نمایش")
        st.dataframe(
            database[preview_columns].fillna("").astype(str),
            width="stretch",
            hide_index=True,
        )


def apply_rtl_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&display=swap');

        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 2rem;
            direction: rtl;
            text-align: right;
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif;
        }
        .stApp {
            direction: rtl;
            text-align: right;
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif;
        }
        h1,
        h2,
        h3,
        h4,
        h5,
        h6,
        p,
        label,
        input,
        textarea,
        button,
        .stMarkdown,
        .stTextInput,
        .stButton,
        .stTextInput label,
        [data-testid="stWidgetLabel"],
        .stButton > button,
        div[data-testid="stMetric"],
        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricValue"],
        div[data-testid="stExpander"],
        div[data-testid="stDataFrame"],
        .result-card,
        .result-text,
        .section-title {
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif !important;
        }
        h1 {
            font-size: 2rem !important;
            font-weight: 750 !important;
            margin-bottom: 0.25rem !important;
            text-align: right;
        }
        .app-subtitle {
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif !important;
            font-size: 1rem;
            color: #64748b;
            font-weight: 500;
            text-align: right;
            direction: rtl;
            margin-top: -0.5rem;
            margin-bottom: 1.5rem;
        }
        .stTextInput label,
        [data-testid="stWidgetLabel"] {
            direction: rtl !important;
            text-align: right !important;
        }
        .stTextInput input,
        input[type="text"] {
            direction: rtl !important;
            text-align: right !important;
            border-radius: 8px;
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif !important;
            unicode-bidi: plaintext;
            font-variant-numeric: tabular-nums;
        }
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            margin-top: 1.75rem;
            min-height: 2.65rem;
            font-weight: 700;
            direction: rtl !important;
            text-align: center !important;
        }
        .stButton > button p {
            text-align: center !important;
        }
        div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stCaptionContainer"] p {
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif !important;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e6eaf0;
            border-radius: 8px;
            padding: 0.8rem 1rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
            direction: rtl !important;
            text-align: right !important;
        }
        div[data-testid="stMetric"] label {
            direction: rtl !important;
            text-align: right !important;
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif !important;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.35rem;
            font-weight: 750;
            direction: ltr !important;
            text-align: right !important;
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif !important;
            font-variant-numeric: tabular-nums;
        }
        div[data-testid="stMetricLabel"] {
            justify-content: flex-end;
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif !important;
        }
        div[data-testid="stDataFrame"] {
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif !important;
        }
        div[data-testid="stDataFrame"] [role="columnheader"],
        div[data-testid="stDataFrame"] [role="gridcell"] {
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif !important;
            text-align: right !important;
            justify-content: flex-end !important;
        }
        .result-card {
            border-radius: 8px;
            border: 1px solid;
            padding: 1rem 1.1rem;
            margin: 1rem 0 0.85rem;
            line-height: 1.8;
            font-weight: 700;
            direction: rtl;
            text-align: right;
        }
        .result-text {
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif !important;
        }
        .result-success {
            background: #ecfdf3;
            border-color: #b7ebc6;
            color: #166534;
        }
        .result-info {
            background: #eff6ff;
            border-color: #bfdbfe;
            color: #1d4ed8;
        }
        .result-warning {
            background: #fffbeb;
            border-color: #fde68a;
            color: #92400e;
        }
        .result-error {
            background: #fef2f2;
            border-color: #fecaca;
            color: #b91c1c;
        }
        .section-title {
            font-size: 1rem;
            font-weight: 750;
            margin: 0.75rem 0 0.45rem;
            color: #1f2937;
            direction: rtl;
            text-align: right;
        }
        .details-table-wrap {
            direction: rtl;
            margin: 0.4rem 0 1rem;
            overflow-x: auto;
        }
        .details-table {
            width: 100%;
            border-collapse: collapse;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            direction: rtl;
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif !important;
            font-size: 0.92rem;
            line-height: 1.8;
            overflow: hidden;
        }
        .details-table th,
        .details-table td {
            border-bottom: 1px solid #e5e7eb;
            border-left: 1px solid #eef2f7;
            padding: 0.7rem 0.85rem;
            text-align: right;
            vertical-align: top;
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif !important;
        }
        .details-table th {
            background: #f8fafc;
            color: #334155;
            font-weight: 700;
            white-space: nowrap;
        }
        .details-table td {
            color: #1f2937;
            background: #ffffff;
        }
        .details-table tr:last-child td {
            border-bottom: 0;
        }
        .details-table .code-cell {
            direction: ltr;
            unicode-bidi: plaintext;
            font-variant-numeric: tabular-nums;
            white-space: nowrap;
            text-align: right;
        }
        div[data-testid="stExpander"] {
            border-radius: 8px;
            border-color: #e6eaf0;
            margin-top: 1rem;
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif !important;
        }
        div[data-testid="stExpander"] summary p {
            direction: rtl;
            text-align: right !important;
            font-family: "Vazirmatn", Tahoma, Arial, sans-serif !important;
        }
        div[data-testid="stHorizontalBlock"] {
            direction: rtl;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="داشبورد بررسی کد تعرفه", layout="wide")
    apply_rtl_styles()

    st.title("داشبورد بررسی کد تعرفه")
    st.markdown(
        '<div class="app-subtitle">بررسی سریع مسیر رفع تعهد صادراتی بر اساس کد تعرفه</div>',
        unsafe_allow_html=True,
    )

    try:
        band_1_df, band_2_df = load_data()
    except Exception as error:
        st.error(f"خطا در بارگذاری اطلاعات از Google Sheets: {error}")
        st.stop()

    show_metrics(band_1_df, band_2_df)

    input_col, button_col = st.columns([4, 1])
    with input_col:
        entered_code = st.text_input("کد تعرفه را وارد کنید")
    with button_col:
        check_clicked = st.button("بررسی کد", type="primary")

    if check_clicked:
        check_hs_code(entered_code, band_1_df, band_2_df)

    show_database_preview(band_1_df, band_2_df)


if __name__ == "__main__":
    main()
