```markdown
# Technical Notes & Decisions

## Why Socket Mode?
Using Socket Mode allows the application to run locally without exposing a public HTTP endpoint.
This is particularly useful in a student environment and simplifies development.

## Why Slack Bolt?
Slack Bolt provides a clean abstraction for:
- Handling events
- Managing authentication
- Writing readable and maintainable code

## Image upload logic
Images are uploaded once at startup to avoid duplicates.
A small delay is added between uploads to respect Slack rate limits.

## Wikipedia API issue
During development, Wikipedia requests initially failed.
This was due to missing HTTP headers.

Solution:
- Adding a proper User-Agent header, which is required by Wikipedia’s API policy.

## Error handling
Basic error handling is implemented:
- Missing `.env` file
- Missing images
- Non-existing Wikipedia pages

## What could be improved
- Add logging instead of print-based feedback
- Handle duplicate image uploads more elegantly
- Add slash commands instead of message parsing
