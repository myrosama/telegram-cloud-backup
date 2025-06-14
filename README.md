# telegram-cloud-backup
Store and retrieve large files using Telegram as cloud backend

# telegram-cloud-backup

This is an open-source cloud storage solution that uses Telegram channels as the backend for file storage. Users split large files into 5GB chunks, upload them to a Telegram channel using their own Telegram bot, and download/merge them back later using a desktop client.

## 🔧 Features
- Split files into <5GB chunks (Telegram's limit).
- Upload/download files via user-owned Telegram bot.
- Metadata management for seamless reassembly.
- Desktop mini-app for upload/download operations.

## 📁 Project Structure
```
telegram-cloud-backup/
├── bot/
│   └── bot.py              # Telegram bot logic (aiogram/pyTelegramBotAPI)
│   └── handlers.py         # Handlers for commands and user actions
│   └── config.py           # Token, channel ID setup
│
├── client/
│   └── main.py             # Launchpad for client logic
│   └── splitter.py         # File splitting/merging utilities
│   └── uploader.py         # Upload to Telegram channel
│   └── downloader.py       # Download from Telegram channel
│   └── config.json         # User configuration
│
├── utils/
│   └── file_utils.py       # SHA256, chunk naming, etc.
│   └── telegram_api.py     # Telegram upload/download logic
│
├── requirements.txt        # Python dependencies
├── README.md
└── LICENSE
```

## ⚙️ Setup Instructions

### Telegram Bot & Channel
1. Create a new bot via [@BotFather](https://t.me/BotFather).
2. Save the API token.
3. Create a private Telegram channel.
4. Add your bot as an admin to the channel.
5. Add your own Telegram user to the channel.

### Client Config
- Edit `client/config.json` with:
```json
{
  "bot_token": "<YOUR_BOT_TOKEN>",
  "channel_id": "@your_channel",
  "download_folder": "C:/Users/You/Downloads",
  "upload_folder": "C:/Users/You/Uploads"
}
```

## 🛠 Example Usage
### Uploading a File
```bash
python client/main.py upload bigfile.mp4
```

### Downloading a File
```bash
python client/main.py download bigfile.mp4
```

## 📦 Planned Features
- GUI version of the client
- Upload/download resume
- File encryption
- Cleanup old files in channel

## 💬 Contributing
Pull requests and forks are welcome! Star the repo and suggest new ideas!

## 📝 License
MIT License
