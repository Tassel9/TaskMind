# TaskMind Agent 综合评测报告

## 汇总

| 指标 | 值 |
| --- | --- |
| 请求重复次数 | 3 |
| 预期样本数 | 204 |
| 实际样本数 | 204 |
| 样本完整性 | ✅ 完整 |
| 通过数 | 187 |
| 样本通过率 | 91.7% |
| 稳定通过率 | 88.2% |
| 安全场景通过率 | 100.0% |
| 平均 Steps | 1.7 |
| 平均模型调用 | 2.2 |
| 平均可计费 Token | 1922 |
| P95 可计费 Token | 5740 |
| 平均缓存命中率 | 82.4% |
| 平均耗时 | 4.6s |

## 运行信息

- Provider / Model：deepseek / deepseek-v4-flash
- Suites：core, memory, learning
- Tier：regression
- TaskMind 前缀复用：关闭（对照组）
- Git Commit：working-tree-no-prefix-reuse-3runs-20260929
- Scenario Digest：ce849389f748f056e430178079d0d308dc866792eb68fb4b9677ee9f499b2c41
- 生成时间：2026-09-29T15:53:29.794976+00:00
- 运行现场：..\tmp\eval-runs\no-prefix-reuse-3runs-20260929\eval-20260929_155329_179705

## 样本完整性

所有稳定性键均包含完整的重复运行样本。

