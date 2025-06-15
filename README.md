# Telegram Cloud Backup

### Store and retrieve large files using Telegram as a personal, unlimited cloud backend.

---

## About The Project

This project turns your Telegram account into a powerful, multi-terabyte cloud storage solution. It provides a set of Python scripts that allow you to upload and download huge files (up to terabytes in size) by splitting them into smaller chunks and storing them securely in a private Telegram channel.

It's a completely **self-hosted** and **non-profit** tool. You own the data, you own the channel, and you own the bot.

There are two primary methods for interacting with your storage:

* **Bot Method:** A simple and user-friendly method that uses a Telegram Bot to upload and download files in 19MB chunks. It's perfect for most files and provides a great user experience.
* **User Method:** A more powerful method that logs in as a regular Telegram user to handle massive 2GB chunks. It's designed for extreme reliability when dealing with terabyte-scale files.

## Features

* **Multi-Terabyte Storage:** Leverage Telegram's generous file storage limits.
* **Automatic File Splitting & Joining:** The scripts handle the complex process of splitting files for upload and reassembling them for download.
* **Resumable Uploads:** If an upload is interrupted, you can run the script again and it will automatically resume from where it left off.
* **Two Upload/Download Methods:** Choose between the simple Bot method or the powerful User method.
* **Command-Line Interface:** Manage your files through an easy-to-use menu in your terminal.
* **Secure & Private:** Your files are stored in your own private channel that only you and your bot can access.
* **Open Source:** The code is free, transparent, and open for contributions.

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

* Python 3.7 or higher installed on your system.
* A Telegram account.
* Git installed on your system.

### Setup Instructions

1.  **Clone the Repository**
    Open your terminal and clone the project from GitHub:
    ```sh
    git clone [https://github.com/myrosama/telegram-cloud-backup.git](https://github.com/myrosama/telegram-cloud-backup.git)
    cd telegram-cloud-backup
    ```

2.  **Install Required Libraries**
    Install all the necessary Python packages using the `requirements.txt` file:
    ```sh
    pip install -r requirements.txt
    ```

3.  **Configure Your Bot (`bot/config.py`)**
    * Talk to **@BotFather** on Telegram to create a new bot. He will give you a `BOT_TOKEN`.
    * Create a new **private** Telegram channel.
    * Add your new bot to the private channel as an **Administrator**.
    * Forward a message from your private channel to **@userinfobot** to get the channel's numerical `CHANNEL_ID` (it will start with `-100...`).
    * Open the `bot/config.py` file and fill in your details:
        ```python
        BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
        OWNER_ID = "YOUR_PERSONAL_TELEGRAM_ID_HERE" # Optional, get from @userinfobot
        CHANNEL_ID = -100... # Your private channel's numerical ID
        ```

4.  **Configure Your User Account (`client/config.py`)** (Optional, for User Method)
    * Go to **https://my.telegram.org** and log in with your phone number.
    * Click on **"API development tools"** and create a new application.
    * You will be given an `API_ID` and `API_HASH`.
    * Open the `client/config.py` file and fill in your details:
        ```python
        API_ID = 1234567 # Your integer API ID
        API_HASH = "YOUR_API_HASH_HERE"
        CHANNEL_ID = -100... # Must be the SAME channel ID as in bot/config.py
        ```

## Usage

All interaction with the client is done through the main menu script.

1.  Open your terminal in the project's root directory.
2.  Run the main script:
    ```sh
    python client/main.py
    ```
3.  A menu will appear, allowing you to choose whether to upload or download, and which method to use.
4.  Follow the on-screen prompts to upload or download your files. Downloaded files will appear in a new `downloads` folder.

## License

This project is distributed under the MIT License. See `LICENSE` for more information.
