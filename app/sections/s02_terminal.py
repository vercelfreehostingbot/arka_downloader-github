"""Arka Downloader section: TERMINAL."""

from .s01_paths import *

# ══════════════════════════════════════════════════════════════
# TERMINAL
# ══════════════════════════════════════════════════════════════
if os.name == "nt":
    os.system("")


class C:
    R = "\033[0m"; B = "\033[1m"; D = "\033[2m"
    RED = "\033[91m"; GRN = "\033[92m"; YEL = "\033[93m"
    BLU = "\033[94m"; MAG = "\033[95m"; CYN = "\033[96m"


def print_banner():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.write(
        f"\n{C.CYN}{C.B}"
        f"   █████╗ ██████╗ ██╗  ██╗ █████╗\n"
        f"  ██╔══██╗██╔══██╗██║ ██╔╝██╔══██╗\n"
        f"  ███████║██████╔╝█████╔╝ ███████║\n"
        f"  ██╔══██║██╔══██╗██╔═██╗ ██╔══██║\n"
        f"  ██║  ██║██║  ██║██║  ██╗██║  ██║\n"
        f"  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝\n{C.R}\n"
        f"{C.MAG}{C.B}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.R}\n"
        f"  {C.YEL}⚡{C.R} {C.B}Version{C.R}  {C.CYN}{FILE_VERSION}{C.R}"
        f"      {C.YEL}👤{C.R} {C.B}Owner{C.R}  {C.CYN}@AMIRALI_IRX{C.R}"
        f"      {C.YEL}💎{C.R} {C.B}System{C.R}  {C.GRN}Premium{C.R}\n"
        f"{C.MAG}{C.B}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.R}\n\n"
    )
    sys.stdout.flush()


def log_step(label: str, value: str, ok: bool = True):
    icon = f"{C.GRN}✓{C.R}" if ok else f"{C.RED}✗{C.R}"
    sys.stdout.write(f"  {C.D}│{C.R} {icon} {label:<20} {C.D}{value}{C.R}\n")
    sys.stdout.flush()


def log_ok(msg: str):
    sys.stdout.write(f"  {C.GRN}✓ {msg}{C.R}\n")
    sys.stdout.flush()


def log_err(msg: str):
    sys.stdout.write(f"  {C.RED}✗ {msg}{C.R}\n")
    sys.stdout.flush()


def log_warn(msg: str):
    sys.stdout.write(f"  {C.YEL}⚠ {msg}{C.R}\n")
    sys.stdout.flush()



__all__ = [name for name in globals() if not name.startswith("__")]
