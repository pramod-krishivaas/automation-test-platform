"""
tests/utils/tesseract_setup.py
──────────────────────────────
Point pytesseract at the Tesseract OCR *engine* binary, wherever it happens to be
installed on this machine.

pytesseract is only a thin wrapper — it shells out to a `tesseract` executable. A
`TesseractNotFoundError` means that executable isn't on PATH and pytesseract's
default `tesseract_cmd` doesn't resolve. That bites us in two situations:

  • Different installers put the binary in different places (scoop → ~/scoop/…,
    choco / winget / UB-Mannheim → C:\\Program Files\\Tesseract-OCR\\…).
  • The platform runs pytest as a SUBPROCESS with a curated env, so the shell's
    PATH (including scoop shims) may not be inherited — PATH lookup then fails
    even though the binary exists.

`configure_tesseract()` resolves the binary once (PATH first, then the known
install locations) and sets `pytesseract.pytesseract.tesseract_cmd` to an absolute
path so it works regardless of the caller's PATH. Import-safe: never raises.
"""
import os
import shutil

import pytesseract

# Absolute locations to probe when the binary isn't found on PATH. Ordered by how
# this repo installs it (scoop, user-level) then the standard machine-wide installers.
_SCOOP_ROOT = os.environ.get("SCOOP") or os.path.expanduser(r"~\scoop")
_CANDIDATES = [
    os.path.join(_SCOOP_ROOT, "shims", "tesseract.exe"),
    os.path.join(_SCOOP_ROOT, "apps", "tesseract", "current", "tesseract.exe"),
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR", "tesseract.exe"),
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/opt/homebrew/bin/tesseract",
]


def find_tesseract():
    """Return an absolute path to the tesseract binary, or None if not found."""
    on_path = shutil.which("tesseract")
    if on_path:
        return on_path
    for candidate in _CANDIDATES:
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def configure_tesseract():
    """
    Set pytesseract.tesseract_cmd to the resolved binary and return that path (or
    None if nothing was found — in which case pytesseract keeps its default and the
    original TesseractNotFoundError will surface, which is the honest outcome).
    """
    exe = find_tesseract()
    if exe:
        pytesseract.pytesseract.tesseract_cmd = exe
    return exe
