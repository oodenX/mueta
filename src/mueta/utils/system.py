# src/mueta/utils/system.py
"""System utilities for dependency checking and OS detection."""

import shutil
import platform
from loguru import logger


def check_fpcalc() -> tuple[bool, str]:
    """检测 fpcalc 是否已安装

    Returns:
        (is_installed, install_guide):
            - is_installed: True if fpcalc is found in PATH
            - install_guide: Installation instructions if not found
    """
    if shutil.which("fpcalc"):
        logger.debug("fpcalc found in system PATH")
        return True, ""

    # 根据操作系统返回安装指南
    os_name = platform.system()

    install_guides = {
        "Linux": """请安装 chromaprint:

  Ubuntu/Debian:
    sudo apt install libchromaprint-tools

  Arch Linux:
    sudo pacman -S chromaprint

  Fedora:
    sudo dnf install chromaprint-tools""",

        "Darwin": """请使用 Homebrew 安装:
    brew install chromaprint""",

        "Windows": """请下载并安装 Chromaprint:
    下载地址: https://acoustid.org/chromaprint

    安装后请确保 fpcalc.exe 在系统 PATH 中"""
    }

    guide = install_guides.get(os_name, install_guides["Windows"])
    logger.warning(f"fpcalc not found on {os_name}")

    return False, guide
