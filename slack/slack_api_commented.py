import os
import time
from pathlib import Path
from urllib.parse import quote

import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient


"""
The goal is not only to make the code work,
but also to clearly explain what is happening
and why each step exists.

"""


def load_env(path=".env"):
    """
    We load environment variables manually from a .env file.

    Why do this?
    - We want to keep tokens out of the code
    - We avoid adding extra dependencies
    - It makes the project easier to understand

    Each valid line in the .env file is injected into os.environ
    so it can be accessed anywhere in the script.
    """
    if not Path(path).exists():
        raise FileNotFoundError(".env file not found")

    with open(path) as f:
        for line in f:
            line = line.strip()

            # Ignore empty lines or comments
            if not line or line.startswith("#"):
                continue

            # Only keep valid KEY=VALUE lines
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            os.environ[key] = value


def upload_images(client, channel_id, images_dir):
    """
    This function is responsible for Part 2 of the assignment.

    When the bot starts, it:
    - scans the images folder
    - selects all valid image files
    - uploads them one by one to the Slack channel

    This is done once at startup to avoid spamming the channel.
    """

    # Supported image formats
    extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    # We only keep real files with valid extensions
    images = [
        img for img in images_dir.iterdir()
        if img.is_file() and img.suffix.lower() in extensions
    ]

    # The assignment explicitly requires at least 3 images
    if len(images) < 3:
        raise ValueError("At least 3 images are required")

    for image in images:
        client.files_upload_v2(
            channel=channel_id,
            file=str(image),
            title=image.name
        )

        # Small delay to respect Slack rate limits
        time.sleep(0.3)


def wikipedia_first_paragraph(title):
    """
    This function handles Part 3 of the assignment.

    It queries Wikipedia's REST API and returns
    the first paragraph of the requested article.

    The User-Agent header is mandatory:
    without it, Wikipedia may block the request.
    """

    if not title:
        return "Wikipedia title missing."

    # Wikipedia REST endpoint for article summaries
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}"

    headers = {
        "User-Agent": "AlbertSchool-HeadOfDataBot/1.0 (student project)"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 404:
        return f"No Wikipedia page found for: {title}"

    if not response.ok:
        return f"Error fetching Wikipedia data ({response.status_code})"

    data = response.json()

    # Wikipedia returns the full introduction in one field
    extract = data.get("extract", "")

    # We only keep the first paragraph for readability
    return extract.split("\n\n")[0]


def main():
    """
    This is the main entry point of the program.

    The logic is intentionally simple and linear:
    1. Load configuration
    2. Upload images
    3. Start listening to Slack messages
    """

    # Load environment variables (.env)
    load_env()

    # Retrieve configuration values
    bot_token = os.environ["SLACK_BOT_TOKEN"]
    app_token = os.environ["SLACK_APP_TOKEN"]
    channel_id = os.environ["GROUP_CHANNEL_ID"]
    images_dir = Path(os.environ.get("IMAGES_DIR", "./images"))

    # Slack Web API client
    client = WebClient(token=bot_token)

    # Part 2: upload images when the bot starts
    upload_images(client, channel_id, images_dir)

    # Initialize the Slack Bolt app
    app = App(token=bot_token)

    @app.event("message")
    def handle_message(event, say):
        """
        This function is triggered every time a message
        is posted in a channel where the bot is present.

        We filter messages carefully to avoid:
        - responding to bots
        - responding to itself
        """

        text = event.get("text", "")

        # Ignore bot messages (including the bot itself)
        if event.get("bot_id") or event.get("subtype") == "bot_message":
            return

        # Only react to messages following the expected format
        if text.startswith("Wikipedia:"):
            title = text.replace("Wikipedia:", "").strip()
            result = wikipedia_first_paragraph(title)
            say(result)

    """
    Socket Mode keeps the application alive and connected
    to Slack without exposing a public HTTP server.

    This is particularly convenient in a student context
    where local execution is preferred.
    """
    SocketModeHandler(app, app_token).start()


if __name__ == "__main__":
    main()
