# Slack API Assignment — Head of Data 101

This repo contains my work for the **Head of Data 101** Slack API assignment (Albert School).

What the bot does:
- uploads a few images to our group channel when it starts
- listens to messages in real time (Socket Mode)
- replies when someone writes `Wikipedia:<topic>` by returning the first paragraph from Wikipedia

---

## What I implemented

### Part 1 — Slack app setup
- created a Slack app from scratch
- enabled Socket Mode
- added the required bot scopes and installed the app in the class workspace

### Part 2 — Upload images
- the script uploads all files found in `./images`
- images are posted in the channel defined by `GROUP_CHANNEL_ID`

### Part 3 — Wikipedia replies
- if a message starts with `Wikipedia:`, the bot queries Wikipedia’s REST API
- it posts the first paragraph back to Slack

---

## How to run

1) Install dependencies:
```bash
pip install -r requirements.txt
