# Security

Do not commit credentials, account numbers, broker tokens, API keys, private endpoints, or VPS paths.

The core framework does not require an API key. Keep local credentials in `.env`, which is ignored by Git.

If a sensitive value is committed, rotate it immediately before relying on Git history cleanup.
