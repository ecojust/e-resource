# V13 网页 QA：完整运行时 near key 修复

此前 `qa/actual-static-v6` 的完整检查在 180 秒等待后失败，原报告与失败截图保留。实际失败快照中，365,524 三角形的完整模型已加载，far owner 1196 生效，旧 near 目标已隐藏，9 个邻居全部保留，通用所有权 audit 通过。失败来自 QA 把 owner 元数据的 near ID 直接与内部运行时 key 比较。

元数据的 `near_owner_id` 是 `14-13722-6690--1_-2-s0-s1`；实际 streamer key 是 `macro_id + '/' + near_owner_id`，即 `14-13722-6690/14-13722-6690--1_-2-s0-s1`。源 metadata 和产品行为正确，不应修改它们迁就测试。

本版以 `parallel-runtime-candidate` 为底，仅改 `target-probe.js` 的一行精确匹配。运行时 key 不使用后缀、模糊匹配或任意 macro 回退。所有断言、180 秒观察上限、产品下载期限、源状态、邻居检查、LOD、W 和截图要求均保持不变。31 文件读取的独立并行改进保留，输出仍按原 baseline 顺序精确比较。

两个版本的文件不可混用。实际运行报告 `tools` 会记录脚本与 5 个 helper 的 SHA；公开复现应按最后实际成功报告复制这一整套。

- `browser_acceptance.py`：26,463 B，SHA256 `8f784d5a5c2f1bb105bdb16686defd64517d200f67ad2d3b45b29690e2a727e1`。
- `target-probe.js`：5,780 B，SHA256 `88f31b53ce34263afb8b553a9b609cbe303b6aa9398dcd0b15969e7698db6b93`。

root 完成旧进程收尾后，用新 output 重跑全部 6 张截图、full/LOD/离开/返回和 W：

```sh
python /workspace/shanghai_expansion/building-by-building-v13/qa/runtime-key-v2/browser_acceptance.py \
  --url http://127.0.0.1:8875/ \
  --output /workspace/shanghai_expansion/building-by-building-v13/qa/actual-static-v6-runtime-key-v2 \
  --expected-landmarks /workspace/shanghai_expansion/building-by-building-v13/integration/candidate-v6/payload/data/landmarks.json \
  --expected-registry /workspace/shanghai_expansion/building-by-building-v13/integration/candidate-v6/payload/data/precise-buildings-v6.json \
  --runtime-baseline /workspace/shanghai_expansion/building-by-building-v13/integration/frozen-main-v12/runtime31.json \
  --catalog-stage pending --use-env-proxy
```

最终 accepted catalog 检查也使用同一套工具，将 expected 文件指向实际最终 payload，另用新 output 并传 `--catalog-stage active --catalog-only`。该模式只声称一次实际采用/near/source/full 及 1 张截图，不冒称重跑 LOD/W/完整动态目录生命周期。

准备验证已完成：Python 编译、5 个 helper 解析；纯离线控制读取实际失败快照，旧表达式 `hiddenNear=false`，新表达式 `hiddenNear=true` 且 9 邻居精确相符；6 个负控（错 metadata macro、错 runtime macro 前缀、错 near ID、漏邻居、替换邻居、旧目标错误可见）全部拒绝。运行 `node check_runtime_key.mjs` 可复现。该控制没有启动浏览器或改动活页面，不能代替新的实际完整通过记录及 root 外观检查。
