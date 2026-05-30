# Cron 定时分析配置指南

> 通过定时任务实现自动化长线趋势扫描，不依赖人工每次触发。

## 设计原则

- 长线分析的天然节奏是**每周一次**（周线收盘后）
- 日线辅助扫描可设为**每日一次**（日线收盘后）
- 不设高频扫描（4H 以下不适用）
- 报告写入本地文件，支持历史回看

## OpenClaw 定时任务配置

### 周线主分析（每周一早上执行）

```
/cron "每周一 09:00 对 BTC/USDT 和 ETH/USDT 执行长线趋势分析，输出报告到 reports/{date}/"
```

### 日线辅助检查（每日执行）

```
/cron "每日 09:00 检查 BTC/USDT 日线关键位是否触发，如有变化则补充到最新周报"
```

### 山寨币月度扫描

```
/cron "每月 1 号 09:00 对关注列表中的山寨币执行基本面复查，重点检查解锁事件"
```

## 传统 Cron 配置（备选）

如果 OpenClaw cron 不可用，使用系统 crontab：

```bash
# 每周一 09:00 UTC+8 — 周线分析
0 9 * * 1 openclaw run "分析 BTC/USDT 和 ETH/USDT 的周线趋势，输出报告" >> ~/hermes-reports/weekly.log 2>&1

# 每日 09:00 — 日线关键位检查
0 9 * * * openclaw run "检查 BTC/USDT 日线关键位" >> ~/hermes-reports/daily.log 2>&1

# 每月 1 号 — 山寨币解锁检查
0 9 1 * * openclaw run "检查关注列表山寨币未来 30 天解锁事件" >> ~/hermes-reports/unlock-check.log 2>&1
```

## 报告归档

```
~/hermes-reports/
├── weekly/
│   ├── 2026-W22/
│   │   ├── BTC-USDT.md
│   │   └── ETH-USDT.md
│   └── 2026-W23/
├── daily/
│   └── 2026-05-29.md
└── monthly/
    └── 2026-05-altcoin-review.md
```
