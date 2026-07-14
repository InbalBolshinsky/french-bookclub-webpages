import os
import time
import urllib.parse
from playwright.sync_api import sync_playwright

def load_members(file_path="members.txt"):
    members = []
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and "," in stripped:
                num, name = stripped.split(",", 1)
                members.append({"number": num.strip(), "name": name.strip()})
    return members

def load_template(file_path="message_template.txt"):
    if not os.path.exists(file_path):
        print(f"Error: Template file '{file_path}' not found.")
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def main():
    members = load_members()
    template = load_template()
    
    if not members:
        print("No members found in members.txt.")
        return
    if not template:
        print("Could not load message template.")
        return

    print(f"Loaded {len(members)} members and template successfully.")
    print("Starting browser... Please watch the browser window.")

    with sync_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "whatsapp_session")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir, 
            headless=False,
            args=[
                "--start-maximized",
                "--disable-notifications"
            ]
        )
        
        page = context.new_page()
        page.goto("https://web.whatsapp.com")
        
        print("\n👉 If you see any pop-up (like 'Continue' or 'Scan QR'), please handle it in the browser.")
        
        try:
            print("Waiting for WhatsApp Web to load...")
            page.wait_for_selector('#pane-side', timeout=25000)
            print("Successfully logged in!")
        except Exception:
            print("\n⚠️ Couldn't detect the chat list automatically, but proceeding assuming you are logged in.")
            time.sleep(5)

        # Start sending messages
        for index, member in enumerate(members):
            phone = member["number"]
            name = member["name"]
            
            personalized_message = template.format(name=name)
            encoded_message = urllib.parse.quote(personalized_message)
            
            # The URL automatically inserts the text into the WhatsApp text area
            whatsapp_url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_message}"
            
            print(f"[{index + 1}/{len(members)}] Opening chat for {name} (+{phone})...")
            page.goto(whatsapp_url)
            
            try:
                # Instead of waiting for the Send button, we wait for the text input box 
                # (which confirms the chat has fully loaded and the text is ready inside it)
                input_box_selector = 'div[contenteditable="true"][data-tab="10"]'
                page.wait_for_selector(input_box_selector, timeout=25000)
                
                # Human delay to ensure everything is rendered
                time.sleep(2)
                
                # Press Enter inside the input box to send the message!
                page.press(input_box_selector, "Enter")
                print(f"✅ Successfully sent to {name}!")
                
                # Spam protection delay
                time.sleep(4)
                
            except Exception as e:
                print(f"❌ Failed to send to {name} (+{phone}). The page might have timed out loading.")
                time.sleep(2)

        print("\n🎉 All messages sent! You can close the browser now.")
        context.close()

if __name__ == "__main__":
    main()