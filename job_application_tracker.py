import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
import re
import pandas as pd
from email.utils import parsedate_to_datetime

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def search_messages(service, query):
    result = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
    messages = []
    if 'messages' in result:
        messages.extend(result['messages'])
    return messages

def get_message_content(service, msg_id):
    message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    payload = message['payload']
    headers = payload['headers']
    subject = next(header['value'] for header in headers if header['name'] == 'Subject')
    date = next(header['value'] for header in headers if header['name'] == 'Date')
    
    ans = [];
    if 'parts' in payload:
        parts = payload['parts']
        if(parts[0]['body']['size'] > 0):
            data = parts[0]['body']['data']
            data = data.replace("-","+").replace("_","/")
            padding_length = 4 - (len(data) % 4)
            if padding_length < 4:
                encoded_string += '=' * padding_length
            decoded_data = base64.b64decode(data)
            decoded_string = decoded_data.decode('utf-8')
            print(subject)
            ans.append(list(filter(None, decoded_string.split('\n'))))
    
    return subject, date, ans

def extract_company_name(subject):
    # You may need to adjust this regex based on your email subjects
    match = re.search(r'(Application|Job) (?:for|at) (.+)', subject)
    if match:
        print(match.group(2).strip())
        return match.group(2).strip()
    return "Unknown Company"

def analyze_job_applications():
    service = get_gmail_service()
    
    # Search for job application emails
    application_query = "subject:(Application OR applied OR job OR congratulations OR Workday OR your application)"
    application_messages = search_messages(service, application_query)
    
    # print(application_messages)

    job_data = []
    
    for msg in application_messages:
        (subject, date, ans) = get_message_content(service, msg['id'])
        company = extract_company_name(subject)
    #     applied_date = date
        
    #     # Determine status based on email content
    #     if "reject" in subject.lower() or "reject" in content.lower():
    #         status = "Rejected"
    #     elif "offer" in subject.lower() or "offer" in content.lower():
    #         status = "Accepted"
    #     else:
    #         status = "Applied"
        
    #     job_data.append({
    #         "Company": company,
    #         "Applied Date": applied_date.strftime("%Y-%m-%d"),
    #         "Status": status
    #     })
    
    # df = pd.DataFrame(job_data)
    # df.to_csv("job_application_status.csv", index=False)
    print("Job application status has been saved to 'job_application_status.csv'")

if __name__ == '__main__':
    analyze_job_applications()