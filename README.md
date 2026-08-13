# newBits

Electron GUI for flashing ChromeOS recovery images to USB drives.

## Prerequisites

[uv](https://docs.astral.sh/uv/) must be installed on the machine running the app. It manages the Python backend automatically — no separate Python install needed.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installation

Download the latest `newBits-*.AppImage` from the releases page.

```bash
chmod +x newBits-*.AppImage
```

### Running without FUSE

Most systems require FUSE to mount AppImages. If you get a FUSE error (common on Fedora and other systems where it isn't installed by default), run with:

```bash
./newBits-*.AppImage --appimage-extract-and-run
```

Or install FUSE and run normally:

```bash
# Fedora
sudo dnf install fuse fuse-libs

# Debian/Ubuntu
sudo apt install libfuse2
```

## Running

Launch the app as your normal user — **do not run as root**:

```bash
./newBits-*.AppImage --appimage-extract-and-run
```

The app will detect that it isn't running as root and prompt you to elevate via **pkexec**, which opens a system privilege dialog. Root access is only needed for the backend process that writes to block devices.

## Usage

1. **Privileges** — click *Elevate with pkexec* and enter your password
2. **Model** — download the ChromeOS recovery list, then search for your device by board ID (e.g. `FIZZ`, `OCTOPUS`)
3. **USB** — select the drive(s) to flash
4. **Download** — the recovery image is downloaded and verified
5. **Apply** — image is written in parallel to all selected drives
   - Click *Write more drives* to flash additional drives with the same image without re-downloading
   - Click *Continue* to proceed to cleanup
6. **Cleanup** — remove temporary files from `/tmp/tmp.newbits`

## Building from source

```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

# Build AppImage
npm run package
```

The built AppImage will be in `dist/`.
