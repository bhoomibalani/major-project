import re
import pandas as pd


# Common WhatsApp export timestamp styles (Android dash + iOS brackets)
DATE_PATTERNS = [
    # 07/09/22, 10:02 am -   |  07/09/22, 10:02 -   |  with optional seconds
    (
        r"\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}(?::\d{2})?"
        r"(?:\s*[\u202f\u00a0 ]?[aApP][mM])?\s-\s"
    ),
    # 07-09-22, 10:02 am -
    (
        r"\d{1,2}-\d{1,2}-\d{2,4},\s\d{1,2}:\d{2}(?::\d{2})?"
        r"(?:\s*[\u202f\u00a0 ]?[aApP][mM])?\s-\s"
    ),
    # [07/09/22, 10:02:00 AM]  or  [7/9/22, 10:02 AM]
    (
        r"\[\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}(?::\d{2})?"
        r"(?:\s*[\u202f\u00a0 ]?[aApP][mM])?\]\s?"
    ),
    # [07.09.22, 10:02:00]
    (
        r"\[\d{1,2}\.\d{1,2}\.\d{2,4},\s\d{1,2}:\d{2}(?::\d{2})?"
        r"(?:\s*[\u202f\u00a0 ]?[aApP][mM])?\]\s?"
    ),
]


def _clean_date(raw: str) -> str:
    raw = raw.strip()
    raw = raw.replace("[", "").replace("]", "")
    raw = re.sub(r"\s*-\s*$", "", raw)
    raw = raw.replace(",", "")
    raw = raw.replace("\u202f", " ").replace("\u00a0", " ")
    raw = raw.replace(".", "/", 2)  # dd.mm.yy -> dd/mm/yy for parsing
    return raw.strip()


def preprocess(data: str) -> pd.DataFrame:
    # Strip BOM / invisible direction marks WhatsApp sometimes adds
    data = data.lstrip("\ufeff").replace("\u200e", "").replace("\u200f", "")

    messages, dates = [], []
    for pattern in DATE_PATTERNS:
        found_dates = re.findall(pattern, data)
        if len(found_dates) > len(dates):
            dates = [_clean_date(d) for d in found_dates]
            messages = re.split(pattern, data)[1:]

    df = pd.DataFrame(
        {
            "user_message": messages,
            "date": pd.to_datetime(dates, dayfirst=True, errors="coerce"),
        }
    )

    if df.empty:
        return _empty_frame()

    df["user_message"] = df["user_message"].astype(str).fillna("")

    # Include '+' so phone-number senders are parsed correctly
    df[["user", "message"]] = df["user_message"].str.extract(
        r"([\w\s\.\+\-]+?):\s(.*)", expand=True
    )

    df["user"] = df["user"].fillna("group_notification")
    df["message"] = df["message"].fillna(df["user_message"])
    df = df.drop(columns=["user_message"])

    df["only_date"] = df["date"].dt.date
    df["day_name"] = df["date"].dt.day_name()
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month_name()
    df["day"] = df["date"].dt.day
    df["hour"] = df["date"].dt.hour
    df["minute"] = df["date"].dt.minute
    df["period"] = df["hour"].apply(
        lambda h: f"{h}-00" if pd.isna(h) else (f"{int(h)}-00" if int(h) == 23 else f"{int(h)}-{int(h) + 1}")
    )
    return df


def _empty_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "date",
            "user",
            "message",
            "only_date",
            "day_name",
            "year",
            "month",
            "day",
            "hour",
            "minute",
            "period",
        ]
    )
