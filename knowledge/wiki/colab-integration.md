---
title: Colab CLI 與 MCP 連接評估
sources:
  - knowledge/raw/colab-cli-mcp-evaluation-2026-11-25.md
updated: 2026-11-25
---

# Colab CLI 與 MCP 連接評估

Google 官方提供 Colab CLI 與 Colab MCP 伺服器兩種做法。費用與雲端額度相關限制見 [[gcp-free-tier]]。

> "可用，但只適合在 hachi 的本機環境執行；雲端容器沒有瀏覽器分頁與個人 ADC，不適用。" — knowledge/raw/colab-cli-mcp-evaluation-2026-11-25.md

## 實測

> "先執行 gcloud auth application-default login 並授權四個範圍後，new、exec、stop、usage 皆可用。" — knowledge/raw/colab-cli-mcp-evaluation-2026-11-25.md

## 風險

> "加速器 VM 會持續消耗運算單元，直到執行 colab stop。" — knowledge/raw/colab-cli-mcp-evaluation-2026-11-25.md

> "colab drivemount 會把 Drive 暴露給 VM，與「不得進入 private 資料夾」的規則衝突，只能掛載專用資料夾。" — knowledge/raw/colab-cli-mcp-evaluation-2026-11-25.md
