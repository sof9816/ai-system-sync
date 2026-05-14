# Remote Access Guide — Let Me Set Up Your PC

Since your PC is on a different network, here are your options.

## Option 1: RustDesk (Recommended — Free, No Account)

1. On your PC, download RustDesk from https://rustdesk.com/
2. Install and run it
3. You'll see an ID + Password (e.g., `123 456 789`)
4. Send me the ID and password (this chat is secure)
5. I connect and do the full setup

**Pros:** Free, open-source, no signup, fast  
**Cons:** You need to be at the PC to start it

## Option 2: AnyDesk

1. Download from https://anydesk.com/
2. Install and run
3. Share your AnyDesk ID (e.g., `123 456 789`)
4. Set a password in Settings → Security → Unattended Access

**Pros:** Well-known, reliable  
**Cons:** Free version has usage limits

## Option 3: TeamViewer

1. Download from https://www.teamviewer.com/
2. Install and run
3. Share ID + password

**Pros:** Industry standard  
**Cons:** Free version flags commercial use, annoying

## Option 4: Parsec (Gaming-focused, Low Latency)

1. Download from https://parsec.app/
2. Sign up (free)
3. Add me as a friend or share a guest link

**Pros:** Extremely low latency, great for remote coding  
**Cons:** Requires account

## Option 5: Windows RDP + Tailscale (Advanced)

If you want persistent access:

1. Install Tailscale on both PCs: https://tailscale.com/
2. Sign in with same account on both
3. Enable Windows Remote Desktop on your PC
4. I connect via Tailscale IP + RDP

**Pros:** Native Windows experience, persistent  
**Cons:** More setup, requires Tailscale account

## What I'll Do Once Connected

1. Check Windows version and prerequisites
2. Install WSL2 + Ubuntu
3. Run the full setup inside WSL
4. Install Obsidian on Windows host
5. Configure API keys (you'll need to paste them)
6. Test everything: hermes, pi, dashboard, aliases
7. Document any PC-specific tweaks

## Security Notes

- Change all remote access passwords after I'm done
- Revoke any guest links
- I will NOT need your API keys (you'll paste those yourself)
- I will NOT access any personal files outside agent-home

## Send Me

Just reply with:
- Which option you picked
- The ID / password / link
- Windows version (Win 10 or 11? Home or Pro?)
