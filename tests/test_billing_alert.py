import sys
from pathlib import Path
import unittest

# 將 services/billing-to-slack 加入 sys.path
sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        / "services"
        / "billing-to-slack"
    ),
)
from main import evaluate_billing_payload


class TestBillingAlert(unittest.TestCase):
    def test_filter_below_threshold(self):
        """低於 50% 門檻時，應回傳 None 略過推播"""
        data = {
            "costAmount": 10.0,
            "budgetAmount": 100.0,
            "currencyCode": "TWD",
            "budgetDisplayName": "每月預算測試",
        }
        res = evaluate_billing_payload(data)
        self.assertIsNone(res)

    def test_filter_zero_cost(self):
        """花費為 0 時，應回傳 None 略過推播"""
        data = {
            "costAmount": 0.0,
            "budgetAmount": 100.0,
            "currencyCode": "TWD",
        }
        res = evaluate_billing_payload(data)
        self.assertIsNone(res)

    def test_trigger_50_percent(self):
        """花費達 50% 時，應觸發黃色 50% 提醒"""
        data = {
            "costAmount": 50.0,
            "budgetAmount": 100.0,
            "currencyCode": "TWD",
            "budgetDisplayName": "每月預算",
        }
        res = evaluate_billing_payload(data)
        self.assertIsNotNone(res)
        self.assertIn("50% 提醒", res["text"])
        self.assertEqual(res["attachments"][0]["color"], "#eed202")

    def test_trigger_90_percent(self):
        """花費達 90% 時，應觸發橙色 90% 提醒"""
        data = {
            "costAmount": 90.0,
            "budgetAmount": 100.0,
            "currencyCode": "TWD",
            "budgetDisplayName": "每月預算",
        }
        res = evaluate_billing_payload(data)
        self.assertIsNotNone(res)
        self.assertIn("90% 提醒", res["text"])
        self.assertEqual(res["attachments"][0]["color"], "#ff9900")

    def test_trigger_100_percent(self):
        """花費達 100% 時，應觸發紅色 100% 警戒"""
        data = {
            "costAmount": 105.0,
            "budgetAmount": 100.0,
            "currencyCode": "TWD",
            "budgetDisplayName": "每月預算",
        }
        res = evaluate_billing_payload(data)
        self.assertIsNotNone(res)
        self.assertIn("100% 警戒", res["text"])
        self.assertEqual(res["attachments"][0]["color"], "#ff0000")

    def test_forecast_100_percent_triggers_even_when_cost_low(self):
        """預測達 100% 時，即使實際花費很低也應通知"""
        data = {
            "costAmount": 10.0,
            "budgetAmount": 100.0,
            "currencyCode": "TWD",
            "budgetDisplayName": "每月預算",
            "forecastThresholdExceeded": 1.0,
        }
        res = evaluate_billing_payload(data)
        self.assertIsNotNone(res)
        self.assertIn("預測本月花費將達 100%", res["text"])

    def test_forecast_below_100_percent_is_skipped(self):
        """預測僅達 50%／90% 且實際花費低時，應略過推播"""
        for threshold in (0.5, 0.9):
            data = {
                "costAmount": 10.0,
                "budgetAmount": 100.0,
                "currencyCode": "TWD",
                "forecastThresholdExceeded": threshold,
            }
            self.assertIsNone(evaluate_billing_payload(data))

    def test_forecast_100_with_actual_over_100_uses_actual_alert(self):
        """實際花費已達 100% 時，使用實際警戒訊息，不重複發預測訊息"""
        data = {
            "costAmount": 105.0,
            "budgetAmount": 100.0,
            "currencyCode": "TWD",
            "forecastThresholdExceeded": 1.0,
        }
        res = evaluate_billing_payload(data)
        self.assertIn("100% 警戒", res["text"])


if __name__ == "__main__":
    unittest.main()
