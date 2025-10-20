#!/usr/bin/env python3
import json
import os
import sys
import subprocess
import tempfile
import signal

STATE_FILE = os.path.join(tempfile.gettempdir(), "bumblebee_pomodoro_pid")

def run_bumblebee():
    # Start bumblebee-status for pomodoro in JSON mode
    proc = subprocess.Popen(
        ["/home/mmorlot/dev-perso/bumblebee-status/bumblebee-status", "-m", "pomodoro", "-t", "gruvbox-powerline", "-f", "json"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )

    # Save the PID for later click forwarding
    with open(STATE_FILE, "w") as f:
        f.write(str(proc.pid))

    try:
        for line in proc.stdout:
            try:
                data = json.loads(line.strip())
                if isinstance(data, list) and len(data) > 0:
                    module = data[0]
                    text = module.get("full_text", "")
                    print(text, flush=True)
            except Exception:
                continue
    except KeyboardInterrupt:
        pass
    finally:
        os.remove(STATE_FILE)
        proc.terminate()

def send_click(button):
    """Send a click event to the running bumblebee-status process."""
    if not os.path.exists(STATE_FILE):
        sys.exit(0)

    with open(STATE_FILE) as f:
        pid = int(f.read().strip())

    # Open the process’s stdin
    proc = subprocess.Popen(
        ["ps", "-o", "tty=", "-p", str(pid)],
        stdout=subprocess.PIPE,
        text=True
    )
    tty = proc.stdout.read().strip()
    if not tty:
        sys.exit(0)

    # Construct a JSON click event, like i3bar sends
    click_event = json.dumps({"name": "pomodoro", "button": button}) + "\n"

    # Send it to the stdin of bumblebee-status
    os.system(f"echo '{click_event}' > /proc/{pid}/fd/0")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        run_bumblebee()
    elif sys.argv[1] == "click-left":
        send_click(1)
    elif sys.argv[1] == "click-right":
        send_click(3)
    elif sys.argv[1] == "click-middle":
        send_click(2)
