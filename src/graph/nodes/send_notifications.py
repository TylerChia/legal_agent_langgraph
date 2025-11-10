"""
Notifications node - sends email and calendar invites
"""
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import markdown2
from datetime import datetime, timedelta
import pytz
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv
load_dotenv()

def send_notifications_node(state: dict) -> dict:
    """
    Send email summary and calendar invites
    """
    user_email = state["user_email"]
    summary_file = state.get("summary_file")
    calendar_file = state.get("calendar_file")
    company_name = state.get("company_name")
    mode = state["mode"]
    
    results = []
    
    # Send email summary with company name in subject
    if summary_file and os.path.exists(summary_file):
        try:
            email_result = send_summary_email(user_email, summary_file, company_name)
            results.append(email_result)
        except Exception as e:
            results.append(f"Email error: {str(e)}")
    
    # Send calendar invites (creator mode only)
    if mode == "creator" and calendar_file and os.path.exists(calendar_file):
        try:
            calendar_result = send_calendar_invites(user_email)
            results.append(calendar_result)
        except Exception as e:
            results.append(f"Calendar error: {str(e)}")
    
    return {
        **state,
        "notification_results": results
    }

def send_summary_email(recipient: str, summary_file: str, company_name: str = None) -> str:
    """Send email with contract summary"""
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    if not sender_email or not sender_password:
        raise RuntimeError("Missing email credentials")
    
    with open(summary_file, "r", encoding="utf-8") as f:
        summary_text = f.read()
    
    # Clean up any markdown code blocks
    summary_text = summary_text.strip()
    if summary_text.startswith("```"):
        summary_text = summary_text[summary_text.find("\n")+1:]
    if summary_text.endswith("```"):
        summary_text = summary_text[:summary_text.rfind("\n")]
    
    # Create subject line with company name
    today = datetime.now().strftime('%Y-%m-%d')
    if company_name and company_name != "Unknown Company":
        subject = f"Contract Summary - {today} - {company_name}"
    else:
        subject = f"Contract Summary - {today}"
    
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = recipient
    msg["Subject"] = subject
    
    html_body = markdown2.markdown(summary_text)
    plain_part = MIMEText(summary_text, "plain")
    html_part = MIMEText(html_body, "html")
    
    msg.attach(plain_part)
    msg.attach(html_part)
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)
    
    return f"✅ Email sent to {recipient}"

def send_calendar_invites(user_email: str) -> str:
    """Send calendar invites for deliverables"""
    if not os.path.exists('calendar_deliverables.json'):
        return "No deliverables found"
    
    with open('calendar_deliverables.json', 'r') as f:
        deliverables = json.load(f)
    
    if not deliverables:
        return "No deliverables to process"
    
    token_json_str = os.getenv('GOOGLE_CALENDAR_TOKEN_JSON')
    if not token_json_str:
        return "Calendar not configured"
    
    token_data = json.loads(token_json_str)
    creds = Credentials.from_authorized_user_info(
        token_data, 
        ['https://www.googleapis.com/auth/calendar']
    )
    
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    service = build('calendar', 'v3', credentials=creds)
    
    created_count = 0
    existing_count = 0
    
    for deliverable in deliverables:
        result = create_calendar_event(service, deliverable, user_email)
        if "created" in result.lower():
            created_count += 1
        elif "exists" in result.lower():
            existing_count += 1
    
    return f"📅 Calendar: {created_count} Events Created"

def create_calendar_event(service, deliverable: dict, user_email: str) -> str:
    """Create a single calendar event"""
    summary = deliverable.get('summary', '')
    description = deliverable.get('description', '')
    start_date = deliverable.get('start_date', '')
    start_time = deliverable.get('start_time')
    timezone_str = deliverable.get('timezone')
    
    if not all([summary, start_date]):
        return f"Skipped: {summary}"
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    pst = pytz.timezone('America/Los_Angeles')
    
    # Determine event type
    if start_time and start_time != 'null':
        time_obj = datetime.strptime(start_time, '%H:%M').time()
        combined_dt = datetime.combine(start_dt, time_obj)
        combined_dt = pst.localize(combined_dt)
        end_dt = combined_dt + timedelta(hours=1)
        
        event_times = {
            "start": {"dateTime": combined_dt.isoformat(), "timeZone": "America/Los_Angeles"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "America/Los_Angeles"},
        }
    else:
        event_times = {
            "start": {"date": start_dt.strftime('%Y-%m-%d')},
            "end": {"date": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d')},
        }
    
    event = {
        "summary": f"📋 {summary}",
        "description": f"Contract Deliverable\n\n{description}",
        "reminders": {"useDefault": True},
        "attendees": [{"email": user_email}],
        **event_times
    }
    
    try:
        service.events().insert(
            calendarId="primary",
            body=event,
            sendUpdates="all"
        ).execute()
        return f"Created: {summary}"
    except Exception as e:
        if "duplicate" in str(e).lower():
            return f"Exists: {summary}"
        return f"Error: {summary} - {str(e)}"