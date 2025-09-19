#!/usr/bin/env python3
"""
AXEEEH TempMail - single-file terminal temp-mail tool.

Features:
- Auto-installs required Python packages if missing
- Uses 1secmail API to generate disposable email, list and read messages
- Save messages to ./messages/
- Copy email address to clipboard (Termux or pyperclip fallback)
- Menu-driven, Termux-friendly
"""

import sys, subprocess, importlib, time, os, random, threading, shutil

# ---------------------------
# Auto-install missing packages
# ---------------------------
REQUIRED = ["requests", "rich", "pyfiglet", "pyperclip"]
missing = []
for pkg in REQUIRED:
    try:
        importlib.import_module(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print("Installing missing packages:", ", ".join(missing))
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
    except Exception as e:
        print("Could not install packages automatically. Install manually and re-run.")
        print("Missing:", missing)
        raise SystemExit(1)

# Now safe to import
import requests
import pyfiglet
import pyperclip
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

# ---------------------------
# Configuration & small utils
# ---------------------------
SECMAIL_BASE = "https://www.1secmail.com/api/v1/"

QUOTES = [
    "Stay curious, keep learning.",
    "Small steps every day add up.",
    "Build things and learn from them.",
    "Practice makes progress."
]

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def ensure_messages_dir():
    os.makedirs("messages", exist_ok=True)

# ---------------------------
# Startup loading with progress bar
# ---------------------------
BOOT_STEPS = [
    "Preparing environment",
    "Checking network",
    "Loading fonts",
    "Initializing inbox engine",
    "Finalizing startup"
]

def startup_sequence(duration_per_step=0.45):
    clear()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as p:
        task = p.add_task("[bold green]Starting AXEEEH TempMail...", total=None)
        for step in BOOT_STEPS:
            p.update(task, description=f"[cyan]{step}[/cyan]")
            time.sleep(duration_per_step)
        p.update(task, description="[green]Done[/green]")
        time.sleep(0.4)

# ---------------------------
# Banner
# ---------------------------
def banner():
    clear()
    ascii_banner = pyfiglet.figlet_format("A X E E E H")
    console.print(f"[bold red]{ascii_banner}[/bold red]")
    console.print(f"[italic yellow]{random.choice(QUOTES)}[/italic yellow]\n")

# ---------------------------
# 1secmail API helpers
# ---------------------------
def secmail_get_mailbox():
    try:
        r = requests.get(SECMAIL_BASE, params={"action":"genRandomMailbox","count":1}, timeout=10)
        r.raise_for_status()
        return r.json()[0]
    except Exception as e:
        console.print(f"[red]Error generating mailbox:[/red] {e}")
        raise

def secmail_list_messages(login, domain):
    try:
        r = requests.get(SECMAIL_BASE, params={"action":"getMessages","login":login,"domain":domain}, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        console.print(f"[red]Error listing messages:[/red] {e}")
        return []

def secmail_read_message(login, domain, msg_id):
    try:
        r = requests.get(SECMAIL_BASE, params={"action":"readMessage","login":login,"domain":domain,"id":msg_id}, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        console.print(f"[red]Error reading message:[/red] {e}")
        return None

# ---------------------------
# UI helpers
# ---------------------------
def show_inbox(msgs, email, title="Inbox"):
    if not msgs:
        console.print("[bold yellow]Inbox is empty.[/bold yellow]")
        return
    table = Table(title=f"{title} for {email} (Total: {len(msgs)})", show_lines=True)
    table.add_column("ID", style="cyan", width=6, justify="center")
    table.add_column("From", style="magenta", width=28, no_wrap=True)
    table.add_column("Subject", style="green", width=50, overflow="fold")
    for m in msgs:
        msg_id = str(m.get("id"))
        frm = m.get("from") or "(unknown)"
        subj = m.get("subject") or "(no subject)"
        if len(subj) > 50:
            subj = subj[:47] + "..."
        table.add_row(msg_id, frm, subj)
    console.print(table)

def copy_to_clipboard(text):
    # Termux native clipboard if available
    if shutil.which("termux-clipboard-set"):
        try:
            subprocess.run(["termux-clipboard-set"], input=text.encode("utf-8"), check=True)
            console.print("[green]Email copied to Termux clipboard.[/green]")
            return
        except Exception:
            pass
    try:
        pyperclip.copy(text)
        console.print("[green]Email copied via pyperclip.[/green]")
    except Exception:
        console.print("[yellow]No clipboard method available. Copy manually.[/yellow]")

def save_message(email, msg):
    ensure_messages_dir()
    safe_email = email.replace("@", "_at_")
    fname = f"messages/{safe_email}_msg_{msg.get('id')}.txt"
    try:
        with open(fname, "w", encoding="utf-8") as f:
            f.write(f"From: {msg.get('from')}\n")
            f.write(f"Subject: {msg.get('subject')}\n\n")
            body = msg.get("textBody") or msg.get("htmlBody") or "(no body)"
            f.write(body)
        console.print(f"[blue]Saved message to {fname}[/blue]")
    except Exception as e:
        console.print(f"[red]Failed saving message:[/red] {e}")

# ---------------------------
# Background fetch design (fast + slow pattern)
# - For now we implement fast (1secmail) and a hidden recheck of 1secmail shortly after.
# - This avoids requiring extra API account flows and still gives a snappy UI.
# ---------------------------
def background_refresh(login, domain, out_container, delay=2.0):
    """Fetch inbox after a short delay and store into out_container[0]"""
    try:
        time.sleep(delay)
        out_container[0] = secmail_list_messages(login, domain)
    except Exception:
        out_container[0] = out_container[0]  # leave as-is on error

# ---------------------------
# Main program (menu)
# ---------------------------
def run_interface():
    try:
        startup_sequence()
        email = secmail_get_mailbox()
    except Exception:
        console.print("[red]Could not initialize mailbox. Check your connection and try again.[/red]")
        return

    login, domain = email.split("@")
    last_count = 0

    while True:
        banner()
        console.print(f"[bold cyan]Your temp address:[/bold cyan] [white]{email}[/white]\n")
        console.print("[1] Show Inbox (fast)")
        console.print("[2] Read message by ID")
        console.print("[3] Change email (new random address)")
        console.print("[4] Copy email address to clipboard")
        console.print("[5] Refresh inbox and check for new messages")
        console.print("[6] Quit")

        choice = console.input("\n[bold yellow]Choose:[/bold yellow] ").strip()

        if choice == "1":
            # fast fetch + background update
            fast_msgs = secmail_list_messages(login, domain)
            container = [fast_msgs]
            t = threading.Thread(target=background_refresh, args=(login, domain, container, 1.6), daemon=True)
            t.start()
            show_inbox(container[0], email, title="Fast Inbox")
            # If background refreshed, notify user (t.join with small timeout)
            t.join(timeout=0.05)
            if not t.is_alive() and container[0] is not fast_msgs:
                # background updated quickly
                console.print("[green]Inbox updated.[/green]")
            console.input("\nPress Enter to return to menu...")

        elif choice == "2":
            msgs = secmail_list_messages(login, domain)
            if not msgs:
                console.print("[yellow]No messages available.[/yellow]")
                console.input("Press Enter...")
                continue
            show_inbox(msgs, email)
            msg_id = console.input("\nEnter message ID to read: ").strip()
            if not msg_id.isdigit():
                console.print("[red]ID must be a number.[/red]")
                console.input("Enter...")
                continue
            msg = secmail_read_message(login, domain, int(msg_id))
            if not msg:
                console.print("[red]Failed to load message.[/red]")
                console.input("Enter...")
                continue
            console.rule("[bold green]Message")
            console.print(f"[bold]From:[/bold] {msg.get('from')}")
            console.print(f"[bold]Subject:[/bold] {msg.get('subject')}\n")
            console.print(msg.get("textBody") or msg.get("htmlBody") or "(no body)")
            save_choice = console.input("\nSave this message to disk? [y/N]: ").strip().lower()
            if save_choice == "y":
                save_message(email, msg)
            console.input("\nEnter to return...")

        elif choice == "3":
            try:
                email = secmail_get_mailbox()
                login, domain = email.split("@")
                console.print(f"[green]Switched to: {email}[/green]")
            except Exception as e:
                console.print(f"[red]Failed to get new email:[/red] {e}")
            console.input("Enter to return...")

        elif choice == "4":
            copy_to_clipboard(email)
            console.input("Enter to return...")

        elif choice == "5":
            msgs = secmail_list_messages(login, domain)
            show_inbox(msgs, email, title="Refreshed Inbox")
            if len(msgs) > last_count:
                console.print("[bold green]New messages arrived since last check![/bold green]")
            last_count = len(msgs)
            console.input("Enter to return...")

        elif choice == "6":
            console.print("[bold green]Goodbye![/bold green]")
            break
        else:
            console.print("[red]Invalid choice.[/red]")
            time.sleep(0.8)

if __name__ == "__main__":
    try:
        run_interface()
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted. Exiting.[/red]")
