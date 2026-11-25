# Gemini 金鑰可用模型檢查（2026-11-25）

- 執行者：GitHub Actions（scripts/gemini_model_check.py，金鑰未寫入本檔）
- 測試方式：`models.list` 取得清單後，對同一批 23 個文字與影像模型各做一次最小 `generateContent` 呼叫，只確認有回應（影像模型不生成圖片，輸出上限 8 tokens）

## 結果

合計測試 23 個，可用 23 個，失敗 0 個。

| 模型 | 類型 | 結果 | HTTP | 說明 |
| :--- | :--- | :--- | :--- | :--- |
| `gemini-3.8-flash` | 文字 | 可用 | 200 | 有回應（MAX_TOKENS） |
| `gemini-3.7-flash` | 文字 | 可用 | 200 | 有回應（MAX_TOKENS） |
| `gemini-3.6-flash` | 文字 | 可用 | 200 | 有回應（MAX_TOKENS） |
| `gemini-3.5-flash` | 文字 | 可用 | 200 | 有回應（MAX_TOKENS） |
| `gemini-3.5-flash-lite` | 文字 | 可用 | 200 | 有回應：OK |
| `gemini-3-flash-preview` | 文字 | 可用 | 200 | 有回應（MAX_TOKENS） |
| `gemini-3.1-flash-lite` | 文字 | 可用 | 200 | 有回應：OK |
| `gemini-3.1-pro-preview` | 文字 | 可用 | 200 | 有回應（MAX_TOKENS） |
| `gemini-2.5-pro` | 文字 | 可用 | 200 | 有回應（MAX_TOKENS） |
| `gemini-2.5-flash` | 文字 | 可用 | 200 | 有回應：OK |
| `gemini-2.5-flash-lite` | 文字 | 可用 | 200 | 有回應：OK |
| `gemini-4-argon` | 文字 | 可用 | 200 | 有回應：OK |
| `gemini-4-carbon` | 文字 | 可用 | 200 | 有回應（MAX_TOKENS） |
| `gemini-4-hydrogen` | 文字 | 可用 | 200 | 有回應（MAX_TOKENS） |
| `gemini-pro-latest` | 文字 | 可用 | 200 | 有回應（MAX_TOKENS） |
| `gemini-flash-latest` | 文字 | 可用 | 200 | 有回應（MAX_TOKENS） |
| `gemini-3.1-flash-image` | 影像 | 可用 | 200 | 有回應：OK |
| `gemini-3.1-flash-image-preview` | 影像 | 可用 | 200 | 有回應：OK |
| `gemini-3-pro-image-preview` | 影像 | 可用 | 200 | 有回應（STOP） |
| `gemini-3-pro-image` | 影像 | 可用 | 200 | 有回應（STOP） |
| `nano-banana-pro-preview` | 影像 | 可用 | 200 | 有回應（STOP） |
| `gemini-2.5-flash-image` | 影像 | 可用 | 200 | 有回應：OK |
| `gemini-nano-banana-2.1` | 影像 | 可用 | 200 | 有回應（STOP） |

## 與 2026-11-25 紀錄比較

- 金鑰可見模型由 65 個變為 65 個，支援 `generateContent` 的由 49 個變為 49 個。
- 新增可見：無。
- 不再出現：無。

## 附錄：支援 generateContent 的模型

- `antigravity-preview-05-2026`
- `antigravity-preview-09-2026`
- `antigravity-preview-latest`
- `deep-research-max-preview-04-2026`
- `deep-research-preview-04-2026`
- `gemini-2.5-computer-use-preview-10-2025`
- `gemini-2.5-flash`
- `gemini-2.5-flash-image`
- `gemini-2.5-flash-lite`
- `gemini-2.5-flash-preview-tts`
- `gemini-2.5-pro`
- `gemini-2.5-pro-preview-tts`
- `gemini-3-flash-preview`
- `gemini-3-pro-image`
- `gemini-3-pro-image-preview`
- `gemini-3.1-flash-image`
- `gemini-3.1-flash-image-preview`
- `gemini-3.1-flash-lite`
- `gemini-3.1-flash-lite-image`
- `gemini-3.1-flash-lite-preview`
- `gemini-3.1-flash-tts-preview`
- `gemini-3.1-pro-preview`
- `gemini-3.1-pro-preview-customtools`
- `gemini-3.5-flash`
- `gemini-3.5-flash-lite`
- `gemini-3.5-transcribe`
- `gemini-3.6-flash`
- `gemini-3.7-flash`
- `gemini-3.8-flash`
- `gemini-3.8-flash-lite-tts`
- `gemini-3.8-flash-tts`
- `gemini-4-argon`
- `gemini-4-carbon`
- `gemini-4-hydrogen`
- `gemini-4-neon`
- `gemini-flash-latest`
- `gemini-flash-lite-latest`
- `gemini-nano-banana-2.1`
- `gemini-omni-1.1-flash`
- `gemini-omni-1.2-flash`
- `gemini-omni-flash-preview`
- `gemini-pro-latest`
- `gemini-robotics-er-2-preview`
- `gemma-4-26b-a4b-it`
- `gemma-4-31b-it`
- `lyria-3-clip-preview`
- `lyria-3-pro-preview`
- `lyria-3.5`
- `nano-banana-pro-preview`
