# Raspchat

An SSH-based chat server. Connect via any standard SSH client to join a real-time text chat room.

## Features

- Connect using your normal SSH client (Terminal, PuTTY, etc.)
- Register new accounts by using `register` as the password on first connection
- Real-time broadcast messaging
- Commands: `/who` (list online users), `/exit` or `/quit` (disconnect)

## Requirements

- Python 3.7+

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

The server listens on **port 2022** by default. On first run, it generates an SSH host key at `ssh_host_key` if one doesn't exist.

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
   - `/who` — see who's online
   - `/exit` or `/quit` — disconnect

## Configuration

Edit the config section at the top of `main.py`:

| Variable   | Default       | Description            |
|-----------|---------------|------------------------|
| `PORT`    | 2022          | Server port            |
| `HOST_KEY`| ssh_host_key  | SSH host key file path |
| `USER_DB` | users.json    | User database file     |
