import os
import time
from pathlib import Path
from urllib.parse import quote

import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient



# 1. Read secrets from .env
def load_env(path=".env"):
    """
    Tokens should not live inside the code.

    We store them in a .env file to avoid pushing secrets to GitHub.
    This function reads that file and loads the variables into os.environ,
    so they can be accessed anywhere in the script.
    """
    env_file = Path(path)
    if not env_file.exists():
        raise FileNotFoundError("The .env file was not found at the project root.")

    for raw_line in env_file.read_text().splitlines():
        line = raw_line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        # Only handle KEY=VALUE lines
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip()



# 2) Upload images on startup

def upload_images(client, channel_id, images_dir):
    """
    Part 2 of the assignment.

    When the bot starts, we scan the images folder
    and upload all valid images to the group channel.

    We do this once at startup to avoid spamming the channel.
    """
    images_path = Path(images_dir)
    if not images_path.exists():
        raise FileNotFoundError(f"Images folder not found: {images_path}")

    allowed_ext = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    images = [
        p for p in images_path.iterdir()
        if p.is_file() and p.suffix.lower() in allowed_ext
    ]

    # The assignment explicitly requires at least 3 images
    if len(images) < 3:
        raise ValueError("At least 3 images are required in the images folder.")

    for image in images:
        client.files_upload_v2(
            channel=channel_id,
            file=str(image),
            title=image.name,
        )

        # Small pause to avoid Slack rate limits
        time.sleep(0.3)



# 3) Wikipedia helper function

def wikipedia_first_paragraph(title):
    """
    Part 3 of the assignment.

    If a message starts with "Wikipedia:<topic>",
    we query Wikipedia's REST API and return the first paragraph.

    One important detail we discovered during testing:
    Wikipedia requires a proper User-Agent header.
    """
    title = (title or "").strip()
    if not title:
        return "Please provide a topic after 'Wikipedia:' (example: Wikipedia:Paris)."

    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}"
    headers = {"User-Agent": "AlbertSchool-HeadOfDataBot/1.0 (student project)"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException:
        return "Wikipedia request failed (network issue). Please try again."

    if response.status_code == 404:
        return f"No Wikipedia page found for: {title}"

    if not response.ok:
        return f"Error fetching Wikipedia data ({response.status_code})"

    data = response.json()
    extract = data.get("extract", "")

    # Wikipedia returns a long introduction string.
    # We keep only the first paragraph for readability.
    first_paragraph = extract.split("\n\n")[0].strip()
    return first_paragraph or f"The page '{title}' exists, but no summary was available."


# 4) Main: glue everything together

def main():
    """
    Main flow of the script:

    1) Load configuration and tokens from .env
    2) Upload images to the group channel
    3) Start listening to Slack messages using Socket Mode
    """
    load_env()

    bot_token = os.environ["SLACK_BOT_TOKEN"]
    app_token = os.environ["SLACK_APP_TOKEN"]
    channel_id = os.environ["GROUP_CHANNEL_ID"]
    images_dir = os.environ.get("IMAGES_DIR", "./images")

    # WebClient is used for Slack Web API calls (file uploads, messages, etc.)
    client = WebClient(token=bot_token)

    # Part 2: upload images when the bot starts
    upload_images(client, channel_id, images_dir)

    # Slack Bolt app to handle real-time events
    app = App(token=bot_token)

    @app.event("message")
    def handle_message(event, say):
        """
        This function runs every time a message is posted
        in a channel where the bot is present.

        We ignore bot messages to avoid responding to ourselves.
        """
        text = (event.get("text") or "").strip()

        if event.get("bot_id") is not None or event.get("subtype") == "bot_message":
            return

        if text.startswith("Wikipedia:"):
            title = text[len("Wikipedia:"):].strip()
            say(wikipedia_first_paragraph(title))

    # Socket Mode keeps the application alive
    # without requiring a public HTTP server.
    SocketModeHandler(app, app_token).start()


if __name__ == "__main__":
    main()
