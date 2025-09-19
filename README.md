
# AXEEEH TempMail Tool

A terminal-based temporary email tool (single-file).  
Generates disposable email addresses using the 1secmail API and provides a simple, colorful terminal UI for viewing and saving messages.

> **Repository:** https://github.com/dhanusshifu/tempmail.git

---

## Features
- Auto-installs required Python packages (if missing).
- Generate a disposable email address instantly.
- Show inbox with message count.
- Read messages by ID and optionally save to `messages/`.
- Copy email to clipboard (works with Termux and pyperclip).
- Single-file (`tempmail.py`) — easy to run.

---

## Installation & Run (Full Process)

1. **Clone the repository**
   ```bash
   git clone https://github.com/dhanusshifu/tempmail.git
   cd tempmail

2. Run the script directly

`python tempmail.py`

The script will check for missing Python packages and install them automatically on first run.

After installation, the program starts right away.





---

# How to Use (Step-by-Step Guide)

Once the tool is running, you will see a simple menu with numbered options:

1. Show Inbox

Displays a table of all emails currently in your inbox.

Includes ID, sender, and subject.



2. Read Message by ID

First, check the inbox to see the IDs of available messages.

Enter the ID to open the full message body.

After reading, you’ll be asked if you want to save it into the messages/ folder.



3. Change Email

Generates a brand-new disposable email address instantly.



4. Copy Email Address

Copies the current temp address to your clipboard.

On Termux, this uses termux-clipboard-set if available. Otherwise, it falls back to pyperclip.



5. Refresh Inbox

Reloads your inbox and shows any new messages since your last check.

If new mail has arrived, you’ll see a notification.



6. Quit

Exit the program cleanly.





---

# Termux Notes (Android)

For clipboard support inside Termux, install Termux API:

``` pkg install termux-api ```

The script will automatically use it when available.



---

# Example Workflow

→Run the tool.

→Copy your new disposable email.

→Use it to sign up for a site or service you want to test.

→ Come back to the tool and choose Refresh Inbox until the confirmation mail arrives.

→Read it with Read Message by ID.

→ Save it if you need a record.



---

# Important Notes

➢ Disposable mailboxes are public and temporary.

➢ Do not use them for important accounts (bank, school, personal).

➢ This tool is for testing, demos, and learning purposes only.



---
