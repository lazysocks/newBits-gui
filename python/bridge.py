#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "requests>=2.34.2",
# ]
# ///

"""
JSON-stdio bridge between the Electron GUI and the newBits recovery backend.
Reads JSON commands from stdin (one per line), writes JSON events to stdout.
"""

import sys
import os
import json
import re
import math
import hashlib
import shutil
import subprocess
from pathlib import Path
from subprocess import Popen


def emit(event_type, **kwargs):
    print(json.dumps({"type": event_type, **kwargs}), flush=True)

def log(msg, level="info"):
    emit("log", level=level, msg=msg)

def result(data):
    emit("result", data=data)

def error(msg):
    emit("error", msg=msg)

def progress(current, total, desc=""):
    emit("progress", current=current, total=total, desc=desc)


def convert_size(n):
    if n == 0:
        return "0 B"
    names = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(n, 1024)))
    return f"{round(n / math.pow(1024, i), 2)} {names[i]}"


def check_sha1(filepath, expected):
    sha = hashlib.sha1()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest() == expected


# ── Command handlers ───────────────────────────────────────────────────────────

def cmd_check_sudo(_):
    result({"is_root": os.getuid() == 0})


def cmd_fetch_recovery_list(args):
    import requests
    workdir = args.get("workdir", "/tmp/tmp.newbits")
    os.makedirs(workdir, exist_ok=True)
    url = "https://dl.google.com/dl/edgedl/chromeos/recovery/recovery2.json"
    dest = os.path.join(workdir, "recovery2.json")

    log("Downloading ChromeOS recovery list from Google…")
    try:
        r = requests.get(url, stream=True, allow_redirects=True)
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        progress(downloaded, total, "Downloading recovery list")
        with open(dest) as f:
            data = json.load(f)
        log(f"Recovery list ready — {len(data)} entries")
        result({"count": len(data), "dest": dest})
    except Exception as e:
        error(str(e))


def cmd_search_models(args):
    json_path = args.get("json_path")
    raw_pattern = args.get("pattern", "").strip()
    pattern = raw_pattern.upper()[:9]

    try:
        with open(json_path) as f:
            data = json.load(f)
    except Exception as e:
        error(str(e))
        return

    matches = []
    for i, model in enumerate(data):
        if model.get("channel") != "STABLE":
            continue
        if pattern and not re.search(pattern, model.get("hwidmatch", "")):
            continue
        matches.append({
            "index": i,
            "model": model.get("model", ""),
            "manufacturer": model.get("manufacturer", ""),
            "chrome_version": model.get("chrome_version", ""),
            "version": model.get("version", ""),
            "hwidmatch": model.get("hwidmatch", ""),
            "url": model.get("url", ""),
            "file": model.get("file", ""),
            "sha1": model.get("sha1", ""),
            "filesize": model.get("filesize", 0),
            "zipfilesize": model.get("zipfilesize", 0),
        })
    result({"models": matches})


def cmd_get_usb_drives(_):
    raw = subprocess.run(
        ["cat", "/proc/partitions"], capture_output=True, text=True
    ).stdout.splitlines()

    drives = []
    for line in raw:
        if re.search(r"sd[a-z]$", line):
            dev = re.sub(r"[0-9\. ]+", "", line).strip().split()[-1]
            if dev and dev not in drives:
                drives.append(dev)

    usb_drives = {}
    for dev in drives:
        try:
            dtype = subprocess.run(
                ["cat", f"/sys/block/{dev}/device/type"], capture_output=True, text=True
            ).stdout.strip()
            removable = subprocess.run(
                ["cat", f"/sys/block/{dev}/removable"], capture_output=True, text=True
            ).stdout.strip()
            link = subprocess.run(
                ["readlink", "-f", f"/sys/block/{dev}"], capture_output=True, text=True
            ).stdout.strip()
            if dtype == "0" and removable == "1" and re.search(r"usb", link):
                vendor = subprocess.run(
                    ["cat", f"/sys/block/{dev}/device/vendor"], capture_output=True, text=True
                ).stdout.strip()
                model = subprocess.run(
                    ["cat", f"/sys/block/{dev}/device/model"], capture_output=True, text=True
                ).stdout.strip()
                size_sectors = int(subprocess.run(
                    ["cat", f"/sys/block/{dev}/size"], capture_output=True
                ).stdout.strip())
                size_bytes = size_sectors * 512
                usb_drives[dev] = {
                    "vendor": vendor,
                    "model": model,
                    "size": size_bytes,
                    "human_readable_size": convert_size(size_bytes),
                }
        except Exception:
            continue

    result({"drives": usb_drives})


