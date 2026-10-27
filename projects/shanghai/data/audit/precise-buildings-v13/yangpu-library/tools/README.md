# V13 最终网页检查：南侧观察位与离开距离修正

这套工具在 `runtime-key-v2` 上修正两个 QA 驱动条件。产品、模型、源建筑、邻居、下载期限和既有验收断言没有改变。旧两次实际失败记录保留，不能改名作为本版通过记录。

南侧旧观察位约为 ENU `[11.02,-110.45,12.38]`，位于邻居 local 1141 的体量内，截图被邻居窗框遮挡。新观察位为 `[0,-85,12]`，朝南入口 `[0.8,-40.91,5]`，FOV 52°。`safe-south-view.json` 以同一范围内 64 栋源 footprint/估计高度核对 0.5m 眼点球及中心线，眼点距最近非目标建筑约 16.117m；也检查最终 RAW 的 365,524 个三角形，中心线在意定立面终点前最后 0.5m 之外无命中。**这只约束眼点和中心线，不证明整个视锥、街具或植被无阻挡，仍须实际截图检查。** 该证据 SHA256 为 `a7337979eea1f0eb2c26cad3b3c63b0f70a50e302db2a28e0d13f0cc8522373e`。

旧 owner 释放驱动在 zoom 15 时仅移动经度 0.06°，实际约 5,706.419m。原产品 `map-scene.js` 在 zoom<16 时默认范围为 12,000m，已有可见模型另有 300m 滞回，因此保持 LOD 可见是正常行为。新检查明确移动到目标以东 18,000m，保持 zoom 15，并记录 requested/actual center 与距离，要求两者严格大于 12,300m；之后仍执行原来的 `!active`、near/far/在线 owner 释放谓词，没有降低要求。

除此之外：东侧漫游、东北斜角、LOD、返回、真实 W 按下/松开、9 邻居、源替换、6 张截图及全部错误检查维持原逻辑。可选 `to_east/to_north` 默认均为 0，已验证所有其他 camera 请求及实际传给页面的 JS 与原版完全一致。31 件运行时读取保留前版的 Promise.all，仍按 baseline 顺序精确核对 HTTP 字节与 SHA。

执行脚本 27,575 B，SHA256 `0fb20a18d32ba6bc0f73bc3b756399557d3a2f6fef24dab1622b5d41ac5840a1`；5 个 JS helper 与 runtime-key-v2 字节完全一致。发布复现时应按最终成功报告的 `tools` 复制整套 6 件，不混用先前 runner。

```sh
python /workspace/shanghai_expansion/building-by-building-v13/qa/safe-views-v3/browser_acceptance.py \
  --url http://127.0.0.1:8875/ \
  --output /workspace/shanghai_expansion/building-by-building-v13/qa/actual-static-v6-safe-views-v3 \
  --expected-landmarks /workspace/shanghai_expansion/building-by-building-v13/integration/candidate-v6/payload/data/landmarks.json \
  --expected-registry /workspace/shanghai_expansion/building-by-building-v13/integration/candidate-v6/payload/data/precise-buildings-v6.json \
  --runtime-baseline /workspace/shanghai_expansion/building-by-building-v13/integration/frozen-main-v12/runtime31.json \
  --catalog-stage pending --use-env-proxy
```

URL/路径以 root 实际服务为准，每次必须新 output。最终 accepted catalog 用相同 6 件工具和实际最终 metadata，另起 output，传 `--catalog-stage active --catalog-only`。该小型运行仅声明一次实际采用/source/near/full 与 1 张截图，不借此声明重新跑过完整动态目录生命周期、LOD 或 W。

准备验证包括 Python 编译及纯离线 camera/driver 对比：仅约定两处驱动改变；3 个其他 camera 请求完全相同；旧 5.7km 请求被严格阈值拒绝，新 18km 请求超过阈值。它们不是实际浏览器通过证明。`runtime-key-v2-browser-baseline.py.txt` 是先前 runner 的只读文字基线，仅用于复现差分，不能作为当前执行工具。可用 `check_camera_change.py --base runtime-key-v2-browser-baseline.py.txt --landmarks /实际候选/landmarks.json --output /新目录/control.json` 复现。

`support-public-whitelist.json` 列出可以公开的说明、来源/差分、有限控制及净空证据。`RUNTIME_KEY_FIX.md` 与原失败 owner 子集保留前一次 near key 修复的历史范围。它们均不能代替最后成功的浏览器报告与 root 实际外观审查。
