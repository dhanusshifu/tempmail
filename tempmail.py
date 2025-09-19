#!/usr/bin/env python3
"""
AXEEEH TempMail (dual backend: 1secmail + mail.tm fallback)
"""

import sys, subprocess, importlib, time, os, shutil, random

# --- Auto install requirements ---
REQUIRED = ["requests", "rich", "pyfiglet", "pyperclip"]
for pkg in REQUIRED:
    try:
        importlib.import_module(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

import requests, pyfiglet, pyperclip
from rich.console import Console
from rich.table import Table

console = Console()

# ---------------------------
# Providers
# ---------------------------
class OneSecMail:
    BASE = "https://www.1secmail.com/api/v1/"

    def get_address(self):
        r = requests.get(self.BASE, params={"action":"genRandomMailbox","count":1}, timeout=8)
        r.raise_for_status()
        return r.json()[0]

    def list_messages(self, login, domain):
        r = requests.get(self.BASE, params={"action":"getMessages","login":login,"domain":domain}, timeout=8)
        r.raise_for_status()
        return r.json()

    def read_message(self, login, domain, msg_id):
        r = requests.get(self.BASE, params={"action":"readMessage","login":login,"domain":domain,"id":msg_id}, timeout=8)
        r.raise_for_status()
        return r.json()

class MailTM:
    BASE = "https://api.mail.tm"

    def __init__(self):
        self.token = None
        self.address = None
        self.password = None

    def get_address(self):
        # generate a random account
        import uuid
        self.address = f"{uuid.uuid4().hex[:10]}@mailsac.com"  # mail.tm uses its own domains but we'll let API decide
        self.password = uuid.uuid4().hex
        # create account
        acc = {"address": self.address, "password": self.password}
        requests.post(f"{self.BASE}/accounts", json=acc, timeout=10)
        # login
        resp = requests.post(f"{self.BASE}/token", json=acc, timeout=10)
        resp.raise_for_status()
        self.token = resp.json()["token"]
        return self.address

    def list_messages(self, login=None, domain=None):
        headers = {"Authorization": f"Bearer {self.token}"}
        r = requests.get(f"{self.BASE}/messages", headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("hydra:member", [])

    def read_message(self, login, domain, msg_id):
        headers = {"Authorization": f"Bearer {self.token}"}
        r = requests.get(f"{self.BASE}/messages/{msg_id}", headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()

# ---------------------------
# Wrapper for dual backend
# ---------------------------
class TempMail:
    def __init__(self):
        self.backend = None
        self.email = None
        self.login = None
        self.domain = None
        self._choose_backend()

    def _choose_backend(self):
        try:
            # try 1secmail
            backend = OneSecMail()
            email = backend.get_address()
            self.backend = backend
            self.email = email
            self.login, self.domain = email.split("@")
            console.print("[green]Using 1secmail backend[/green]")
        except Exception:
            # fallback to mail.tm
            backend = MailTM()
            email = backend.get_address()
            self.backend = backend
            self.email = email
            self.login, self.domain = email.split("@")
            console.print("[yellow]Using mail.tm backend (fallback)[/yellow]")

    def new_address(self):
        return self._choose_backend()

    def list_messages(self):
        return self.backend.list_messages(self.login, self.domain)

    def read_message(self, msg_id):
        return self.backend.read_message(self.login, self.domain, msg_id)

# ---------------------------
# UI helpers
# ---------------------------
def clear(): os.system("cls" if os.name=="nt" else "clear")

def banner():
    clear()
    b = pyfiglet.figlet_format("A X E E E H")
    console.print(f"[bold red]{b}[/bold red]\n")

def show_inbox(msgs, email):
    if not msgs:
        console.print("[yellow]Inbox empty[/yellow]")
        return
    table = Table(title=f"Inbox for {email}")
    table.add_column("ID", style="cyan")
    table.add_column("From", style="magenta")
    table.add_column("Subject", style="green")
    for m in msgs:
        mid = str(m.get("id") or m.get("id", ""))
        frm = m.get("from") or m.get("sender", {}).get("address", "")
        subj = m.get("subject") or "(no subject)"
        table.add_row(mid, frm, subj)
    console.print(table)

def copy_email(email):
    try:
        if shutil.which("termux-clipboard-set"):
            subprocess.run(["termux-clipboard-set"], input=email.encode(), check=True)
            console.print("[green]Copied with termux-clipboard-set[/green]")
        else:
            pyperclip.copy(email)
            console.print("[green]Copied with pyperclip[/green]")
    except Exception:
        console.print("[yellow]Copy failed. Copy manually.[/yellow]")

# ---------------------------
# Main loop
# ---------------------------
def run():
    tm = TempMail()
    while True:
        banner()
        console.print(f"Your email: [bold cyan]{tm.email}[/bold cyan]\n")
        console.print("[1] Show Inbox")
        console.print("[2] Read Message by ID")
        console.print("[3] New Address")
        console.print("[4] Copy Email")
        console.print("[5] Quit")
        c = console.input("\nChoose: ").strip()
        if c=="1":
            msgs = tm.list_messages()
            show_inbox(msgs, tm.email)
            input("Enter...")
        elif c=="2":
            msgs = tm.list_messages()
            show_inbox(msgs, tm.email)
            msgid = console.input("Enter ID: ").strip()
            if not msgid: continue
            msg = tm.read_message(msgid)
            console.rule("Message")
            console.print(f"From: {msg.get('from') or msg.get('sender',{}).get('address','')}")
            console.print(f"Subject: {msg.get('subject')}\n")
            console.print(msg.get("textBody") or msg.get("intro") or "(no body)")
            input("Enter...")
        elif c=="3":
            tm = TempMail()
        elif c=="4":
            copy_email(tm.email)
            input("Enter...")
        elif c=="5":
            break
        else:
            continue

if __name__=="__main__":
    run()
