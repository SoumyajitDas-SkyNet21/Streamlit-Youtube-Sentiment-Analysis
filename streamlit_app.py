import streamlit as st
from googleapiclient.discovery import build
import re
import emoji
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# Initialize YouTube API
API_KEY = 'AIzaSyAKylkn9ANwkb2gA1q8MEVpMrs_a_UbHJY'
youtube = build('youtube', 'v3', developerKey=API_KEY)

# Function to fetch YouTube comments
def fetch_comments(video_id):
    """
    Fetches comments from a YouTube video using the YouTube API.
    """
    comments = []
    nextPageToken = None
    while len(comments) < 600:
        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=100,
            pageToken=nextPageToken
        )
        response = request.execute()
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            comments.append(comment['textDisplay'])
        nextPageToken = response.get('nextPageToken')
        if not nextPageToken:
            break
    return comments

# Function to analyze sentiment
def sentiment_scores(comment):
    """
    Calculates the sentiment polarity of a comment.
    """
    sentiment_analyzer = SentimentIntensityAnalyzer()
    sentiment_dict = sentiment_analyzer.polarity_scores(comment)
    return sentiment_dict['compound']

# Function to display sentiment distribution bar chart
def display_bar_chart(labels, counts):
    fig, ax = plt.subplots()
    ax.bar(labels, counts, color=['#76c7c0', '#f76c6c', '#ffcc5c'])
    ax.set_title('Sentiment Distribution')
    ax.set_xlabel('Sentiments')
    ax.set_ylabel('Number of Comments')
    st.pyplot(fig)

# Function to display sentiment distribution pie chart
def display_pie_chart(labels, counts):
    fig, ax = plt.subplots()
    ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#8fd175', '#f76c6c', '#ffd700'])
    ax.set_title('Sentiment Distribution (Pie Chart)')
    st.pyplot(fig)

# Function to display sentiment distribution donut chart
def display_donut_chart(labels, counts):
    fig, ax = plt.subplots()
    ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=90, wedgeprops={'width': 0.4}, colors=['#76c7c0', '#f76c6c', '#ffcc5c'])
    ax.set_title('Sentiment Distribution (Donut Chart)')
    st.pyplot(fig)

# Function to display word cloud
def display_word_cloud(comments):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(' '.join(comments))
    st.image(wordcloud.to_array(), use_column_width=True)

# Streamlit interface
st.title('YouTube Comment Sentiment Analysis')

# Input field and button for analysis
video_url = st.text_input('Enter YouTube Video URL')
if st.button('Analyze'):
    if video_url:
        # Extract video ID from URL
        video_id = video_url[-11:]
        st.write("Analyzing comments...")

        # Fetch comments
        comments = fetch_comments(video_id)

        # Filter relevant comments
        relevant_comments = []
        threshold_ratio = 0.75
        hyperlink_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

        for comment_text in comments:
            comment_text = comment_text.lower().strip()
            if hyperlink_pattern.search(comment_text):
                continue
            emojis_count = emoji.emoji_count(comment_text)
            text_characters = len(re.sub(r'\s', '', comment_text))
            if any(char.isalnum() for char in comment_text):
                if emojis_count == 0 or (text_characters / (text_characters + emojis_count)) > threshold_ratio:
                    relevant_comments.append(comment_text)

        # Analyze sentiments
        positive_comments, negative_comments, neutral_comments = [], [], []
        polarity = []

        for comment in relevant_comments:
            score = sentiment_scores(comment)
            polarity.append(score)
            if score > 0.05:
                positive_comments.append(comment)
            elif score < -0.05:
                negative_comments.append(comment)
            else:
                neutral_comments.append(comment)

        # Display sentiment distribution
        labels = ['Positive', 'Negative', 'Neutral']
        counts = [len(positive_comments), len(negative_comments), len(neutral_comments)]

        display_bar_chart(labels, counts)
        display_pie_chart(labels, counts)
        display_donut_chart(labels, counts)

        # Display word cloud
        display_word_cloud(relevant_comments)

        # Display average polarity
        avg_polarity = sum(polarity) / len(polarity)
        st.write(f"Average Polarity: {avg_polarity:.2f}")
        if avg_polarity > 0.05:
            st.write("The video has a Positive response.")
        elif avg_polarity < -0.05:
            st.write("The video has a Negative response.")
        else:
            st.write("The video has a Neutral response.")
    else:
        st.write("Please enter a valid YouTube URL.")
