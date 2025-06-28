"""
Gmail Integration - Email parsing and Google Alerts processing
"""
import os
import imaplib
import email
import re
import html
import urllib.parse
import logging
from datetime import datetime
from email.header import decode_header

logger = logging.getLogger(__name__)


class GmailPoller:
    def __init__(self):
        self.imap_server = "imap.gmail.com"
        self.email_user = os.getenv("GMAIL_USER")
        self.email_password = os.getenv("GMAIL_APP_PASSWORD")  # Use App Password for security

    def connect_to_gmail(self):
        """Connect to Gmail via IMAP"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_user, self.email_password)
            logger.info("Successfully connected to Gmail")
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to Gmail: {e}")
            return None

    def get_google_alerts(self):
        """Fetch unread Google Alerts from Gmail"""
        mail = self.connect_to_gmail()
        if not mail:
            return []

        try:
            mail.select("inbox")

            # Search for unread emails from Google Alerts
            status, messages = mail.search(None, 'UNSEEN FROM "googlealerts-noreply@google.com"')

            if status != "OK":
                logger.error("Failed to search emails")
                return []

            alerts = []
            message_ids = messages[0].split()

            for msg_id in message_ids:
                try:
                    status, msg_data = mail.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue

                    # Parse email
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)

                    # Extract content
                    alert_data = self.parse_google_alert(email_message)
                    if alert_data:
                        alerts.append(alert_data)

                except Exception as e:
                    logger.error(f"Error processing email {msg_id}: {e}")

            mail.close()
            mail.logout()
            logger.info(f"Found {len(alerts)} Google Alerts")
            return alerts

        except Exception as e:
            logger.error(f"Error fetching Google Alerts: {e}")
            return []

    def parse_google_alert(self, email_message):
        """Parse Google Alert email to extract title, summary, and article snippet"""
        try:
            # Get subject
            subject = decode_header(email_message["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()

            # Extract the search term from subject (format: "Google Alert - YOUR_SEARCH_TERM")
            search_term = re.search(r"Google Alert - (.+)", subject)
            search_term = search_term.group(1) if search_term else "Unknown"

            # Get email body
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/html":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = email_message.get_payload(decode=True).decode()

            # Extract articles from HTML body
            articles = self.extract_articles_from_html(body)

            return {
                "search_term": search_term,
                "timestamp": datetime.now().isoformat(),
                "articles": articles,
            }

        except Exception as e:
            logger.error(f"Error parsing Google Alert: {e}")
            return None

    def extract_articles_from_html(self, html_body):
        """Extract article titles, links, and snippets from Google Alert HTML"""
        # Debug: Save the HTML to see what we're working with
        logger.info("📧 DEBUG: Analyzing email HTML structure...")

        # Write HTML to file for debugging
        with open("debug_email.html", "w", encoding="utf-8") as f:
            f.write(html_body)
        logger.info("📧 HTML saved to debug_email.html for inspection")

        articles = []

        # Updated regex patterns for current Google Alert structure
        # Look for article titles in the itemprop="name" spans
        title_link_pattern = (
            r'<a href="([^"]*)" itemprop="url"[^>]*>.*?<span itemprop="name"[^>]*>(.*?)</span>'
        )
        description_pattern = r'<div itemprop="description"[^>]*>(.*?)</div>'

        # Find title links and descriptions
        title_links = re.findall(title_link_pattern, html_body, re.DOTALL)
        descriptions = re.findall(description_pattern, html_body, re.DOTALL)

        logger.info(f"📧 Found {len(title_links)} articles with {len(descriptions)} descriptions")

        # Process the extracted articles
        for i, (link, title_html) in enumerate(title_links):
            # Clean up the title (remove HTML tags and decode)
            title = re.sub(r"<[^>]+>", "", title_html).strip()

            # Decode HTML entities properly
            title = html.unescape(title)

            # Get corresponding description
            description = ""
            if i < len(descriptions):
                description = re.sub(r"<[^>]+>", "", descriptions[i]).strip()
                description = html.unescape(description)

            logger.info(f"📧 Extracted article: '{title}' -> {description[:100]}...")

            # Skip obvious UI elements
            if len(title) < 10 or "flag as irrelevant" in title.lower():
                continue

            # Clean Google redirect URLs
            cleaned_link = self.clean_google_redirect_url(link)
            logger.debug(f"🔗 Cleaned: {cleaned_link}")

            articles.append({"title": title, "link": cleaned_link, "snippet": description})

        logger.info(f"📧 Extracted {len(articles)} valid articles after filtering")
        for i, article in enumerate(articles):
            logger.info(f"📧 Article {i+1}: '{article['title'][:80]}...'")

        return articles

    def clean_google_redirect_url(self, url):
        """Extract the actual URL from Google's redirect URL"""
        if "google.com/url" in url:
            try:
                # First decode HTML entities like &amp;
                url = html.unescape(url)

                # Parse the URL parameters
                parsed = urllib.parse.urlparse(url)
                params = urllib.parse.parse_qs(parsed.query)

                # Extract the actual URL from the 'url' parameter
                if "url" in params:
                    actual_url = params["url"][0]
                    logger.debug(f"🔗 Cleaned Google redirect: {actual_url[:100]}...")
                    return actual_url
            except Exception as e:
                logger.warning(f"⚠️ Error cleaning Google URL: {e}")

        return url
