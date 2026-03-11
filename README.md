# RPIChat

An SSH-based chat server. Connect via any standard SSH client to join real-time text chat rooms.

## Features

- Connect using your normal SSH client (Terminal, PuTTY, etc.)
- Register new accounts by using `register` as the password on first connection
- Real-time broadcast messaging with multiple rooms
- Commands: `/help`, `/online`, `/join`, `/msg`, `/me`, `/clear`, `/changepass`, `/exit`, `/quit`
- Room operators can `/kick`, `/op`, `/deop` users
- Message history for new joiners
- Optional timestamps on messages
- Rate limiting and session limits

## Requirements

- Python 3.9+

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

The server listens on **port 2022** by default.

## Project Structure

```
raspchat/
├── main.py              # Entry point
├── config.json          # Configuration
├── rpichat/             # Package
│   ├── __init__.py
│   ├── config.py        # Config loading
│   ├── storage.py       # User & room_ops persistence
│   ├── state.py         # Runtime state (clients, locks)
│   ├── utils.py         # Formatting, colors, validation
│   ├── server.py        # SSH server, broadcaster
│   └── cogs/            # Pluggable commands (see rpichat/cogs/README.md)

## Usage

1. **Register a new account**
   ```bash
   ssh -p 2022 yourname@localhost
   ```
   When prompted for password, enter: `register`

2. **Login (existing account)**
   ```bash
   ssh -p 2022 yourname@localhost
   ```
   Enter your password as usual.

3. **In chat**
   - Type messages and press Enter to send
   - `/help` — list all commands
   - `/online` — see who's in your room
   - `/join #room` — join or create a room
   - `/msg user message` — private message
   - `/me waves` — action message
   - `/clear` — clear screen
   - `/changepass` — change password
   - `/typing` — show typing indicator
   - `/exit` or `/quit` — disconnect

## Configuration

Edit `config.json`:

| Variable | Default | Description |
|----------|---------|-------------|
| `port` | 2022 | Server port |
| `host_key` | ssh_host_key | SSH host key file path |
| `user_db` | users.json | User database file |
| `login_banner` | *(see config)* | Message shown before password prompt |
| `username_min_len` | 3 | Minimum username length |
| `username_max_len` | 20 | Maximum username length |
| `login_rate_limit` | 5 | Max failed logins per window |
| `login_rate_window_sec` | 60 | Rate limit window (seconds) |
| `max_sessions_per_user` | 2 | Max concurrent sessions per user |
| `timestamps` | true | Show timestamps on messages |
| `history_size` | 50 | Messages to show new joiners |
| `default_room` | general | Room to join on login |
| `typing_indicator_timeout_sec` | 10 | How long /typing lasts |
