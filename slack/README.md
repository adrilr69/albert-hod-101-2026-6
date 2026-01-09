# Slack API Assignment — Head of Data 101

This project was built as part of the **Head of Data 101** course at Albert School.

The objective is to interact with the **Slack Web API** using Python in order to:
1. Post images in a Slack channel
2. Listen to messages in real time using Socket Mode
3. Answer Wikipedia queries automatically

---

## Features implemented

### Part 1 — Slack App setup
- Slack App created from scratch
- Bot user configured
- Permissions handled via OAuth & Permissions
- Socket Mode enabled (no public server required)

### Part 2 — Image upload
- The script automatically uploads all images located in the `images/` folder
- Images are posted in the group channel of the project

### Part 3 — Wikipedia bot
- The bot listens to all messages in the channel
- When a message starts with `Wikipedia:<topic>`, the bot:
  - Queries the Wikipedia REST API
  - Extracts the first paragraph of the article
  - Posts the response directly in Slack

---

## Technologies used

- Python 3
- Slack Bolt (Python)
- Slack Web API
- Socket Mode
- Wikipedia REST API

---

## How to run the project

1. Install dependencies:
```bash
pip install -r requirements.txt

