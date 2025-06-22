"""
Gmail Organizer for MarketMan
Automatically moves read MarketMan alerts to a dedicated folder to keep inbox clean
"""

import os
import pickle
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging

logger = logging.getLogger(__name__)

class GmailOrganizer:
    """Organize Gmail messages for MarketMan"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(self, credentials_file=None, token_file=None):
        self.credentials_file = credentials_file or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config", "gmail_credentials.json"
        )
        self.token_file = token_file or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config", "gmail_token.pickle"
        )
        self.service = None
        self.marketman_label_id = None
    
    def authenticate(self):
        """Authenticate with Gmail API"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"❌ Gmail credentials file not found: {self.credentials_file}")
                    print("📝 To set up Gmail integration:")
                    print("1. Go to Google Cloud Console")
                    print("2. Enable Gmail API")
                    print("3. Download credentials.json")
                    print(f"4. Save as {self.credentials_file}")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        return True
    
    def get_or_create_marketman_label(self) -> Optional[str]:
        """Get or create the MarketMan label/folder"""
        if not self.service:
            return None
        
        try:
            # Check if MarketMan label exists
            labels = self.service.users().labels().list(userId='me').execute()
            
            for label in labels.get('labels', []):
                if label['name'].lower() == 'marketman':
                    self.marketman_label_id = label['id']
                    logger.info(f"Found existing MarketMan label: {label['id']}")
                    return label['id']
            
            # Create MarketMan label
            label_object = {
                'name': 'MarketMan',
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show',
                'color': {
                    'textColor': '#ffffff',
                    'backgroundColor': '#2da2bb'  # Nice blue color
                }
            }
            
            created_label = self.service.users().labels().create(
                userId='me', body=label_object).execute()
            
            self.marketman_label_id = created_label['id']
            logger.info(f"Created MarketMan label: {created_label['id']}")
            return created_label['id']
            
        except HttpError as error:
            logger.error(f"Error managing MarketMan label: {error}")
            return None
    
    def find_marketman_messages(self, days_back: int = 7, read_only: bool = True) -> List[Dict]:
        """Find MarketMan-related messages"""
        if not self.service:
            return []
        
        try:
            # Build search query - just Google Alerts emails
            base_query = 'from:googlealerts-noreply@google.com'
            
            query_parts = [base_query]
            
            if read_only:
                query_parts.append('is:read')
            
            # Date filter
            date_filter = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            query_parts.append(f'after:{date_filter}')
            
            query = ' '.join(query_parts)
            
            logger.info(f"Searching Gmail with query: {query}")
            
            # Search for messages
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=100).execute()
            
            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} Google Alerts messages")
            
            # Get message details for all messages (not just first 50)
            detailed_messages = []
            for i, message in enumerate(messages):
                try:
                    if i > 0 and i % 10 == 0:  # Progress indicator
                        logger.info(f"Processing message {i+1}/{len(messages)}")
                    
                    msg_detail = self.service.users().messages().get(
                        userId='me', id=message['id']).execute()
                    detailed_messages.append({
                        'id': message['id'],
                        'threadId': msg_detail.get('threadId'),
                        'labels': msg_detail.get('labelIds', []),
                        'snippet': msg_detail.get('snippet', ''),
                        'payload': msg_detail.get('payload', {})
                    })
                except HttpError as error:
                    logger.warning(f"Error getting message {message['id']}: {error}")
                    continue
            
            logger.info(f"Successfully processed {len(detailed_messages)} messages")
            
            return detailed_messages
            
        except HttpError as error:
            logger.error(f"Error searching messages: {error}")
            return []
    
    def move_messages_to_marketman(self, message_ids: List[str]) -> Dict[str, bool]:
        """Move messages to MarketMan label and remove from inbox"""
        if not self.service or not self.marketman_label_id:
            logger.error("Gmail service or MarketMan label not initialized")
            return {}
        
        if not message_ids:
            return {}
        
        results = {}
        
        for msg_id in message_ids:
            try:
                # Add MarketMan label and remove INBOX label
                self.service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body={
                        'addLabelIds': [self.marketman_label_id],
                        'removeLabelIds': ['INBOX']
                    }
                ).execute()
                
                results[msg_id] = True
                logger.debug(f"Moved message {msg_id} to MarketMan folder")
                
            except HttpError as error:
                logger.error(f"Error moving message {msg_id}: {error}")
                results[msg_id] = False
        
        success_count = sum(1 for success in results.values() if success)
        logger.info(f"Successfully moved {success_count}/{len(message_ids)} messages to MarketMan folder")
        
        return results
    
    def organize_marketman_emails(self, days_back: int = 7, dry_run: bool = False) -> Dict:
        """Main function to organize MarketMan emails"""
        logger.info(f"🗂️  Organizing MarketMan emails (last {days_back} days)")
        
        if not self.authenticate():
            return {'error': 'Authentication failed'}
        
        if not self.get_or_create_marketman_label():
            return {'error': 'Could not create/find MarketMan label'}
        
        # Find Google Alerts messages
        messages = self.find_marketman_messages(days_back=days_back, read_only=True)
        
        # Filter out messages already in MarketMan folder
        inbox_messages = [
            msg for msg in messages 
            if 'INBOX' in msg.get('labels', []) and 
               self.marketman_label_id not in msg.get('labels', [])
        ]
        
        logger.info(f"Found {len(inbox_messages)} read Google Alerts messages in inbox to organize")
        
        if not inbox_messages:
            return {
                'total_found': len(messages),
                'inbox_messages': len(inbox_messages),
                'moved': 0,
                'message': 'No messages to organize'
            }
        
        if dry_run:
            logger.info("🧪 DRY RUN - Would move these messages:")
            for msg in inbox_messages[:5]:  # Show first 5
                logger.info(f"  • {msg['snippet'][:60]}...")
            if len(inbox_messages) > 5:
                logger.info(f"  • ... and {len(inbox_messages)-5} more")
            
            return {
                'total_found': len(messages),
                'inbox_messages': len(inbox_messages),
                'moved': 0,
                'dry_run': True,
                'message': f'Would move {len(inbox_messages)} messages'
            }
        
        # Move messages
        message_ids = [msg['id'] for msg in inbox_messages]
        move_results = self.move_messages_to_marketman(message_ids)
        
        success_count = sum(1 for success in move_results.values() if success)
        
        return {
            'total_found': len(messages),
            'inbox_messages': len(inbox_messages),
            'moved': success_count,
            'failed': len(move_results) - success_count,
            'message': f'Moved {success_count} Google Alerts to MarketMan folder'
        }

    def undo_marketman_organization(self) -> Dict:
        """Move all emails back from MarketMan folder to inbox"""
        logger.info("🔄 Moving emails back from MarketMan folder to inbox...")
        
        if not self.authenticate():
            return {'error': 'Authentication failed'}
        
        if not self.get_or_create_marketman_label():
            return {'error': 'Could not find MarketMan label'}
        
        try:
            # Find all messages in MarketMan folder
            results = self.service.users().messages().list(
                userId='me', 
                labelIds=[self.marketman_label_id],
                maxResults=500
            ).execute()
            
            marketman_messages = results.get('messages', [])
            logger.info(f"Found {len(marketman_messages)} messages in MarketMan folder")
            
            if not marketman_messages:
                return {
                    'moved': 0,
                    'message': 'No messages found in MarketMan folder'
                }
            
            # Move messages back to inbox
            move_results = {}
            for message in marketman_messages:
                try:
                    # Remove MarketMan label and add INBOX label
                    self.service.users().messages().modify(
                        userId='me',
                        id=message['id'],
                        body={
                            'removeLabelIds': [self.marketman_label_id],
                            'addLabelIds': ['INBOX']
                        }
                    ).execute()
                    
                    move_results[message['id']] = True
                    
                except HttpError as error:
                    logger.error(f"Error moving message {message['id']}: {error}")
                    move_results[message['id']] = False
            
            success_count = sum(1 for success in move_results.values() if success)
            
            return {
                'moved': success_count,
                'failed': len(move_results) - success_count,
                'message': f'Moved {success_count} messages back to inbox'
            }
            
        except HttpError as error:
            logger.error(f"Error undoing organization: {error}")
            return {'error': str(error)}

    def test_google_alerts_search(self) -> Dict:
        """Test if we can find Google Alerts emails"""
        logger.info("🧪 Testing Google Alerts search...")
        
        if not self.authenticate():
            return {'error': 'Authentication failed'}
        
        try:
            # Search for any Google Alerts in last 30 days
            date_filter = (datetime.now() - timedelta(days=30)).strftime('%Y/%m/%d')
            
            # All Google Alerts
            all_alerts_query = f'from:googlealerts-noreply@google.com after:{date_filter}'
            all_results = self.service.users().messages().list(
                userId='me', q=all_alerts_query, maxResults=100).execute()
            all_alerts = all_results.get('messages', [])
            
            return {
                'total_alerts': len(all_alerts),
                'message': f'Found {len(all_alerts)} Google Alerts total'
            }
            
        except HttpError as error:
            logger.error(f"Error testing Google Alerts: {error}")
            return {'error': str(error)}


def main():
    """CLI interface for Gmail organizer"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Organize MarketMan Gmail messages")
    parser.add_argument("--days", type=int, default=7, help="Days back to search (default: 7)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without doing it")
    parser.add_argument("--setup", action="store_true", help="Set up Gmail integration")
    
    args = parser.parse_args()
    
    organizer = GmailOrganizer()
    
    if args.setup:
        print("🚀 Setting up Gmail integration...")
        print("📝 You'll need to:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 credentials (Desktop application)")
        print("5. Download the JSON file")
        print(f"6. Save it as: {organizer.credentials_file}")
        print("\nThen run this command again without --setup")
        return
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run organizer
    result = organizer.organize_marketman_emails(
        days_back=args.days,
        dry_run=args.dry_run
    )
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        sys.exit(1)
    
    print(f"✅ {result['message']}")
    print(f"📊 Found {result['total_found']} total MarketMan messages")
    print(f"📥 {result['inbox_messages']} were in inbox")
    if result.get('moved', 0) > 0:
        print(f"🗂️  Moved {result['moved']} to MarketMan folder")
    if result.get('failed', 0) > 0:
        print(f"❌ Failed to move {result['failed']} messages")


if __name__ == "__main__":
    main()
