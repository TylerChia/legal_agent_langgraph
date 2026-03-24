"""
Notifications node - sends email and calendar invites
Enhanced with better error logging
"""
import os
import json
import resend
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
    print(f"📧 Attempting to send email to {user_email}")
    print(f"📄 Summary file: {summary_file}")
    print(f"📄 File exists: {os.path.exists(summary_file) if summary_file else 'N/A'}")
    
    if summary_file and os.path.exists(summary_file):
        try:
            email_result = send_summary_email(user_email, summary_file, company_name)
            results.append(email_result)
            print(f"✅ {email_result}")
        except Exception as e:
            error_msg = f"Email error: {str(e)}"
            results.append(error_msg)
            print(f"❌ {error_msg}")
            # Print full traceback for debugging
            import traceback
            traceback.print_exc()
    else:
        no_file_msg = "No summary file to send"
        results.append(no_file_msg)
        print(f"{no_file_msg}")
    
    # Send calendar invites (creator mode only)
    if mode == "creator" and calendar_file and os.path.exists(calendar_file):
        try:
            calendar_result = send_calendar_invites(user_email)
            results.append(calendar_result)
            print(f"✅ {calendar_result}")
        except Exception as e:
            error_msg = f"Calendar error: {str(e)}"
            results.append(error_msg)
            print(f"❌ {error_msg}")
    
    return {
        **state,
        "notification_results": results
    }


# def send_summary_email(recipient: str, summary_file: str, company_name: str = None) -> str:
#     """Send email with contract summary via SendGrid"""
#     print(f"📧 Starting SendGrid email send process...")

#     # Load credentials
#     sender_email = os.getenv("SENDER_EMAIL")
#     sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

#     print(f"📧 Sender email configured: {bool(sender_email)}")
#     print(f"📧 SendGrid API key configured: {bool(sendgrid_api_key)}")

#     if not sender_email or not sendgrid_api_key:
#         raise RuntimeError("Missing SendGrid credentials (SENDER_EMAIL or SENDGRID_API_KEY)")

#     # Read summary file
#     print(f"📧 Reading summary from: {summary_file}")
#     try:
#         with open(summary_file, "r", encoding="utf-8") as f:
#             summary_text = f.read()
#         print(f"📧 Summary length: {len(summary_text)} characters")
#     except Exception as e:
#         raise RuntimeError(f"Failed to read summary file: {str(e)}")

#     # Clean up markdown code blocks
#     summary_text = summary_text.strip()
#     if summary_text.startswith("```"):
#         summary_text = summary_text[summary_text.find("\n")+1:]
#     if summary_text.endswith("```"):
#         summary_text = summary_text[:summary_text.rfind("\n")]

#     # Subject line
#     today = datetime.now().strftime('%Y-%m-%d')
#     if company_name and company_name != "Unknown Company":
#         subject = f"Contract Summary - {today} - {company_name}"
#     else:
#         subject = f"Contract Summary - {today}"

#     print(f"📧 Email subject: {subject}")
#     print(f"📧 Recipient: {recipient}")

#     # Convert Markdown to HTML
#     html_body = markdown2.markdown(summary_text)

#     # Build SendGrid Mail object
#     message = Mail(
#         from_email=sender_email,
#         to_emails=recipient,
#         subject=subject,
#         html_content=html_body
#     )

#     # Send via SendGrid API
#     try:
#         print(f"📧 Sending via SendGrid API...")
#         sg = SendGridAPIClient(sendgrid_api_key)
#         response = sg.send(message)
#         print(f"📧 SendGrid response status: {response.status_code}")
#         if response.status_code not in [200, 202]:
#             raise RuntimeError(f"SendGrid API returned status {response.status_code}: {response.body}")
#         print(f"📧 Message sent successfully!")
#     except Exception as e:
#         raise RuntimeError(f"SendGrid error: {str(e)}")

#     return f"✅ Email sent to {recipient}"


def send_summary_email(recipient: str, summary_file: str, company_name: str = None) -> str:
    """Send email with contract summary via Resend"""
    print(f"📧 Starting email send process...")

    # Check credentials
    sender_email = os.getenv("SENDER_EMAIL")
    resend_api_key = os.getenv("RESEND_API_KEY")

    print(f"📧 Sender email configured: {bool(sender_email)}")
    print(f"📧 Resend API key configured: {bool(resend_api_key)}")

    if not sender_email or not resend_api_key:
        raise RuntimeError("Missing email credentials (SENDER_EMAIL or RESEND_API_KEY)")

    resend.api_key = resend_api_key

    # Read summary file
    print(f"📧 Reading summary from: {summary_file}")
    try:
        with open(summary_file, "r", encoding="utf-8") as f:
            summary_text = f.read()
        print(f"📧 Summary length: {len(summary_text)} characters")
    except Exception as e:
        raise RuntimeError(f"Failed to read summary file: {str(e)}")

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

    print(f"📧 Email subject: {subject}")
    print(f"📧 Recipient: {recipient}")

    # Convert Markdown to HTML
    html_body = markdown2.markdown(summary_text)

    # Send via Resend API
    print(f"📧 Sending via Resend API...")
    try:
        params = {
            "from": sender_email,
            "to": [recipient],
            "subject": subject,
            "html": html_body,
            "text": summary_text,
        }
        email = resend.Emails.send(params)
        print(f"📧 Resend response: {email}")
        print(f"📧 Message sent successfully!")
    except Exception as e:
        raise RuntimeError(f"Resend email error: {str(e)}")

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
        # Update the env var with refreshed token so it persists in-process
        refreshed_token = creds.to_json()
        os.environ['GOOGLE_CALENDAR_TOKEN_JSON'] = refreshed_token
        print(f"🔄 Google Calendar token refreshed. Update your GOOGLE_CALENDAR_TOKEN_JSON env var if needed.")

    if not creds.valid:
        return "Calendar authentication expired. Please re-authenticate."

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