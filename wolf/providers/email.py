"""
Email provider for Wolf CLI.
"""

import os
import platform
import mailbox

def find_thunderbird_profile():
    """
    Find the Thunderbird profile directory.
    """
    if platform.system() == "Windows":
        app_data = os.environ.get("APPDATA")
        if not app_data:
            return None
        thunderbird_path = os.path.join(app_data, "Thunderbird", "Profiles")
    elif platform.system() == "Darwin":
        home = os.path.expanduser("~")
        thunderbird_path = os.path.join(home, "Library", "Thunderbird", "Profiles")
    else: # Linux
        home = os.path.expanduser("~")
        thunderbird_path = os.path.join(home, ".thunderbird")

    if not os.path.exists(thunderbird_path):
        return None

    for item in os.listdir(thunderbird_path):
        if item.endswith(".default"):
            return os.path.join(thunderbird_path, item)
    
    # Fallback if no .default profile is found
    profiles = [d for d in os.listdir(thunderbird_path) if os.path.isdir(os.path.join(thunderbird_path, d))]
    if profiles:
        return os.path.join(thunderbird_path, profiles[0])

    return None

def list_mailboxes():
    """
    List available mailboxes (MBOX files) in the Thunderbird profile.
    """
    profile_path = find_thunderbird_profile()
    print(f"DEBUG: Thunderbird profile path: {profile_path}")
    if not profile_path:
        return {"error": "Thunderbird profile not found."}

    mail_locations = [
        os.path.join(profile_path, "ImapMail"),
        os.path.join(profile_path, "Mail")
    ]
    print(f"DEBUG: Mail locations: {mail_locations}")

    mailboxes = []
    for location in mail_locations:
        if os.path.exists(location):
            for root, dirs, files in os.walk(location):
                for file in files:
                    # MBOX files often have no extension, or sometimes .mbox
                    # We'll be a bit lenient here
                    if "." not in file or file.endswith(".mbox"):
                        # Get the relative path to the mail location
                        relative_path = os.path.relpath(os.path.join(root, file), location)
                        mailboxes.append(relative_path)
    
    return {"mailboxes": sorted(mailboxes)}

def read_mailbox(mailbox_name: str, count: int = 10):
    """
    Read emails from a specific mailbox.
    """
    profile_path = find_thunderbird_profile()
    if not profile_path:
        return {"error": "Thunderbird profile not found."}

    # Find the full path to the mailbox
    mailbox_path = None
    mail_locations = [
        os.path.join(profile_path, "ImapMail"),
        os.path.join(profile_path, "Mail")
    ]
    for location in mail_locations:
        path = os.path.join(location, mailbox_name)
        if os.path.exists(path):
            mailbox_path = path
            break
    
    if not mailbox_path:
        return {"error": f"Mailbox '{mailbox_name}' not found."}

    try:
        mbox = mailbox.mbox(mailbox_path)
        emails = []
        # Iterate over messages in reverse order to get the latest emails
        for i, message in reversed(list(enumerate(mbox))):
            if len(emails) >= count:
                break
            
            subject = message['subject']
            sender = message['from']
            date = message['date']
            
            emails.append({
                "id": i,
                "subject": subject,
                "from": sender,
                "date": date
            })
        
        return {"emails": emails}
    except Exception as e:
        return {"error": str(e)}
