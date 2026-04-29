# Bolna Slack Alert Integration

A webhook server that sends Slack alerts whenever a Bolna voice AI call ends, capturing the call **id**, **agent_id**, **duration**, and **transcript**.

## How It Works

```
Bolna Call Ends → Webhook POST → FastAPI Server → Slack Alert
                                       ↓
                                  PostgreSQL (audit log)
```

1. Bolna fires a webhook on every call status change
2. Server filters for `completed` status (when transcript is fully available)
3. Extracts id, agent_id, duration, and transcript from the payload
4. Sends a formatted Slack message via Incoming Webhook
5. Stores the call log in PostgreSQL for audit

For long transcripts that exceed Slack's character limit, the message is automatically split into multiple connected parts.

## Live

- **Server**: https://bolna-alerts.mayank06711.xyz
- **Health**: https://bolna-alerts.mayank06711.xyz/health
- **Webhook**: `POST https://bolna-alerts.mayank06711.xyz/api/v1/webhook`

## Slack Alert Screenshots

_Screenshots attached below_

## Setup

### Prerequisites
- Docker & Docker Compose
- Bolna API key ([bolna.ai](https://bolna.ai) → Developers → Create API Key)
- Slack Incoming Webhook URL ([api.slack.com/apps](https://api.slack.com/apps))

### Run

```bash
# Clone
git clone https://github.com/Mayank06711/bolna-slack-integration.git
cd bolna-slack-integration

# Create .env from template
cp .env.example .env
# Fill in your BOLNA_API_KEY, BOLNA_AGENT_ID, SLACK_WEBHOOK_URL

# Start (app + postgres)
docker compose up -d --build

# Run database migration
docker exec bolna-app alembic upgrade head

# Verify
curl http://localhost:8000/health
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `BOLNA_API_KEY` | Bolna API bearer token |
| `BOLNA_AGENT_ID` | Agent UUID |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |
| `DATABASE_URL` | PostgreSQL connection string (auto-configured in Docker) |
| `ENABLE_IP_WHITELIST` | Restrict webhook to Bolna's IP (default: false) |

### Configure Bolna Webhook

1. Open your agent on [bolna.ai](https://bolna.ai)
2. Go to **Analytics** tab
3. Set webhook URL to your server's `/api/v1/webhook` endpoint
4. Save

## Tech Stack

- **FastAPI** — async webhook server
- **PostgreSQL** — call log storage
- **httpx** — async HTTP client for Slack
- **SQLAlchemy** — async ORM with connection pooling
- **Alembic** — database migrations
- **Docker** — containerized deployment
