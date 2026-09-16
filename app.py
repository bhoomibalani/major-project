import matplotlib.pyplot as plt
import streamlit as st
import preprocessor, helper
import seaborn as sns
import altair as alt

st.set_page_config(layout="wide")
st.sidebar.title("WABRA Chat Analyzer")
uploaded_file = st.sidebar.file_uploader("Choose a File")

if uploaded_file:
    raw_bytes = uploaded_file.getvalue()
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raw_text = raw_bytes.decode("utf-16")

    df = preprocessor.preprocess(raw_text)

    if df.empty:
        st.error(
            "Could not parse any messages from this file. "
            "Export the chat from WhatsApp as a .txt file "
            "(without media) and try again."
        )
        st.code("\n".join(raw_text.splitlines()[:5]) or "(empty file)", language="text")
    else:
        user_list = df["user"].unique().tolist()
        if "group_notification" in user_list:
            user_list.remove("group_notification")
        user_list.sort()
        user_list.insert(0, "Overall")

        selected_user = st.sidebar.selectbox("Show Analysis of:", user_list)

        if st.sidebar.button("Show Analysis"):
            num_messages, words, num_media, links = helper.fetch_stats(selected_user, df)

            st.title("Top Statistics")
            stats = [
                ("Total Messages", num_messages),
                ("Total Words", words),
                ("Media Shared", num_media),
                ("Links Shared", links),
            ]
            for stat in stats:
                st.metric(stat[0], stat[1])

            if selected_user == "Overall":
                st.title("Most Active Users")
                x, df_per = helper.most_busy_user(df)
                st.bar_chart(x)
                st.dataframe(df_per)

            st.title("Word Cloud & Most Common Words")
            df_wc = helper.create_wordcloud(selected_user, df)
            if df_wc is None:
                st.info("Not enough text messages to generate a word cloud.")
            else:
                st.image(
                    df_wc.to_image(),
                    caption="Word Cloud",
                    use_container_width=True,
                )

            most_common_df = helper.most_common_words(selected_user, df)
            if most_common_df.empty:
                st.info("No common words found for this selection.")
            else:
                st.bar_chart(most_common_df.set_index(0))

            st.title("Emoji Analysis")
            emoji_df = helper.emoji_helper(selected_user, df)
            if emoji_df.empty:
                st.info("No emojis found for this selection.")
            else:
                emoji_df.columns = ["Emoji", "Count"]
                st.dataframe(emoji_df)
                pie_chart = (
                    alt.Chart(emoji_df)
                    .mark_arc()
                    .encode(
                        theta=alt.Theta(field="Count", type="quantitative"),
                        color=alt.Color(field="Emoji", type="nominal"),
                        tooltip=["Emoji", "Count"],
                    )
                    .properties(width=400, height=400)
                )
                st.altair_chart(pie_chart, use_container_width=True)

            st.title("Timeline Analysis")
            timeline = helper.monthly_timeline(selected_user, df)
            if timeline.empty:
                st.info("No timeline data available.")
            else:
                st.line_chart(timeline.set_index("time")["message"])

            st.title("Activity Map")
            week_activity = helper.week_activity_map(selected_user, df)
            month_activity = helper.month_activity_map(selected_user, df)
            if week_activity.empty:
                st.info("No activity data available.")
            else:
                st.bar_chart(week_activity)
                st.bar_chart(month_activity)

            st.title("Weekly Activity Heatmap")
            user_heatmap = helper.activity_heatmap(selected_user, df)
            if user_heatmap.empty:
                st.info("No heatmap data available.")
            else:
                sns.heatmap(user_heatmap, ax=plt.gca())
                st.pyplot(plt.gcf())