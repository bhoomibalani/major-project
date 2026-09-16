import pandas as pd
from collections import Counter
from urlextract import URLExtract
from wordcloud import WordCloud
import emoji

ext = URLExtract()


def fetch_stats(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user.replace("\n", " ")]

    # Convert non-string messages to strings to avoid errors
    df = df.copy()
    df["message"] = df["message"].astype(str).str.strip()

    # Total number of messages
    num_messages = df.shape[0]

    # Total number of words
    words = sum(len(message.split()) for message in df["message"])

    # Total number of media messages
    num_media = df[df["message"] == "<Media omitted>"].shape[0]

    # Total number of links
    links = []
    for message in df["message"]:
        links.extend(
            ext.find_urls(str(message))
        )  # Ensuring each message is treated as a string

    return num_messages, words, num_media, len(links)


def most_busy_user(df):
    x = df["user"].value_counts().head()
    df_per = (
        (df["user"].value_counts(normalize=True) * 100)
        .round(2)
        .reset_index()
        .rename(columns={"index": "Name", "user": "Percentage"})
    )
    return x, df_per


def create_wordcloud(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user.replace("\n", " ")]

    messages = (
        df["message"]
        .astype(str)
        .str.strip()
        .loc[lambda s: ~s.isin(["<Media omitted>", "This message was deleted", "nan", ""])]
    )
    text = " ".join(messages)
    if not text.strip():
        return None

    return WordCloud(width=500, height=500, background_color="white").generate(text)


def most_common_words(selected_user, df):
    with open("stop_hinglish.txt", "r") as f:
        stop_words = set(f.read().split())

    if selected_user != "Overall":
        df = df[df["user"] == selected_user.replace("\n", " ")]

    words = [
        word
        for message in df["message"].astype(str).str.strip()
        if message not in ("<Media omitted>", "This message was deleted", "nan", "")
        for word in message.lower().split()
        if word not in stop_words
    ]
    return pd.DataFrame(Counter(words).most_common(20))


def emoji_helper(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user.replace("\n", " ")]

    emojis = [
        char
        for message in df["message"]
        for char in message
        if char in emoji.EMOJI_DATA
    ]
    return pd.DataFrame(Counter(emojis).most_common())


def monthly_timeline(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user.replace("\n", " ")]

    timeline = df.groupby(["year", "month"]).count()["message"].reset_index()
    timeline["time"] = (
        timeline["month"].astype(str) + "-" + timeline["year"].astype(str)
    )
    return timeline


def week_activity_map(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user.replace("\n", " ")]
    return df["day_name"].value_counts()


def month_activity_map(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user.replace("\n", " ")]
    return df["month"].value_counts()


def activity_heatmap(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user.replace("\n", " ")]
    return df.pivot_table(
        index="day_name", columns="period", values="message", aggfunc="count"
    ).fillna(0)
