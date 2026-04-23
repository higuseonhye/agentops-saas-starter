import os

import httpx


API_BASE = os.getenv("AGENTOPS_API_BASE", "http://localhost:8000")
API_KEY = os.getenv("AGENTOPS_API_KEY", "")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
ALERT_ACCURACY_THRESHOLD = float(os.getenv("ALERT_ACCURACY_THRESHOLD", "0.7"))
ALERT_DAILY_COST_THRESHOLD = float(os.getenv("ALERT_DAILY_COST_THRESHOLD", "50.0"))


def send_alert(text: str):
    if not SLACK_WEBHOOK_URL:
        print(f"[ALERT-MOCK] {text}")
        return
    httpx.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10.0)


def main():
    if not API_KEY:
        raise RuntimeError("AGENTOPS_API_KEY is required.")

    headers = {"x-api-key": API_KEY}
    perf = httpx.get(f"{API_BASE}/performance", headers=headers, timeout=10.0).json()
    usage = httpx.get(f"{API_BASE}/usage", headers=headers, timeout=10.0).json()

    accuracy = float(perf["accuracy"])
    today_cost = float(usage["daily_cost"][-1]) if usage["daily_cost"] else 0.0

    if accuracy < ALERT_ACCURACY_THRESHOLD:
        send_alert(f":warning: Accuracy dropped to {accuracy:.2f}")
    if today_cost > ALERT_DAILY_COST_THRESHOLD:
        send_alert(f":money_with_wings: Daily cost spike detected: ${today_cost:.2f}")

    print("Alert check done.")


if __name__ == "__main__":
    main()
