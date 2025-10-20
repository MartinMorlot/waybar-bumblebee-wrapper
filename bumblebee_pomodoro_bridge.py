#!/usr/bin/env python3
import json
import os
import sys
import subprocess
import tempfile
import signal

STATE_FILE = os.path.join(tempfile.gettempdir(), "bumblebee_pomodoro_pid")

def run_bumblebee():
    """Run bumblebee-status pomodoro module and continuously stream updates for Waybar."""
    proc = subprocess.Popen(
        ["/home/mmorlot/dev-perso/bumblebee-status/bumblebee-status",
         "-m", "pomodoro",
         "-t", "gruvbox-powerline",
         "-f", "json"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Save PID for click forwarding
    with open(STATE_FILE, "w") as f:
        f.write(str(proc.pid))

    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                if isinstance(data, list):
                    # Find first non-decorator block
                    text_to_print = None
                    for module in data:
                        if not module.get("_decorator", False):
                            text = module.get("full_text", "")
                            if text:
                                text_to_print = text
                                break
                    if text_to_print:
                        print(text_to_print, flush=True)
            except json.JSONDecodeError:
                # Fallback: print line as-is if JSON parsing fails
                print(line, flush=True)

    except KeyboardInterrupt:
        pass
    finally:
        # Clean up PID file and terminate bumblebee-status process
        if os.path.exists(STATE_FILE):
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
