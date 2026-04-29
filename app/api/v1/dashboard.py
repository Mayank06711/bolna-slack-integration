from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.models.database import CallLog
from app.api.dependencies import get_db_session

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root_dashboard(session: AsyncSession = Depends(get_db_session)):
    # Get total alerts and last alert time
    result = await session.execute(
        select(
            func.count(CallLog.id),
            func.max(CallLog.created_at),
        ).where(CallLog.slack_notified == True)
    )
    total_alerts, last_alert_at = result.one()

    last_alert_str = last_alert_at.strftime("%Y-%m-%d %H:%M:%S UTC") if last_alert_at else "No alerts yet"

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Bolna Slack Alerts</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0f1117;
            color: #e1e4e8;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }}
        .card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 48px;
            text-align: center;
            max-width: 480px;
        }}
        h1 {{ color: #58a6ff; margin-bottom: 8px; font-size: 28px; }}
        .subtitle {{ color: #8b949e; margin-bottom: 32px; }}
        .stat {{
            font-size: 64px;
            font-weight: bold;
            color: #3fb950;
            margin: 16px 0;
        }}
        .label {{ color: #8b949e; font-size: 14px; }}
        .last-alert {{ color: #8b949e; font-size: 13px; margin-top: 24px; }}
        .footer {{ color: #484f58; font-size: 12px; margin-top: 32px; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Bolna Slack Alerts</h1>
        <p class="subtitle">by Mayank Soni</p>
        <div class="stat">{total_alerts}</div>
        <div class="label">Slack alerts sent</div>
        <div class="last-alert">Last alert: {last_alert_str}</div>
        <div class="footer">Bolna Call Webhook &rarr; Slack Integration</div>
    </div>
</body>
</html>"""