def cmd_download_image(args):
    import requests
    url = args["url"]
    filename = args["filename"]
    dest = args["dest"]
    sha1_hash = args.get("sha1")
    resume = args.get("resume", False)

    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if resume and os.path.exists(dest):
            existing = Path(dest).stat().st_size
            headers = {"Range": f"bytes={existing}-"}
            r = requests.get(url, stream=True, headers=headers)
            total = int(r.headers.get("content-length", 0))
            downloaded = existing
            mode = "ab"
        else:
            if os.path.exists(dest):
                os.remove(dest)
            r = requests.get(url, stream=True, allow_redirects=True)
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            mode = "wb"

        log(f"Downloading {filename} ({convert_size(total)})…")
        with open(dest, mode) as f:
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress(downloaded, total or downloaded, f"Downloading {filename}")

        if sha1_hash:
            log("Verifying SHA1…")
            if check_sha1(dest, sha1_hash):
                log("SHA1 verified ✓")
                result({"success": True, "dest": dest})
            else:
                error("SHA1 mismatch — file may be corrupt")
        else:
            result({"success": True, "dest": dest})
    except Exception as e:
        error(str(e))


def cmd_unzip_image(args):
    zipfile = args["zipfile"]
    workdir = args["workdir"]
    imagefile = args["imagefile"]
    filesize = int(args["filesize"])

    try:
        if os.path.exists(imagefile):
            os.remove(imagefile)
        log(f"Extracting {os.path.basename(zipfile)}…")
        subprocess.run(["unzip", "-o", zipfile, "-d", workdir], check=True, capture_output=True)
        actual = Path(imagefile).stat().st_size
        if actual == filesize:
            log("Image size verified ✓")
            result({"success": True, "imagefile": imagefile})
        else:
            error(f"Image size mismatch — expected {filesize}, got {actual}")
    except Exception as e:
        error(str(e))


def cmd_apply_image(args):
    image_file = args["image_file"]
    devices = args["devices"]

    # dd requires root
    if os.getuid() != 0:
        error("Root privileges required to write to block devices")
        return

    try:
        log(f"Writing {os.path.basename(image_file)} to {len(devices)} device(s)…")
        procs = []
        for dev in devices:
            log(f"Starting dd → /dev/{dev}")
            cmd = f"dd bs=4M of=/dev/{dev} if={image_file} conv=sync status=progress"
            procs.append((dev, Popen(cmd, shell=True)))

        for dev, proc in procs:
            proc.wait()
            if proc.returncode == 0:
                log(f"/dev/{dev} — complete ✓")
            else:
                log(f"/dev/{dev} — dd exited with code {proc.returncode}", level="error")

        result({"success": True})
    except Exception as e:
        error(str(e))


def cmd_cleanup(args):
    files = args.get("files", [])
    for filepath in files:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                log(f"Removed {filepath}")
        except Exception as e:
            log(f"Could not remove {filepath}: {e}", level="warning")
    result({"success": True})


# ── Dispatch ───────────────────────────────────────────────────────────────────

HANDLERS = {
    "check_sudo":           cmd_check_sudo,
    "fetch_recovery_list":  cmd_fetch_recovery_list,
    "search_models":        cmd_search_models,
    "get_usb_drives":       cmd_get_usb_drives,
    "download_image":       cmd_download_image,
    "unzip_image":          cmd_unzip_image,
    "apply_image":          cmd_apply_image,
    "cleanup":              cmd_cleanup,
}


def main():
    log("Bridge ready")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            cmd = json.loads(line)
            handler = HANDLERS.get(cmd.get("cmd"))
            if handler:
                handler(cmd)
            else:
                error(f"Unknown command: {cmd.get('cmd')}")
        except json.JSONDecodeError:
            error(f"Invalid JSON: {line}")
        except Exception as e:
            error(f"Unhandled error: {e}")


if __name__ == "__main__":
    main()
