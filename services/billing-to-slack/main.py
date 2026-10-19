import base64
import json
import os
import urllib.request
try:
    import functions_framework
except ImportError:
    # 支援未安裝 functions_framework 的測試環境之 fallback
    class _DummyFramework:
        @staticmethod
        def cloud_event(fn):
            return fn

    functions_framework = _DummyFramework()

# Webhook 一律由環境變數 SLACK_WEBHOOK_URL 提供（部署時設定），程式碼不內嵌任何網址
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")


def evaluate_billing_payload(data: dict):
    """解析並評估帳單預算資料，若未達 50% 門檻則回傳 None（不發送通知）。"""
    cost = data.get("costAmount", 0)
    budget = data.get("budgetAmount", 0)
    currency = data.get("currencyCode", "TWD")
    name = data.get("budgetDisplayName", "每月預算")

    pct = (cost / budget * 100) if budget and budget > 0 else 0

    # 預測門檻：只在預測花費達 100% 時通知；預測 50%／90% 的通知不發送
    forecast = data.get("forecastThresholdExceeded")
    if forecast is not None and forecast >= 1.0 and pct < 100:
        return {
            "text": f"📈 *【GCP 帳單預算：預測本月花費將達 100%】*\n• 預算名稱：{name}\n• 目前花費：{cost:.2f} {currency} ({pct:.1f}%)\n• 設定限額：{budget:.2f} {currency}",
            "attachments": [
                {
                    "color": "#ff9900",
                    "fields": [
                        {"title": "預算名稱", "value": str(name), "short": True},
                        {"title": "目前花費", "value": f"{cost:.2f} {currency}", "short": True},
                        {"title": "消耗比例", "value": f"{pct:.1f}%", "short": True},
                        {"title": "設定預算", "value": f"{budget:.2f} {currency}", "short": True},
                    ],
                }
            ],
        }

    # 門檻過濾：未達 50% 警報門檻不發送，避免平日每 30~60 分鐘定時計算洗版
    if pct < 50:
        print(f"目前花費比例 {pct:.1f}% 未達 50% 警報門檻，略過推播。")
        return None

    if pct >= 100:
        color = "#ff0000"
        status_text = "🚨 *【GCP 帳單預算達到 100% 警戒】*"
    elif pct >= 90:
        color = "#ff9900"
        status_text = "⚠️ *【GCP 帳單預算達到 90% 提醒】*"
    else:  # pct >= 50
        color = "#eed202"
        status_text = "ℹ️ *【GCP 帳單預算達到 50% 提醒】*"

    payload = {
        "text": f"{status_text}\n• 預算名稱：{name}\n• 目前花費：{cost:.2f} {currency} ({pct:.1f}%)\n• 設定限額：{budget:.2f} {currency}",
        "attachments": [
            {
                "color": color,
                "fields": [
                    {"title": "預算名稱", "value": str(name), "short": True},
                    {"title": "目前花費", "value": f"{cost:.2f} {currency}", "short": True},
                    {"title": "消耗比例", "value": f"{pct:.1f}%", "short": True},
                    {"title": "設定預算", "value": f"{budget:.2f} {currency}", "short": True},
                ],
            }
        ],
    }
    return payload


@functions_framework.cloud_event
def notify_slack(cloud_event):
    raw_data = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
    data = json.loads(raw_data)

    payload = evaluate_billing_payload(data)
    if payload is None:
        return

    if not SLACK_WEBHOOK_URL:
        raise RuntimeError("未設定環境變數 SLACK_WEBHOOK_URL，無法發送 Slack 通知")

    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req)
