import praw
import smtplib
from email.mime.text import MIMEText
import os
import time

# Reddit API credentials (replace with your own or use environment variables)
REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID', 'YOUR_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET', 'YOUR_CLIENT_SECRET')
REDDIT_USER_AGENT = os.environ.get('REDDIT_USER_AGENT', 'YOUR_USER_AGENT')

# Email configuration
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', 'your_email@gmail.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'your_email_password')
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL', 'recipient@example.com')

# Slack webhook URL (replace with your own or use environment variables)
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', 'YOUR_SLACK_WEBHOOK_URL')

# Brand keywords to track
BRAND_KEYWORDS = ['your_brand_name', 'another_keyword']

# Subreddits to monitor
SUBREDDITS = ['all'] # Monitor all subreddits, or specify like ['technology', 'gadgets']

# How often to check for new posts (in seconds)
CHECK_INTERVAL = 60 * 5 # 5 minutes

# Keep track of processed post IDs to avoid duplicates
processed_posts = set()

def send_slack_alert(message):
    """Sends an alert to Slack."""
    if not SLACK_WEBHOOK_URL or SLACK_WEBHOOK_URL == 'YOUR_SLACK_WEBHOOK_URL':
        print("Slack webhook URL not configured. Skipping Slack alert.")
        return

    import requests
    payload = {"text": message}
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status() # Raise an exception for bad status codes
        print("Slack alert sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Slack alert: {e}")

def send_email_alert(subject, body):
    """Sends an alert via email."""
    if not SMTP_USERNAME or SMTP_USERNAME == 'your_email@gmail.com':
        print("Email credentials not configured. Skipping email alert.")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = RECIPIENT_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls() # Secure the connection
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, RECIPIENT_EMAIL, msg.as_string())
        print("Email alert sent successfully.")
    except Exception as e:
        print(f"Error sending email alert: {e}")

def monitor_reddit():
    """Monitors Reddit for brand mentions and sends alerts."""
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )

    subreddit_str = ",".join(SUBREDDITS)
    print(f"Monitoring subreddits: {subreddit_str} for keywords: {', '.join(BRAND_KEYWORDS)}")

    while True:
        try:
            for subreddit_name in SUBREDDITS:
                subreddit = reddit.subreddit(subreddit_name)
                # Check new posts
                for submission in subreddit.new(limit=25):
                    if submission.id not in processed_posts:
                        post_content = (submission.title + " " + submission.selftext).lower()
                        for keyword in BRAND_KEYWORDS:
                            if keyword.lower() in post_content:
                                print(f"Found mention of '{keyword}' in post: {submission.title}")
                                # Construct alert message
                                alert_subject = f"Reddit Brand Mention: {keyword} - {submission.title[:50]}..."
                                alert_body = f"A new post on Reddit mentions '{keyword}':\n\nTitle: {submission.title}\nURL: {submission.url}\nAuthor: {submission.author}\nSubreddit: r/{submission.subreddit}\n\nContent:\n{submission.selftext[:500]}..."

                                # Send alerts
                                send_slack_alert(f"🚨 *Reddit Alert* 🚨\nKeyword: `{keyword}`\nTitle: `{submission.title}`\nLink: {submission.url}")
                                send_email_alert(alert_subject, alert_body)

                                processed_posts.add(submission.id)
                                break # Move to next submission once a keyword is found

            print(f"Waiting for {CHECK_INTERVAL} seconds before next check...")
            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print(f"An error occurred: {e}")
            print("Retrying after a short delay...")
            time.sleep(60) # Wait a minute before retrying after an error

if __name__ == "__main__":
    # Basic check for essential credentials
    if REDDIT_CLIENT_ID == 'YOUR_CLIENT_ID' or REDDIT_CLIENT_SECRET == 'YOUR_CLIENT_SECRET' or REDDIT_USER_AGENT == 'YOUR_USER_AGENT':
        print("ERROR: Please configure your Reddit API credentials (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT) or set them as environment variables.")
    elif SMTP_USERNAME == 'your_email@gmail.com' or SMTP_PASSWORD == 'your_email_password':
        print("WARNING: Email alerts are configured but email credentials (SMTP_USERNAME, SMTP_PASSWORD) are not set. Email alerts will be skipped.")
    elif SLACK_WEBHOOK_URL == 'YOUR_SLACK_WEBHOOK_URL':
        print("WARNING: Slack alerts are configured but SLACK_WEBHOOK_URL is not set. Slack alerts will be skipped.")
    else:
        monitor_reddit()
