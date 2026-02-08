import logging
import os
import platform
import shlex
import shutil
import subprocess
import webbrowser

from livekit.agents import function_tool


logger = logging.getLogger(__name__)


def _run_command(command: list[str]) -> bool:
    try:
        subprocess.run(command, check=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        logger.exception("Command failed: %s", command)
        return False


def _open_with_default_app(target_path: str) -> None:
    if platform.system() == "Windows":
        os.startfile(target_path)  # type: ignore[attr-defined]
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", target_path])
    else:
        subprocess.Popen(["xdg-open", target_path])


@function_tool()
async def open_path(path: str) -> str:
    """
    Opens a file or folder on the local machine.

    Use this tool when the user wants to open a local file or directory.
    """
    expanded_path = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(expanded_path):
        return f"Path not found: {expanded_path}"

    try:
        _open_with_default_app(expanded_path)
        return f"Opened: {expanded_path}"
    except Exception as exc:
        logger.exception("Failed to open path: %s", expanded_path)
        return f"Failed to open path: {exc}"


@function_tool()
async def open_url(url: str) -> str:
    """
    Opens a URL in the default browser.

    Use this tool when the user wants to open a website.
    """
    cleaned_url = url.strip()
    if not cleaned_url:
        return "No URL provided."

    if "://" not in cleaned_url:
        cleaned_url = f"https://{cleaned_url}"

    try:
        webbrowser.open(cleaned_url, new=2)
        return f"Opened URL: {cleaned_url}"
    except Exception as exc:
        logger.exception("Failed to open URL: %s", cleaned_url)
        return f"Failed to open URL: {exc}"


@function_tool()
async def launch_app(app: str, args: str = "") -> str:
    """
    Launches a local application by name or full path.

    Use this tool when the user wants to open an installed application.
    """
    app = app.strip()
    if not app:
        return "No application name provided."

    executable = shutil.which(app) or (app if os.path.exists(app) else None)
    if not executable:
        return f"Application not found: {app}"

    cmd = [executable]
    if args:
        cmd.extend(shlex.split(args))

    try:
        subprocess.Popen(cmd)
        return f"Launched: {app}"
    except Exception as exc:
        logger.exception("Failed to launch app: %s", app)
        return f"Failed to launch app: {exc}"


@function_tool()
async def open_email(to: str = "", subject: str = "", body: str = "") -> str:
    """
    Opens the default email client with a pre-filled draft.

    Use this tool when the user wants to send an email.
    """
    params = []
    if subject:
        params.append(f"subject={subject}")
    if body:
        params.append(f"body={body}")
    query = "&".join(params)
    mailto = f"mailto:{to}"
    if query:
        mailto = f"{mailto}?{query}"
    webbrowser.open(mailto, new=2)
    return "Opened email composer."


@function_tool()
async def open_calendar() -> str:
    """
    Opens the default calendar web app.

    Use this tool when the user wants to check or add events.
    """
    webbrowser.open("https://calendar.google.com", new=2)
    return "Opened calendar."


@function_tool()
async def open_github(path: str = "") -> str:
    """
    Opens GitHub (optionally a specific repo or profile path).

    Use this tool when the user wants to open GitHub.
    """
    url = "https://github.com"
    if path:
        url = f"{url}/{path.lstrip('/')}"
    webbrowser.open(url, new=2)
    return "Opened GitHub."


@function_tool()
async def open_whatsapp(phone: str = "", message: str = "") -> str:
    """
    Opens WhatsApp Web, optionally with a phone number and message.
    """
    url = "https://web.whatsapp.com"
    if phone:
        url = f"https://wa.me/{phone}"
        if message:
            url = f"{url}?text={message}"
    webbrowser.open(url, new=2)
    return "Opened WhatsApp."


@function_tool()
async def open_instagram(profile: str = "") -> str:
    """
    Opens Instagram, optionally a profile.
    """
    url = "https://www.instagram.com"
    if profile:
        url = f"{url}/{profile.lstrip('/')}"
    webbrowser.open(url, new=2)
    return "Opened Instagram."


@function_tool()
async def set_system_volume(level: int) -> str:
    """
    Sets the system volume (0-100).

    Use this tool when the user asks to change volume.
    """
    clamped = max(0, min(100, int(level)))
    system = platform.system()

    if system == "Darwin":
        ok = _run_command(["osascript", "-e", f"set volume output volume {clamped}"])
    elif system == "Windows":
        ok = False
    else:
        ok = _run_command(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{clamped}%"])
        if not ok:
            ok = _run_command(["amixer", "set", "Master", f"{clamped}%"])

    if ok:
        return f"System volume set to {clamped}%."
    return "Unable to change system volume on this system."


@function_tool()
async def lock_screen() -> str:
    """
    Locks the screen.
    """
    system = platform.system()
    if system == "Darwin":
        ok = _run_command(
            ["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"]
        )
    elif system == "Windows":
        ok = _run_command(["rundll32.exe", "user32.dll,LockWorkStation"])
    else:
        ok = _run_command(["loginctl", "lock-session"])

    if ok:
        return "Screen locked."
    return "Unable to lock the screen on this system."
