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
    st.subheader(title)
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
    col_1.metric("تعداد کدهای بند ۱", f"{len(band_1_codes):,}")
    col_2.metric("تعداد کدهای بند ۲", f"{len(band_2_codes):,}")
    col_3.metric("مجموع کدهای یکتا", f"{len(unique_codes):,}")


def check_hs_code(entered_code: str, band_1_df: pd.DataFrame, band_2_df: pd.DataFrame) -> None:
    normalized_code = normalize_hs_code(entered_code)

    if not normalized_code:
        st.warning("لطفاً یک کد تعرفه معتبر وارد کنید.")
        return

    band_1_matches = band_1_df[band_1_df["کد نرمال‌شده"] == normalized_code]
    band_2_matches = band_2_df[band_2_df["کد نرمال‌شده"] == normalized_code]

    exists_in_band_1 = not band_1_matches.empty
    exists_in_band_2 = not band_2_matches.empty

    if exists_in_band_1 and exists_in_band_2:
        st.warning("این کد در هر دو بند وجود دارد و دیتابیس نیاز به بررسی دارد.")
        display_matched_rows("جزئیات بند ۱", band_1_matches)
        display_matched_rows("جزئیات بند ۲", band_2_matches)
    elif exists_in_band_1:
        st.success("این کد مشمول بند ۱ است و باید از مسیر تالار دوم برای رفع تعهد بررسی شود.")
        display_matched_rows("جزئیات کد", band_1_matches)
    elif exists_in_band_2:
        st.success("این کد مشمول بند ۲ است و امکان بررسی مسیر تحویل کش به بانک ملی را دارد.")
        display_matched_rows("جزئیات کد", band_2_matches)
    else:
        st.info("کد واردشده در دیتابیس فعلی یافت نشد.")


def show_database_preview(band_1_df: pd.DataFrame, band_2_df: pd.DataFrame) -> None:
    with st.expander("نمایش و جست‌وجو در دیتابیس"):
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

        st.dataframe(
            database[preview_columns].fillna("").astype(str),
            width="stretch",
            hide_index=True,
        )


def apply_rtl_styles() -> None:
    st.markdown(
        """
        <style>
        html, body, [class*="css"], .stApp {
            direction: rtl;
            text-align: right;
            font-family: Tahoma, Arial, sans-serif;
        }
        .stTextInput input {
            direction: rtl;
            text-align: right;
        }
        div[data-testid="stMetric"],
        div[data-testid="stDataFrame"] {
            direction: rtl;
            text-align: right;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="داشبورد بررسی کد تعرفه", layout="wide")
    apply_rtl_styles()

    st.title("داشبورد بررسی کد تعرفه")

    try:
        band_1_df, band_2_df = load_data()
    except Exception as error:
        st.error(f"خطا در بارگذاری اطلاعات از Google Sheets: {error}")
        st.stop()

    show_metrics(band_1_df, band_2_df)

    entered_code = st.text_input("کد تعرفه را وارد کنید")
    if st.button("بررسی کد", type="primary"):
        check_hs_code(entered_code, band_1_df, band_2_df)

    show_database_preview(band_1_df, band_2_df)


if __name__ == "__main__":
    main()
