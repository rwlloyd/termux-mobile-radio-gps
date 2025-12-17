# Android Device Setup: Termux

## Installation
1. Download Termux and Termux:API from F-Droid Store
2. Launch the app and allow necessary permissions
3. Run `pkg update && pkg upgrade` to update packages
    - Follow any instructions if repo list needs refreshing

## Initial Configuration
```bash
pkg install git curl wget nano termux-api jq bc
```

## Storage Access
```bash
termux-setup-storage
```
Grant file system permissions when prompted.

This command sets up symlinks between termux and android. 

After that, these paths exist:
```bash
~/storage/shared/     → Internal storage (Download, Documents, etc)
~/storage/downloads/  → Download folder
~/storage/dcim/
~/storage/documents/
```

## Other Tools (Optional)
```bash
pkg install build-essential python nodejs
```

## SSH Setup (Optional)
```bash
pkg install openssh
sshd
```

## Tips
- Use `Ctrl + Volume Down` for additional keys
- Install `termux-api` for hardware access
- Keep packages updated regularly with `pkg upgrade`