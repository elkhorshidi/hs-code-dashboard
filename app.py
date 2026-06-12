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
    st.dataframe(
        matches[columns].fillna("").astype(str),
        width="stretch",
        hide_index=True,
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
        show_result_card("این کد در هر دو بند وجود دارد و دیتابیس نیاز به بررسی دارد.", "warning")
        display_matched_rows("جزئیات بند ۱", band_1_matches)
        display_matched_rows("جزئیات بند ۲", band_2_matches)
    elif exists_in_band_1:
        show_result_card(
            "این کد مشمول بند ۱ است و باید از مسیر تالار دوم برای رفع تعهد بررسی شود.",
            "info",
        )
        display_matched_rows("جزئیات کد", band_1_matches)
    elif exists_in_band_2:
        show_result_card(
            "این کد مشمول بند ۲ است و امکان بررسی مسیر تحویل کش به بانک ملی را دارد.",
            "success",
        )
        display_matched_rows("جزئیات کد", band_2_matches)
    else:
        show_result_card("کد واردشده در دیتابیس فعلی یافت نشد.", "error")


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
        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        html, body, [class*="css"], .stApp {
            direction: rtl;
            text-align: right;
            font-family: Tahoma, Arial, sans-serif;
        }
        h1 {
            font-size: 2rem !important;
            font-weight: 750 !important;
            margin-bottom: 0.25rem !important;
        }
        .subtitle {
            color: #596579;
            font-size: 1rem;
            margin: -0.15rem 0 1.25rem;
        }
        .stTextInput input {
            direction: rtl;
            text-align: right;
            border-radius: 8px;
        }
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            margin-top: 1.75rem;
            min-height: 2.65rem;
            font-weight: 700;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e6eaf0;
            border-radius: 8px;
            padding: 0.8rem 1rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] div {
            direction: rtl;
            text-align: right;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.35rem;
            font-weight: 750;
        }
        div[data-testid="stDataFrame"] {
            direction: rtl;
            text-align: right;
        }
        .result-card {
            border-radius: 8px;
            border: 1px solid;
            padding: 1rem 1.1rem;
            margin: 1rem 0 0.85rem;
            line-height: 1.8;
            font-weight: 700;
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
        }
        div[data-testid="stExpander"] {
            border-radius: 8px;
            border-color: #e6eaf0;
            margin-top: 1rem;
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
        '<div class="subtitle">بررسی سریع مسیر رفع تعهد صادراتی بر اساس کد تعرفه</div>',
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
