# Gemini 模型可用性檢查整理（2026-11-14）

來源：專案檔 gemini-test/gemini-model-check-2026-11-14.md。金鑰本身未寫入。

## 重點結論

- 測試 23 個文字與影像模型，23 個可用，失敗 0 個。
- 與 2026-10-14 紀錄中的 6 個模型比較，全部仍可用。
- 金鑰共可見 64 個模型，其中 49 個支援 generateContent。

## 測試方法

1. 用 models.list 取得清單。
2. 文字與影像系列各做一次最小 generateContent 呼叫。
3. 文字提示：Reply with exactly one word: OK
4. 影像提示：Generate a tiny 64x64 solid red square image.

## 文字模型（16 個，全部回覆 OK）

| 系列 | 模型 |
| :--- | :--- |
| Gemini 4 | gemini-4-argon、gemini-4-carbon、gemini-4-hydrogen |
| Gemini 3.x Flash | gemini-3.8-flash、gemini-3.7-flash、gemini-3.6-flash、gemini-3.5-flash、gemini-3-flash-preview |
| Gemini 3.x Lite | gemini-3.5-flash-lite、gemini-3.1-flash-lite |
| Gemini 3.1 Pro | gemini-3.1-pro-preview |
| Gemini 2.5 | gemini-2.5-pro、gemini-2.5-flash、gemini-2.5-flash-lite |
| 別名 | gemini-pro-latest、gemini-flash-latest |

## 影像模型（7 個，全部回傳 1 張圖片）

gemini-3.1-flash-image、gemini-3.1-flash-image-preview、gemini-3-pro-image、gemini-3-pro-image-preview、nano-banana-pro-preview、gemini-2.5-flash-image、gemini-nano-banana-2.1

## 其他支援 generateContent 的類別（未逐一測試）

- 語音與轉錄：TTS 系列、gemini-3.5-transcribe
- 研究與代理：deep-research 系列、antigravity-preview 系列、computer-use、robotics-er
- 音樂：lyria 系列
- 開放權重：gemma-4 系列
- 多模態：omni 系列

## 維護方式

- 每月重測一次並更新本整理（對應 Jira HAC-11）。
- Drive 上有同名 Google 文件副本，更新任一份時另一份也要同步。