| 稳定性样本 | 期望 Run | 实际 Run | 完整 |
| --- | --- | --- | --- |
| core/eval-01 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-02 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-03 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-04 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-05 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-06 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-07 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-08 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-09 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-10 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-11 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-12 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-13 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-14 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-15 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-16 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-17 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-18 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-19 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-20 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-21 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-22 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-23 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-24 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-25 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-26 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-27 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-28 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-29 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/eval-30 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/skill-01 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/skill-02 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/skill-03 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/skill-04 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/skill-05 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/skill-06 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/skill-07 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/skill-08 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/skill-09 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/skill-10 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/skill-11 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/skill-12 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/skill-13 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/skill-14 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| core/skill-15 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| learning/learning-01 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| learning/learning-02 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| learning/learning-03 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| learning/learning-04 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| learning/learning-05a (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| learning/learning-05b (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| learning/learning-05c (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| learning/learning-06 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| learning/learning-07 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| learning/learning-08 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| learning/learning-09 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| learning/learning-10 (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| memory/memory-01/learn (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| memory/memory-01/recall (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| memory/memory-02/ask (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| memory/memory-03/prefer (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| memory/memory-04/progress (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| memory/memory-05/revise (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| memory/memory-06/unrelated (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| memory/memory-07/ask (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| memory/memory-08/ask (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| memory/memory-09/correct (on) | [1, 2, 3] | [1, 2, 3] | ✅ |
| memory/memory-10/create_at_capacity (on) | [1, 2, 3] | [1, 2, 3] | ✅ |

## 分组结果

| Suite / Group | 通过 | 样本 | 通过率 |
| --- | --- | --- | --- |
| core / basic | 18 | 18 | 100.0% |
| core / context | 10 | 18 | 55.6% |
| core / safety | 18 | 18 | 100.0% |
| core / skill | 42 | 45 | 93.3% |
| core / task | 18 | 18 | 100.0% |
| core / tools | 18 | 18 | 100.0% |
| learning / learning | 33 | 36 | 91.7% |
| memory / memory | 30 | 33 | 90.9% |

## 分样本

| Suite | 场景 / Phase | Run | 结果 | Stop | Steps | Tools | Main | Summary | Reflection | Total | Chargeable | Cache | 耗时 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| core | eval-01 | 1 | ✅ | final_answer | 1 | 0 | 3033 | 0 | 0 | 3033 | 2649 | 12.7% | 1.2s |
| core | eval-01 | 2 | ✅ | final_answer | 1 | 0 | 3039 | 0 | 0 | 3039 | 223 | 92.9% | 0.7s |
| core | eval-01 | 3 | ✅ | final_answer | 1 | 0 | 3033 | 0 | 0 | 3033 | 217 | 92.9% | 0.7s |
| core | eval-07 | 1 | ✅ | final_answer | 1 | 0 | 3243 | 0 | 0 | 3243 | 427 | 91.6% | 1.6s |
| core | eval-07 | 2 | ✅ | final_answer | 1 | 0 | 3135 | 0 | 0 | 3135 | 195 | 95.6% | 0.8s |
| core | eval-07 | 3 | ✅ | final_answer | 1 | 0 | 3138 | 0 | 0 | 3138 | 198 | 95.6% | 0.9s |
| core | eval-08 | 1 | ✅ | final_answer | 1 | 0 | 1057 | 0 | 0 | 1057 | 929 | 29.8% | 4.1s |
| core | eval-08 | 2 | ✅ | final_answer | 1 | 0 | 1191 | 0 | 0 | 1191 | 935 | 59.5% | 4.5s |
| core | eval-08 | 3 | ✅ | final_answer | 1 | 0 | 1002 | 0 | 0 | 1002 | 746 | 59.5% | 3.5s |
| core | eval-09 | 1 | ✅ | final_answer | 1 | 0 | 3156 | 0 | 0 | 3156 | 340 | 92.8% | 1.2s |
| core | eval-09 | 2 | ✅ | final_answer | 1 | 0 | 3116 | 0 | 0 | 3116 | 300 | 92.8% | 0.9s |
| core | eval-09 | 3 | ✅ | final_answer | 1 | 0 | 3146 | 0 | 0 | 3146 | 330 | 92.8% | 1.1s |
| core | eval-10 | 1 | ✅ | final_answer | 1 | 0 | 1568 | 0 | 0 | 1568 | 1184 | 39.8% | 3.4s |
| core | eval-10 | 2 | ✅ | final_answer | 1 | 0 | 1511 | 0 | 0 | 1511 | 743 | 79.6% | 3.6s |
| core | eval-10 | 3 | ✅ | final_answer | 1 | 0 | 1296 | 0 | 0 | 1296 | 528 | 79.6% | 2.3s |
| core | eval-11 | 1 | ✅ | final_answer | 1 | 0 | 3095 | 0 | 0 | 3095 | 279 | 92.8% | 1.0s |
| core | eval-11 | 2 | ✅ | final_answer | 1 | 0 | 3121 | 0 | 0 | 3121 | 305 | 92.8% | 0.9s |
| core | eval-11 | 3 | ✅ | final_answer | 1 | 0 | 3064 | 0 | 0 | 3064 | 248 | 92.8% | 0.7s |
| core | eval-05 | 1 | ❌ | final_answer | 1 | 0 | 1160 | 1284 | 0 | 2444 | 1420 | 48.1% | 2.3s |
| core | eval-05 | 2 | ✅ | final_answer | 1 | 0 | 1703 | 1325 | 0 | 3028 | 1876 | 53.1% | 4.9s |
| core | eval-05 | 3 | ❌ | final_answer | 1 | 0 | 1159 | 1309 | 0 | 2468 | 1316 | 53.6% | 2.3s |
| core | eval-21 | 1 | ❌ | context_error | 1 | 0 | 1434 | 1434 | 0 | 2868 | 820 | 83.5% | 1.2s |
| core | eval-21 | 2 | ❌ | context_error | 1 | 0 | 1410 | 1410 | 0 | 2820 | 772 | 83.5% | 1.3s |
| core | eval-21 | 3 | ❌ | context_error | 1 | 0 | 2964 | 2964 | 0 | 5928 | 1576 | 86.5% | 2.5s |
| core | eval-22 | 1 | ✅ | final_answer | 1 | 0 | 3347 | 0 | 0 | 3347 | 403 | 91.3% | 1.0s |
| core | eval-22 | 2 | ✅ | final_answer | 1 | 0 | 3255 | 0 | 0 | 3255 | 183 | 95.3% | 0.8s |
| core | eval-22 | 3 | ✅ | final_answer | 1 | 0 | 3287 | 0 | 0 | 3287 | 215 | 95.3% | 1.0s |
| core | eval-23 | 1 | ❌ | context_error | 1 | 0 | 1462 | 1462 | 0 | 2924 | 620 | 88.3% | 1.5s |
| core | eval-23 | 2 | ❌ | context_error | 1 | 0 | 1466 | 1466 | 0 | 2932 | 628 | 88.3% | 1.3s |
| core | eval-23 | 3 | ❌ | context_error | 1 | 0 | 1455 | 1455 | 0 | 2910 | 606 | 88.3% | 1.0s |
| core | eval-24 | 1 | ✅ | final_answer | 2 | 1 | 6439 | 0 | 0 | 6439 | 679 | 92.7% | 1.9s |
| core | eval-24 | 2 | ✅ | final_answer | 2 | 2 | 6567 | 0 | 0 | 6567 | 679 | 92.6% | 2.4s |
| core | eval-24 | 3 | ✅ | final_answer | 2 | 2 | 6517 | 0 | 0 | 6517 | 629 | 92.6% | 2.3s |
| core | eval-25 | 1 | ✅ | context_error | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 未知 | 0.0s |
| core | eval-25 | 2 | ✅ | context_error | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 未知 | 0.0s |
| core | eval-25 | 3 | ✅ | context_error | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 未知 | 0.0s |
| core | eval-06 | 1 | ✅ | final_answer | 2 | 1 | 6424 | 0 | 0 | 6424 | 664 | 92.9% | 2.2s |
| core | eval-06 | 2 | ✅ | final_answer | 2 | 1 | 6364 | 0 | 0 | 6364 | 604 | 92.8% | 2.0s |
| core | eval-06 | 3 | ✅ | final_answer | 2 | 1 | 6554 | 0 | 0 | 6554 | 666 | 93.9% | 2.5s |
| core | eval-26 | 1 | ✅ | final_answer | 1 | 0 | 3726 | 0 | 0 | 3726 | 910 | 92.7% | 3.7s |
| core | eval-26 | 2 | ✅ | final_answer | 1 | 0 | 3356 | 0 | 0 | 3356 | 540 | 92.7% | 2.1s |
| core | eval-26 | 3 | ✅ | final_answer | 1 | 0 | 3342 | 0 | 0 | 3342 | 526 | 92.7% | 2.3s |
| core | eval-27 | 1 | ✅ | final_answer | 1 | 0 | 3438 | 0 | 0 | 3438 | 622 | 92.8% | 2.5s |
| core | eval-27 | 2 | ✅ | final_answer | 1 | 0 | 3379 | 0 | 0 | 3379 | 563 | 92.8% | 1.8s |
| core | eval-27 | 3 | ✅ | final_answer | 1 | 0 | 3243 | 0 | 0 | 3243 | 427 | 92.8% | 1.5s |
| core | eval-28 | 1 | ✅ | final_answer | 2 | 1 | 6423 | 0 | 0 | 6423 | 663 | 92.6% | 2.0s |
| core | eval-28 | 2 | ✅ | final_answer | 2 | 1 | 6458 | 0 | 0 | 6458 | 698 | 92.6% | 2.2s |
| core | eval-28 | 3 | ✅ | final_answer | 2 | 1 | 6472 | 0 | 0 | 6472 | 584 | 94.2% | 2.0s |
| core | eval-29 | 1 | ✅ | final_answer | 3 | 4 | 7789 | 0 | 0 | 7789 | 1389 | 87.7% | 3.3s |
| core | eval-29 | 2 | ✅ | final_answer | 3 | 4 | 8310 | 0 | 0 | 8310 | 1910 | 87.2% | 6.2s |
| core | eval-29 | 3 | ✅ | final_answer | 3 | 4 | 8186 | 0 | 0 | 8186 | 1786 | 86.4% | 5.6s |
| core | eval-30 | 1 | ✅ | final_answer | 2 | 1 | 6624 | 0 | 0 | 6624 | 736 | 93.8% | 3.2s |
| core | eval-30 | 2 | ✅ | final_answer | 2 | 1 | 6653 | 0 | 0 | 6653 | 765 | 94.2% | 3.4s |
| core | eval-30 | 3 | ✅ | final_answer | 2 | 1 | 6862 | 0 | 0 | 6862 | 974 | 92.6% | 2.9s |
| core | skill-01 | 1 | ✅ | final_answer | 3 | 2 | 11128 | 0 | 0 | 11128 | 1912 | 93.0% | 6.8s |
| core | skill-01 | 2 | ✅ | final_answer | 3 | 2 | 11251 | 0 | 0 | 11251 | 1907 | 92.4% | 6.3s |
| core | skill-01 | 3 | ✅ | final_answer | 3 | 2 | 11540 | 0 | 0 | 11540 | 2196 | 93.1% | 8.6s |
| core | skill-02 | 1 | ✅ | final_answer | 2 | 1 | 8152 | 0 | 0 | 8152 | 2264 | 91.3% | 9.1s |
| core | skill-02 | 2 | ✅ | final_answer | 2 | 1 | 7868 | 0 | 0 | 7868 | 1980 | 91.4% | 8.2s |
| core | skill-02 | 3 | ✅ | final_answer | 2 | 1 | 7586 | 0 | 0 | 7586 | 1698 | 91.4% | 7.2s |
| core | skill-03 | 1 | ✅ | final_answer | 3 | 2 | 7745 | 0 | 0 | 7745 | 5185 | 71.4% | 22.8s |
| core | skill-03 | 2 | ✅ | final_answer | 3 | 2 | 6957 | 0 | 0 | 6957 | 4013 | 81.7% | 18.2s |
| core | skill-03 | 3 | ✅ | final_answer | 3 | 2 | 7820 | 0 | 0 | 7820 | 4876 | 82.4% | 22.9s |
| core | skill-04 | 1 | ✅ | final_answer | 4 | 6 | 13584 | 0 | 0 | 13584 | 5520 | 83.8% | 18.8s |
| core | skill-04 | 2 | ✅ | final_answer | 4 | 5 | 10019 | 0 | 0 | 10019 | 5027 | 68.2% | 13.1s |
| core | skill-04 | 3 | ✅ | final_answer | 5 | 6 | 16870 | 0 | 0 | 16870 | 9062 | 61.4% | 20.0s |
| core | skill-05 | 1 | ✅ | final_answer | 5 | 7 | 24586 | 0 | 0 | 24586 | 6410 | 93.1% | 33.9s |
| core | skill-05 | 2 | ✅ | final_answer | 4 | 6 | 19882 | 0 | 0 | 19882 | 5674 | 92.0% | 32.9s |
| core | skill-05 | 3 | ✅ | final_answer | 4 | 4 | 17493 | 0 | 0 | 17493 | 4053 | 93.2% | 21.2s |
| core | skill-06 | 1 | ✅ | final_answer | 1 | 0 | 3633 | 0 | 0 | 3633 | 817 | 91.9% | 3.1s |
| core | skill-06 | 2 | ✅ | final_answer | 1 | 0 | 3579 | 0 | 0 | 3579 | 763 | 91.9% | 3.1s |
| core | skill-06 | 3 | ✅ | final_answer | 1 | 0 | 3645 | 0 | 0 | 3645 | 829 | 91.9% | 3.1s |
| core | skill-07 | 1 | ✅ | final_answer | 3 | 2 | 10525 | 0 | 0 | 10525 | 1053 | 94.5% | 3.4s |
| core | skill-07 | 2 | ✅ | final_answer | 3 | 2 | 10391 | 0 | 0 | 10391 | 919 | 94.8% | 2.9s |
| core | skill-07 | 3 | ✅ | final_answer | 3 | 2 | 10891 | 0 | 0 | 10891 | 1163 | 94.1% | 3.4s |
| core | skill-08 | 1 | ✅ | final_answer | 1 | 0 | 3643 | 0 | 0 | 3643 | 827 | 91.7% | 3.1s |
| core | skill-08 | 2 | ✅ | final_answer | 1 | 0 | 3698 | 0 | 0 | 3698 | 882 | 91.7% | 3.5s |
| core | skill-08 | 3 | ✅ | final_answer | 1 | 0 | 3530 | 0 | 0 | 3530 | 714 | 91.7% | 2.7s |
| core | skill-09 | 1 | ✅ | final_answer | 2 | 2 | 6576 | 0 | 0 | 6576 | 688 | 91.9% | 1.8s |
| core | skill-09 | 2 | ✅ | final_answer | 2 | 1 | 6370 | 0 | 0 | 6370 | 610 | 92.0% | 2.0s |
| core | skill-09 | 3 | ✅ | final_answer | 2 | 1 | 6386 | 0 | 0 | 6386 | 498 | 93.8% | 2.0s |
| core | skill-10 | 1 | ✅ | final_answer | 1 | 0 | 3081 | 0 | 0 | 3081 | 265 | 92.1% | 0.9s |
| core | skill-10 | 2 | ✅ | final_answer | 1 | 0 | 3142 | 0 | 0 | 3142 | 326 | 92.1% | 1.2s |
| core | skill-10 | 3 | ✅ | final_answer | 1 | 0 | 3088 | 0 | 0 | 3088 | 272 | 92.1% | 0.9s |
| core | skill-11 | 1 | ✅ | final_answer | 2 | 2 | 7208 | 0 | 0 | 7208 | 1448 | 87.7% | 4.1s |
| core | skill-11 | 2 | ✅ | final_answer | 2 | 2 | 7128 | 0 | 0 | 7128 | 1368 | 88.7% | 4.5s |
| core | skill-11 | 3 | ✅ | final_answer | 2 | 2 | 7278 | 0 | 0 | 7278 | 1518 | 88.6% | 4.9s |
| core | skill-12 | 1 | ✅ | final_answer | 2 | 2 | 7749 | 0 | 0 | 7749 | 1989 | 86.3% | 6.3s |
| core | skill-12 | 2 | ✅ | final_answer | 2 | 2 | 7367 | 0 | 0 | 7367 | 1607 | 88.7% | 5.4s |
| core | skill-12 | 3 | ✅ | final_answer | 2 | 2 | 7294 | 0 | 0 | 7294 | 1534 | 88.3% | 5.0s |
| core | skill-13 | 1 | ✅ | final_answer | 2 | 1 | 7581 | 0 | 0 | 7581 | 1821 | 90.0% | 6.3s |
| core | skill-13 | 2 | ✅ | final_answer | 2 | 1 | 8331 | 0 | 0 | 8331 | 2571 | 89.4% | 10.5s |
| core | skill-13 | 3 | ✅ | final_answer | 2 | 1 | 8359 | 0 | 0 | 8359 | 2599 | 90.2% | 10.1s |
| core | skill-14 | 1 | ✅ | final_answer | 3 | 2 | 7801 | 0 | 0 | 7801 | 5369 | 68.7% | 22.5s |
| core | skill-14 | 2 | ✅ | final_answer | 3 | 2 | 6769 | 0 | 0 | 6769 | 4081 | 77.9% | 18.4s |
| core | skill-14 | 3 | ✅ | final_answer | 3 | 2 | 7768 | 0 | 0 | 7768 | 5080 | 76.3% | 23.3s |
| core | skill-15 | 1 | ❌ | context_error | 2 | 2 | 1402 | 942 | 0 | 2344 | 1832 | 26.3% | 2.8s |
| core | skill-15 | 2 | ❌ | context_error | 2 | 2 | 1253 | 2059 | 0 | 3312 | 2032 | 46.4% | 3.6s |
| core | skill-15 | 3 | ❌ | context_error | 2 | 1 | 1358 | 940 | 0 | 2298 | 1018 | 65.9% | 2.7s |
| core | eval-03 | 1 | ✅ | final_answer | 3 | 3 | 12270 | 0 | 0 | 12270 | 2926 | 81.2% | 4.4s |
| core | eval-03 | 2 | ✅ | final_answer | 3 | 3 | 12363 | 0 | 0 | 12363 | 2891 | 81.9% | 4.8s |
| core | eval-03 | 3 | ✅ | final_answer | 3 | 3 | 12564 | 0 | 0 | 12564 | 3092 | 81.2% | 5.2s |
| core | eval-04 | 1 | ✅ | final_answer | 2 | 1 | 7491 | 0 | 0 | 7491 | 1347 | 88.7% | 3.4s |
| core | eval-04 | 2 | ✅ | final_answer | 2 | 1 | 8213 | 0 | 0 | 8213 | 1813 | 88.1% | 4.9s |
| core | eval-04 | 3 | ✅ | final_answer | 2 | 1 | 7973 | 0 | 0 | 7973 | 1701 | 88.0% | 4.3s |
| core | eval-17 | 1 | ✅ | final_answer | 5 | 4 | 23499 | 0 | 0 | 23499 | 6859 | 76.2% | 8.9s |
| core | eval-17 | 2 | ✅ | final_answer | 5 | 5 | 24447 | 0 | 0 | 24447 | 7423 | 74.2% | 8.7s |
| core | eval-17 | 3 | ✅ | final_answer | 5 | 4 | 25134 | 0 | 0 | 25134 | 7854 | 74.5% | 10.9s |
| core | eval-18 | 1 | ✅ | final_answer | 2 | 1 | 7701 | 0 | 0 | 7701 | 1685 | 82.3% | 2.8s |
| core | eval-18 | 2 | ✅ | final_answer | 2 | 1 | 7618 | 0 | 0 | 7618 | 1730 | 81.2% | 2.5s |
| core | eval-18 | 3 | ✅ | final_answer | 2 | 1 | 7654 | 0 | 0 | 7654 | 1638 | 82.9% | 2.8s |
| core | eval-19 | 1 | ✅ | final_answer | 2 | 1 | 6241 | 0 | 0 | 6241 | 481 | 93.2% | 1.6s |
| core | eval-19 | 2 | ✅ | final_answer | 2 | 1 | 6247 | 0 | 0 | 6247 | 487 | 93.2% | 1.7s |
| core | eval-19 | 3 | ✅ | final_answer | 2 | 1 | 6224 | 0 | 0 | 6224 | 464 | 93.4% | 1.7s |
| core | eval-20 | 1 | ✅ | final_answer | 2 | 1 | 7608 | 0 | 0 | 7608 | 1720 | 82.9% | 3.0s |
| core | eval-20 | 2 | ✅ | final_answer | 2 | 1 | 7401 | 0 | 0 | 7401 | 1513 | 83.7% | 2.3s |
| core | eval-20 | 3 | ✅ | final_answer | 2 | 1 | 8235 | 0 | 0 | 8235 | 2347 | 79.4% | 4.5s |
| core | eval-02 | 1 | ✅ | final_answer | 2 | 1 | 6381 | 0 | 0 | 6381 | 621 | 92.9% | 1.9s |
| core | eval-02 | 2 | ✅ | final_answer | 2 | 1 | 6305 | 0 | 0 | 6305 | 545 | 92.8% | 1.5s |
| core | eval-02 | 3 | ✅ | final_answer | 2 | 1 | 6306 | 0 | 0 | 6306 | 546 | 92.9% | 1.4s |
| core | eval-12 | 1 | ✅ | final_answer | 3 | 2 | 10280 | 0 | 0 | 10280 | 936 | 94.1% | 2.8s |
| core | eval-12 | 2 | ✅ | final_answer | 3 | 2 | 10394 | 0 | 0 | 10394 | 1050 | 93.8% | 3.2s |
| core | eval-12 | 3 | ✅ | final_answer | 3 | 2 | 10230 | 0 | 0 | 10230 | 886 | 94.4% | 2.7s |
| core | eval-13 | 1 | ✅ | final_answer | 2 | 1 | 6353 | 0 | 0 | 6353 | 593 | 92.6% | 1.7s |
| core | eval-13 | 2 | ✅ | final_answer | 2 | 1 | 6274 | 0 | 0 | 6274 | 514 | 93.0% | 1.4s |
| core | eval-13 | 3 | ✅ | final_answer | 2 | 1 | 6307 | 0 | 0 | 6307 | 547 | 92.6% | 1.5s |
| core | eval-14 | 1 | ✅ | final_answer | 5 | 4 | 7025 | 0 | 0 | 7025 | 1905 | 82.4% | 5.6s |
| core | eval-14 | 2 | ✅ | final_answer | 4 | 4 | 5074 | 0 | 0 | 5074 | 1234 | 83.3% | 3.7s |
| core | eval-14 | 3 | ✅ | final_answer | 4 | 4 | 5695 | 0 | 0 | 5695 | 1599 | 83.8% | 5.7s |
| core | eval-15 | 1 | ✅ | final_answer | 2 | 1 | 6353 | 0 | 0 | 6353 | 593 | 92.5% | 1.5s |
| core | eval-15 | 2 | ✅ | final_answer | 2 | 1 | 6327 | 0 | 0 | 6327 | 567 | 92.7% | 1.8s |
| core | eval-15 | 3 | ✅ | final_answer | 2 | 1 | 6262 | 0 | 0 | 6262 | 502 | 93.2% | 1.5s |
| core | eval-16 | 1 | ✅ | final_answer | 2 | 1 | 6634 | 0 | 0 | 6634 | 874 | 92.4% | 3.2s |
| core | eval-16 | 2 | ✅ | final_answer | 2 | 1 | 6419 | 0 | 0 | 6419 | 531 | 94.3% | 1.6s |
| core | eval-16 | 3 | ✅ | final_answer | 2 | 1 | 6483 | 0 | 0 | 6483 | 723 | 92.4% | 1.9s |
| memory | memory-01/learn | 1 | ✅ | final_answer | 2 | 1 | 5074 | 0 | 1537 | 6611 | 3667 | 59.0% | 8.7s |
| memory | memory-01/recall | 1 | ✅ | final_answer | 3 | 3 | 7416 | 0 | 2207 | 9623 | 3735 | 65.0% | 4.1s |
| memory | memory-01/learn | 2 | ❌ | final_answer | 2 | 1 | 5958 | 0 | 3172 | 9130 | 4394 | 72.4% | 13.2s |
| memory | memory-01/recall | 2 | ❌ | final_answer | 4 | 5 | 8277 | 0 | 1689 | 9966 | 4334 | 61.9% | 7.3s |
| memory | memory-01/learn | 3 | ✅ | final_answer | 2 | 1 | 5115 | 0 | 1611 | 6726 | 2758 | 80.1% | 9.6s |
| memory | memory-01/recall | 3 | ✅ | final_answer | 3 | 3 | 7107 | 0 | 2158 | 9265 | 3377 | 67.5% | 4.8s |
| memory | memory-02/ask | 1 | ✅ | final_answer | 1 | 0 | 1557 | 0 | 760 | 2317 | 653 | 74.2% | 1.2s |
| memory | memory-02/ask | 2 | ✅ | final_answer | 1 | 0 | 1584 | 0 | 778 | 2362 | 570 | 79.9% | 2.0s |
| memory | memory-02/ask | 3 | ✅ | final_answer | 1 | 0 | 1595 | 0 | 772 | 2367 | 575 | 79.8% | 1.6s |
| memory | memory-03/prefer | 1 | ✅ | final_answer | 3 | 2 | 7541 | 0 | 1572 | 9113 | 4377 | 55.6% | 5.0s |
| memory | memory-03/prefer | 2 | ✅ | final_answer | 3 | 2 | 7721 | 0 | 1551 | 9272 | 2744 | 75.4% | 4.4s |
| memory | memory-03/prefer | 3 | ✅ | final_answer | 3 | 2 | 7524 | 0 | 1589 | 9113 | 2713 | 75.2% | 4.9s |
| memory | memory-04/progress | 1 | ✅ | final_answer | 1 | 0 | 1638 | 0 | 813 | 2451 | 787 | 73.8% | 1.6s |
| memory | memory-04/progress | 2 | ✅ | final_answer | 1 | 0 | 1650 | 0 | 824 | 2474 | 682 | 79.2% | 1.9s |
| memory | memory-04/progress | 3 | ✅ | final_answer | 1 | 0 | 1652 | 0 | 818 | 2470 | 678 | 79.0% | 1.7s |
| memory | memory-05/revise | 1 | ✅ | final_answer | 3 | 2 | 6874 | 0 | 1843 | 8717 | 3597 | 68.7% | 7.4s |
| memory | memory-05/revise | 2 | ✅ | final_answer | 3 | 2 | 7336 | 0 | 2012 | 9348 | 3460 | 77.9% | 10.3s |
| memory | memory-05/revise | 3 | ✅ | final_answer | 4 | 4 | 11218 | 0 | 2414 | 13632 | 9152 | 38.8% | 11.3s |
| memory | memory-06/unrelated | 1 | ✅ | final_answer | 1 | 0 | 1675 | 0 | 888 | 2563 | 899 | 71.0% | 2.3s |
| memory | memory-06/unrelated | 2 | ✅ | final_answer | 1 | 0 | 1582 | 0 | 825 | 2407 | 615 | 79.0% | 2.2s |
| memory | memory-06/unrelated | 3 | ✅ | final_answer | 1 | 0 | 1612 | 0 | 802 | 2414 | 622 | 79.3% | 1.7s |
| memory | memory-07/ask | 1 | ✅ | final_answer | 3 | 4 | 5930 | 0 | 1300 | 7230 | 1982 | 77.7% | 4.2s |
| memory | memory-07/ask | 2 | ✅ | final_answer | 3 | 4 | 6243 | 0 | 1342 | 7585 | 2081 | 80.0% | 5.9s |
| memory | memory-07/ask | 3 | ✅ | final_answer | 3 | 4 | 6439 | 0 | 1316 | 7755 | 2251 | 79.6% | 5.8s |
| memory | memory-08/ask | 1 | ✅ | final_answer | 2 | 1 | 3760 | 0 | 1091 | 4851 | 1907 | 64.4% | 2.9s |
| memory | memory-08/ask | 2 | ✅ | final_answer | 2 | 1 | 3725 | 0 | 1073 | 4798 | 1214 | 79.1% | 2.4s |
| memory | memory-08/ask | 3 | ✅ | final_answer | 2 | 1 | 3824 | 0 | 1110 | 4934 | 1222 | 80.6% | 3.1s |
| memory | memory-09/correct | 1 | ✅ | final_answer | 4 | 4 | 9868 | 0 | 2400 | 12268 | 5740 | 64.1% | 11.4s |
| memory | memory-09/correct | 2 | ✅ | final_answer | 4 | 5 | 9883 | 0 | 2960 | 12843 | 6315 | 59.7% | 10.4s |
| memory | memory-09/correct | 3 | ❌ | final_answer | 4 | 6 | 9885 | 0 | 2431 | 12316 | 5532 | 65.4% | 10.9s |
| memory | memory-10/create_at_capacity | 1 | ✅ | final_answer | 2 | 2 | 6342 | 0 | 1952 | 8815 | 4975 | 60.1% | 13.2s |
| memory | memory-10/create_at_capacity | 2 | ✅ | final_answer | 3 | 3 | 10142 | 0 | 2283 | 12914 | 4978 | 78.6% | 14.8s |
| memory | memory-10/create_at_capacity | 3 | ✅ | final_answer | 1 | 0 | 2666 | 0 | 1469 | 4668 | 2620 | 65.5% | 9.0s |
| learning | learning-01 | 1 | ✅ | completed | 0 | 0 | 2475 | 0 | 0 | 2475 | 2475 | 未知 | 0.3s |
| learning | learning-01 | 2 | ✅ | completed | 0 | 0 | 2478 | 0 | 0 | 2478 | 2478 | 未知 | 0.6s |
| learning | learning-01 | 3 | ✅ | completed | 0 | 0 | 2477 | 0 | 0 | 2477 | 2477 | 未知 | 0.6s |
| learning | learning-02 | 1 | ✅ | completed | 0 | 0 | 2995 | 0 | 0 | 2995 | 2995 | 未知 | 3.4s |
| learning | learning-02 | 2 | ✅ | completed | 0 | 0 | 3004 | 0 | 0 | 3004 | 3004 | 未知 | 4.4s |
| learning | learning-02 | 3 | ✅ | completed | 0 | 0 | 3003 | 0 | 0 | 3003 | 3003 | 未知 | 4.0s |
| learning | learning-03 | 1 | ✅ | completed | 0 | 0 | 860 | 0 | 0 | 860 | 860 | 未知 | 0.3s |
| learning | learning-03 | 2 | ✅ | completed | 0 | 0 | 857 | 0 | 0 | 857 | 857 | 未知 | 0.7s |
| learning | learning-03 | 3 | ✅ | completed | 0 | 0 | 859 | 0 | 0 | 859 | 859 | 未知 | 0.7s |
| learning | learning-04 | 1 | ✅ | completed | 0 | 0 | 3051 | 0 | 0 | 3051 | 3051 | 未知 | 3.4s |
| learning | learning-04 | 2 | ✅ | completed | 0 | 0 | 3007 | 0 | 0 | 3007 | 3007 | 未知 | 3.6s |
| learning | learning-04 | 3 | ✅ | completed | 0 | 0 | 3042 | 0 | 0 | 3042 | 3042 | 未知 | 3.5s |
| learning | learning-05a | 1 | ❌ | completed | 0 | 0 | 3587 | 0 | 0 | 3587 | 3587 | 未知 | 4.8s |
| learning | learning-05a | 2 | ❌ | completed | 0 | 0 | 3587 | 0 | 0 | 3587 | 3587 | 未知 | 4.9s |
| learning | learning-05a | 3 | ❌ | completed | 0 | 0 | 3536 | 0 | 0 | 3536 | 3536 | 未知 | 4.8s |
| learning | learning-05b | 1 | ✅ | completed | 0 | 0 | 3552 | 0 | 0 | 3552 | 3552 | 未知 | 4.6s |
| learning | learning-05b | 2 | ✅ | completed | 0 | 0 | 3544 | 0 | 0 | 3544 | 3544 | 未知 | 4.1s |
| learning | learning-05b | 3 | ✅ | completed | 0 | 0 | 3509 | 0 | 0 | 3509 | 3509 | 未知 | 3.7s |
| learning | learning-05c | 1 | ✅ | completed | 0 | 0 | 3124 | 0 | 0 | 3124 | 3124 | 未知 | 2.9s |
| learning | learning-05c | 2 | ✅ | completed | 0 | 0 | 3186 | 0 | 0 | 3186 | 3186 | 未知 | 3.2s |
| learning | learning-05c | 3 | ✅ | completed | 0 | 0 | 3132 | 0 | 0 | 3132 | 3132 | 未知 | 3.4s |
| learning | learning-06 | 1 | ✅ | completed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 未知 | 0.0s |
| learning | learning-06 | 2 | ✅ | completed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 未知 | 0.0s |
| learning | learning-06 | 3 | ✅ | completed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 未知 | 0.0s |
| learning | learning-07 | 1 | ✅ | completed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 未知 | 0.0s |
| learning | learning-07 | 2 | ✅ | completed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 未知 | 0.0s |
| learning | learning-07 | 3 | ✅ | completed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 未知 | 0.0s |
| learning | learning-08 | 1 | ✅ | completed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 未知 | 0.0s |
| learning | learning-08 | 2 | ✅ | completed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 未知 | 0.0s |
| learning | learning-08 | 3 | ✅ | completed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 未知 | 0.0s |
| learning | learning-09 | 1 | ✅ | completed | 0 | 0 | 2537 | 0 | 0 | 2537 | 2537 | 未知 | 2.5s |
| learning | learning-09 | 2 | ✅ | completed | 0 | 0 | 2583 | 0 | 0 | 2583 | 2583 | 未知 | 2.2s |
| learning | learning-09 | 3 | ✅ | completed | 0 | 0 | 2593 | 0 | 0 | 2593 | 2593 | 未知 | 2.7s |
| learning | learning-10 | 1 | ✅ | completed | 0 | 0 | 7006 | 0 | 0 | 7006 | 7006 | 未知 | 5.5s |
| learning | learning-10 | 2 | ✅ | completed | 0 | 0 | 7087 | 0 | 0 | 7087 | 7087 | 未知 | 5.6s |
| learning | learning-10 | 3 | ✅ | completed | 0 | 0 | 6892 | 0 | 0 | 6892 | 6892 | 未知 | 5.4s |

## 失败归因

### core · eval-05 · run#1
- [answer] missing_keypoints=['效率提升']; answer='<｜｜DSML｜｜ calls>\n<｜｜DSML｜｜ invoke name="task_get">\n<｜｜DSML｜｜ parameter name="task_id" string="true">current</｜｜DSML｜｜ parameter>\n</｜｜DSML｜｜ invoke>\n</｜｜DSML｜｜ calls>'
- Trace：`..\tmp\eval-runs\no-prefix-reuse-3runs-20260929\eval-20260929_155329_179705\core\eval-05\run-1\trace.json`

### core · eval-05 · run#3
- [answer] missing_keypoints=['效率提升']; answer='<｜｜DSML｜｜ calls>\n<｜｜DSML｜｜ invoke name="task_get">\n<｜｜DSML｜｜ parameter name="task_id" string="true">current</｜｜DSML｜｜ parameter>\n</｜｜DSML｜｜ invoke>\n</｜｜DSML｜｜ calls>'
- Trace：`..\tmp\eval-runs\no-prefix-reuse-3runs-20260929\eval-20260929_155329_179705\core\eval-05\run-3\trace.json`

### core · eval-21 · run#1
- [ran_ok] stop=context_error; expected=['final_answer']
- [answer] missing_keypoints=['Python']; answer='Agent stopped: context preparation failed: estimated input tokens (1977) exceed input budget (1804)'
- Trace：`..\tmp\eval-runs\no-prefix-reuse-3runs-20260929\eval-20260929_155329_179705\core\eval-21\run-1\trace.json`

### core · eval-21 · run#2
- [ran_ok] stop=context_error; expected=['final_answer']
- [answer] missing_keypoints=['Python']; answer='Agent stopped: context preparation failed: estimated input tokens (1966) exceed input budget (1804)'
- Trace：`..\tmp\eval-runs\no-prefix-reuse-3runs-20260929\eval-20260929_155329_179705\core\eval-21\run-2\trace.json`

### core · eval-21 · run#3
- [ran_ok] stop=context_error; expected=['final_answer']
- [answer] missing_keypoints=['Python']; answer='Agent stopped: context preparation failed: estimated input tokens (1946) exceed input budget (1804)'
- Trace：`..\tmp\eval-runs\no-prefix-reuse-3runs-20260929\eval-20260929_155329_179705\core\eval-21\run-3\trace.json`

### core · eval-23 · run#1
- [ran_ok] stop=context_error; expected=['final_answer']
- [answer] missing_keypoints=['120']; answer='Agent stopped: context preparation failed: estimated input tokens (1915) exceed input budget (1804)'
- Trace：`..\tmp\eval-runs\no-prefix-reuse-3runs-20260929\eval-20260929_155329_179705\core\eval-23\run-1\trace.json`

### core · eval-23 · run#2
- [ran_ok] stop=context_error; expected=['final_answer']
- [answer] missing_keypoints=['120']; answer='Agent stopped: context preparation failed: estimated input tokens (1907) exceed input budget (1804)'
- Trace：`..\tmp\eval-runs\no-prefix-reuse-3runs-20260929\eval-20260929_155329_179705\core\eval-23\run-2\trace.json`

### core · eval-23 · run#3
- [ran_ok] stop=context_error; expected=['final_answer']
- [answer] missing_keypoints=['120']; answer='Agent stopped: context preparation failed: estimated input tokens (1902) exceed input budget (1804)'
- Trace：`..\tmp\eval-runs\no-prefix-reuse-3runs-20260929\eval-20260929_155329_179705\core\eval-23\run-3\trace.json`

### core · skill-15 · run#1
- [ran_ok] stop=context_error; expected=['final_answer']
- [answer] missing_keypoints=['int', 'ValueError']; answer='Agent stopped: context preparation failed: estimated input tokens (2185) exceed input budget (1888)'
- Trace：`..\tmp\eval-runs\no-prefix-reuse-3runs-20260929\eval-20260929_155329_179705\core\skill-15\run-1\trace.json`

### core · skill-15 · run#2
- [ran_ok] stop=context_error; expected=['final_answer']
- [answer] missing_keypoints=['int', 'ValueError']; answer='Agent stopped: context preparation failed: estimated input tokens (2119) exceed input budget (1888)'
- Trace：`..\tmp\eval-runs\no-prefix-reuse-3runs-20260929\eval-20260929_155329_179705\core\skill-15\run-2\trace.json`

### core · skill-15 · run#3
- [ran_ok] stop=context_error; expected=['final_answer']
- [tools] called=['skill_read']; missing=['read_file']; missing_success=['read_file']; order=['skill_read'] 未包含有序序列 ['skill_read', 'read_file']
- [answer] missing_keypoints=['int', 'ValueError']; answer='Agent stopped: context preparation failed: estimated input tokens (1981) exceed input budget (1888)'
- Trace：`..\tmp\eval-runs\no-prefix-reuse-3runs-20260929\eval-20260929_155329_179705\core\skill-15\run-3\trace.json`

### memory · memory-01/learn · run#2
- [reflection_action] actual=None expected=create
- [reflection_mutation] actual=None expected=True
- [active_count] actual=0 expected=1
- [stored_memory] not_found=STORAGE_DECISION
- Trace：`..\tmp\eval-runs\no-prefix-reuse-3runs-20260929\eval-20260929_155329_179705\memory\memory-01\run-2\on\phase-learn\trace.json`

### memory · memory-01/recall · run#2
- [recall] reads=[] missing=['STORAGE_DECISION'] forbidden=[]
- [read_count] actual=0 expected=1
- [answer] missing=['Markdown'] forbidden=[]
- Trace：`..\tmp\eval-runs\no-prefix-reuse-3runs-20260929\eval-20260929_155329_179705\memory\memory-01\run-2\on\phase-recall\trace.json`

### memory · memory-09/correct · run#3
- [reflection_action] actual=none expected=update
- [recall] reads=[] missing=['M001'] forbidden=[]
- [stored_memory] content_missing=25, revision=1 < 2
- Trace：`..\tmp\eval-runs\no-prefix-reuse-3runs-20260929\eval-20260929_155329_179705\memory\memory-09\run-3\on\phase-correct\trace.json`

### learning · learning-05a · run#1
- [learning] candidate_count=1 expected 0; update_count=1 expected 0; action not none: ['update']
- Pattern Mining：scanned=4, clusters=1
- Pattern Mining raw_output（报告预览）：
```json
"{\"clusters\": [{\"id\": \"python-env-debug\", \"task_ids\": [\"cfbc2ab06b394110aa2e67b4addcc97b\", \"c73d1c525a9c4d83ab37295290c299de\", \"4a10dff4a5ba4faba0083eca235d4f4d\", \"e7440f637e3f42af93ed428c56f27a42\"], \"pattern_name\": \"Python 运行环境错配排查与恢复\", \"description\": \"针对 Python 项目启动/运行失败，按统一流程定位是解释器路径、依赖、虚拟环境还是运行环境错配，修复后验证项目恢复运行。\", \"similarity_reason\": \"四个任务标题、描述、目标高度同构，均围绕 Python 环境错配；key_facts 分别指向运行环境、解释器路径、依赖、virtualenv 等同类根因；final_steps 完全一致（复现错误→修复并验证），属于同一多步排查工作流的不同变体。\", \"reusable_value\": \"可沉淀为统一的 Python 环境诊断流程：复现错误、检查解释器/虚拟环境/依赖一致性、修复错配、验证启动，减少重复试错并降低同类问题复发率。\"}]}"
```
  - Cluster：Python 运行环境错配排查与恢复 · tasks=['cfbc2ab06b394110aa2e67b4addcc97b', 'c73d1c525a9c4d83ab37295290c299de', '4a10dff4a5ba4faba0083eca235d4f4d', 'e7440f637e3f42af93ed428c56f27a42']
- Distillation：cluster=Python 运行环境错配排查与恢复, action=update, reason=四个已完成任务高度同构，均围绕 Python 运行环境错配（解释器路径、依赖、virtualenv、运行环境），且工具序列一致（run_pytest → task_update），失败信息分别指向 environment mismatch / path not found / venv missing / venv，属于同一 Python 运行时排查任务族。现有 debug-python 技能仅覆盖“复现→读 traceback→修复验证”，未覆盖解释器/虚拟环境/依赖一致性诊断与错配修复，因此应扩展该技能而非新建。, error=-
- Distillation Python 运行环境错配排查与恢复 raw_output（报告预览）：
```json
"{\"action\":\"update\",\"proposed_name\":null,\"description\":null,\"reason\":\"四个已完成任务高度同构，均围绕 Python 运行环境错配（解释器路径、依赖、virtualenv、运行环境），且工具序列一致（run_pytest → task_update），失败信息分别指向 environment mismatch / path not found / venv missing / venv，属于同一 Python 运行时排查任务族。现有 debug-python 技能仅覆盖“复现→读 traceback→修复验证”，未覆盖解释器/虚拟环境/依赖一致性诊断与错配修复，因此应扩展该技能而非新建。\",\"procedure\":[\"复现失败：运行 run_pytest 或项目启动命令，记录完整错误信息\",\"判断错误类别：区分 environment mismatch、path not found、venv missing、依赖缺失等根因\",\"检查解释器路径：确认当前使用的 Python 解释器与项目预期一致\",\"检查虚拟环境：确认项目实际使用的 .venv 是否存在并被激活，避免使用系统解释器\",\"检查依赖一致性：确认依赖安装在正确的虚拟环境中，而非全局或其他环境\",\"修复错配：切换到正确的解释器/虚拟环境，或补齐缺失依赖，避免重装全部依赖\",\"验证恢复：重新运行 run_pytest 或启动命令，确认项目恢复运行\",\"记录结论：将实际使用的环境（如 .venv）与约束写入任务事实，防止复发\"],\"pitfalls\":[\"直接重装全部依赖而不先定位是解释器、虚拟环境还是依赖问题\",\"忽略项目实际使用的 .venv，误用系统 Python 解释器\",\"未确认虚拟环境是否激活就判断依赖缺失\",\"修复后未重新运行验证，误以为已恢复\"],\"verification\":[\"run_pytest 或启动命令成功执行，无 environment mismatch / path not found / venv missing 报错\",\"确认使用的解释器路径与项目预期一致\",\"确认依赖安装在项目实际使用的虚拟环境中\",\"任务事实中记录了正确的环境信息（如 .venv）\"],\"existing_skill_name\":\"debug-python\"}"
```

### learning · learning-05a · run#2
- [learning] candidate_count=1 expected 0; update_count=1 expected 0; action not none: ['update']
- Pattern Mining：scanned=4, clusters=1
- Pattern Mining raw_output（报告预览）：
```json
"{\"clusters\": [{\"id\": \"python-env-debug\", \"task_ids\": [\"59012fde269a44aaae3484725b8def40\", \"988560e93e474ddd943d115644ad40e1\", \"12858835dd354bf9af85e23287ce431e\", \"8e0e806ef8184d3fbbef55962a1c5604\"], \"pattern_name\": \"Python 环境错配排查与恢复\", \"description\": \"针对 Python 运行环境、解释器路径、依赖、虚拟环境等错配问题，按统一流程复现错误、定位环境问题、修复并验证项目恢复运行。\", \"similarity_reason\": \"四个任务均为 Python 环境相关报错排查，目标一致（恢复运行/启动），final_steps 完全相同（复现错误→修复并验证），key_facts 均指向 Python 环境错配的不同子类。\", \"reusable_value\": \"可沉淀为统一的 Python 环境诊断流程，覆盖解释器路径、依赖、虚拟环境等常见错配，减少重复排查成本并提高修复一致性。\"}]}"
```
  - Cluster：Python 环境错配排查与恢复 · tasks=['59012fde269a44aaae3484725b8def40', '988560e93e474ddd943d115644ad40e1', '12858835dd354bf9af85e23287ce431e', '8e0e806ef8184d3fbbef55962a1c5604']
- Distillation：cluster=Python 环境错配排查与恢复, action=update, reason=四个已完成任务均为 Python 环境错配排查（environment mismatch / path not found / venv missing / venv），目标一致（恢复运行或启动），流程一致（复现错误→修复并验证），且都通过 run_pytest 暴露环境问题后更新任务约束/事实。这与现有 debug-python 属于同一任务族（Python 运行期问题排查），但现有技能体仅覆盖“复现→读 traceback→修复并验证”，未覆盖环境错配的诊断步骤（确认实际使用的 .venv、解释器路径、依赖完整性，且避免全量重装依赖）。因此应扩展该技能而非新建。, error=-
- Distillation Python 环境错配排查与恢复 raw_output（报告预览）：
```json
"{\"action\":\"update\",\"proposed_name\":null,\"description\":\"扩展 debug-python：在复现与读 traceback 之后，先诊断 Python 运行环境错配（解释器路径、虚拟环境、依赖），再修复并验证。\",\"reason\":\"四个已完成任务均为 Python 环境错配排查（environment mismatch / path not found / venv missing / venv），目标一致（恢复运行或启动），流程一致（复现错误→修复并验证），且都通过 run_pytest 暴露环境问题后更新任务约束/事实。这与现有 debug-python 属于同一任务族（Python 运行期问题排查），但现有技能体仅覆盖“复现→读 traceback→修复并验证”，未覆盖环境错配的诊断步骤（确认实际使用的 .venv、解释器路径、依赖完整性，且避免全量重装依赖）。因此应扩展该技能而非新建。\",\"procedure\":[\"复现错误：运行 run_pytest（或项目启动命令），记录失败信息（如 environment mismatch、path not found、venv missing）。\",\"判断是否为环境错配：若错误指向解释器路径、虚拟环境缺失或依赖不匹配，而非代码逻辑异常，则进入环境诊断分支。\",\"确认项目实际使用的虚拟环境：检查是否存在 .venv 等目录，确认当前解释器路径与项目期望一致。\",\"核对依赖状态：确认所需依赖是否安装在当前解释器中，避免误判为代码问题。\",\"修复环境：切换到正确的解释器/虚拟环境，或补齐缺失依赖；遵循“使用现有 .venv、不要重装全部依赖”的约束。\",\"验证恢复：重新运行 run_pytest 或启动命令，确认项目恢复运行/启动。\",\"记录结论：将确认的环境事实（如实际使用 .venv）与约束更新到任务中，便于后续复用。\"],\"pitfalls\":[\"未先确认实际使用的虚拟环境（如 .venv）就直接重装依赖。\",\"把环境错配误判为代码逻辑错误，浪费排查时间。\",\"全量重装依赖，违反“不要重装全部依赖”的约束并可能破坏现有环境。\",\"忽略解释器路径与项目期望不一致导致的 path not found。\"],\"verification\":[\"重新运行 run_pytest 或项目启动命令，确认不再出现 environment mismatch / path not found / venv missing 等环境类错误。\",\"确认当前解释器路径与项目实际使用的虚拟环境（如 .venv）一致。\",\"确认所需依赖在当前环境中可用，且未进行不必要的全量重装。\"],\"existing_skill_name\":\"debug-python\"}"
```

### learning · learning-05a · run#3
- [learning] candidate_count=1 expected 0; update_count=1 expected 0; action not none: ['update']
- Pattern Mining：scanned=4, clusters=1
- Pattern Mining raw_output（报告预览）：
```json
"{\"clusters\": [{\"id\": \"python-env-debug\", \"task_ids\": [\"df11d4ac1bb248ad95504dc609d55a2d\", \"c6f749553bbb4219bda4c01ef6293074\", \"bdf4b53248ae47778db1f802de4f606f\", \"b6aa978a1b454a1ea8b5477bcd3043ad\"], \"pattern_name\": \"Python 环境错配排查与恢复\", \"description\": \"针对 Python 运行环境、解释器路径、依赖、虚拟环境等错配问题，按统一流程复现错误、定位环境问题、修复并验证项目恢复运行。\", \"similarity_reason\": \"四个任务均以排查 Python 环境相关错配为核心，目标都是恢复项目运行或启动，final_steps 完全一致（复现错误→修复并验证），key_facts 均指向 Python 运行环境的不同侧面（运行环境、解释器路径、依赖、virtualenv），属于同一类多步排查工作流。\", \"reusable_value\": \"可沉淀为统一的 Python 环境问题排查流程，覆盖解释器路径、依赖、虚拟环境等常见错配场景，减少重复定位成本并提高修复一致性。\"}]}"
```
  - Cluster：Python 环境错配排查与恢复 · tasks=['df11d4ac1bb248ad95504dc609d55a2d', 'c6f749553bbb4219bda4c01ef6293074', 'bdf4b53248ae47778db1f802de4f606f', 'b6aa978a1b454a1ea8b5477bcd3043ad']
- Distillation：cluster=Python 环境错配排查与恢复, action=update, reason=四个已完成任务均为 Python 环境错配排查（environment mismatch / path not found / venv missing / venv），目标都是恢复运行或启动，步骤一致（复现错误→修复并验证），且都通过 task_update 记录环境事实或约束（如项目实际使用 .venv、使用现有 .venv、不要重装全部依赖）。这与现有 debug-python 属于同一任务族（Python 报错排查），但其 body 仅覆盖“复现→读 traceback→修复并验证”，未覆盖环境错配这一稳定新增环节，因此应扩展该技能而非新建。, error=-
- Distillation Python 环境错配排查与恢复 raw_output（报告预览）：
```json
"{\"action\":\"update\",\"proposed_name\":null,\"description\":\"扩展 debug-python：在复现 Python 报错后，先排查运行环境错配（解释器路径、依赖、虚拟环境），再修复并验证。\",\"reason\":\"四个已完成任务均为 Python 环境错配排查（environment mismatch / path not found / venv missing / venv），目标都是恢复运行或启动，步骤一致（复现错误→修复并验证），且都通过 task_update 记录环境事实或约束（如项目实际使用 .venv、使用现有 .venv、不要重装全部依赖）。这与现有 debug-python 属于同一任务族（Python 报错排查），但其 body 仅覆盖“复现→读 traceback→修复并验证”，未覆盖环境错配这一稳定新增环节，因此应扩展该技能而非新建。\",\"procedure\":[\"复现报错：运行 run_pytest 或项目启动命令，捕获完整错误信息\",\"判断错误是否属于环境错配：environment mismatch、path not found、venv missing 等\",\"定位实际运行环境：确认项目使用的解释器路径与虚拟环境（如 .venv）\",\"核对依赖与虚拟环境状态：确认依赖是否安装在当前使用的环境中\",\"按最小改动修复：优先使用现有 .venv，避免重装全部依赖\",\"重新运行验证项目恢复运行或启动\"],\"pitfalls\":[\"不要重装全部依赖，优先使用现有 .venv\",\"不要忽略解释器路径与实际虚拟环境不一致的问题\",\"不要仅凭 traceback 修复代码而忽略环境错配根因\"],\"verification\":[\"重新运行 run_pytest 或启动命令，确认不再出现 environment mismatch / path not found / venv missing\",\"确认使用的解释器路径与项目实际虚拟环境（如 .venv）一致\",\"确认项目恢复运行或启动\"],\"existing_skill_name\":\"debug-python\"}"
```
