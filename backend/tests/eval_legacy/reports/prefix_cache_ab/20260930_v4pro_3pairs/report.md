# TaskMind 前缀保护专项 A/B 评测

- Provider：`deepseek`
- Model：`deepseek-v4-pro`
- 配对数：3
- 生成时间：2026-09-29T16:44:33.811213+00:00

## 评测口径

- 场景：长历史 + 4 轮顺序依赖文件读取，输入跨过软压缩线但尽量不越过强制线。
- 对照组：关闭 TaskMind Run 内请求前缀复用，软线处允许立即压缩。
- 实验组：开启前缀复用，前缀稳定时允许 defer。
- 隔离：每个实验臂使用不同的早期 cache namespace；每对交替执行顺序。
- 主指标：排除第一次模型调用后，主模型输入 token 的加权缓存命中率。
- 诊断指标：首次软压缩压力转折点的加权缓存命中率。

## 结果

| 指标 | 对照组（rebuild） | 实验组（reuse） |
|---|---:|---:|
| 完整通过 | 3/3 | 3/3 |
| 观察到软线转折 | 3/3 | 3/3 |
| 第二次及后续主调用缓存命中率 | 48.2% | 88.7% |
| 第二次及后续 cached/input tokens | 27648/57370 | 110976/125161 |
| 软线转折调用缓存命中率 | 10.1% | 92.2% |
| 软线转折 cached/input tokens | 1152/11408 | 26112/28317 |
| Provider 可计费 token 近似值 | 56291 | 39998 |
| 总耗时 | 30.1s | 23.9s |

- 有效配对：3/3。
- 对照组决策计数：`{'rebuild': 9, 'compact': 6}`。
- 实验组决策计数：`{'rebuild': 3, 'defer': 12}`。

## 观察结论

- 第二次及后续主调用缓存命中率提高 40.5 个百分点。
- 软线转折调用缓存命中率提高 82.1 个百分点。
- Provider 可计费 token 近似值减少 28.9%。

## 解释边界

只有两组都完成工具链、都观察到软线转折，并且实验组出现 defer、对照组出现 compact/rebuild，才能把命中率差异用于支持前缀保护机制。Provider 缓存是尽力而为，三对样本仍属于专项离线证据，不代表生产流量。

## 逐次运行

| Pair | Arm | Pass | Steps | Transition | Post-first cache | Chargeable |
|---:|---|---:|---:|---|---:|---:|
| 1 | rebuild | PASS | 5 | step=2, decision=compact, cache=10.1% | 48.2% | 18757 |
| 1 | reuse | PASS | 5 | step=2, decision=defer, cache=92.3% | 88.8% | 13174 |
| 2 | reuse | PASS | 5 | step=2, decision=defer, cache=92.0% | 88.5% | 13522 |
| 2 | rebuild | PASS | 5 | step=2, decision=compact, cache=10.1% | 48.1% | 18881 |
| 3 | rebuild | PASS | 5 | step=2, decision=compact, cache=10.1% | 48.3% | 18653 |
| 3 | reuse | PASS | 5 | step=2, decision=defer, cache=92.3% | 88.7% | 13302 |
