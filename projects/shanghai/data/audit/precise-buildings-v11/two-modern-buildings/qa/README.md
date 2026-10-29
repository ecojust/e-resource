# 两栋现代建筑的浏览器 QA 准备

此目录只有冻结工具和 pending 模型输入。没有运行浏览器、生成实际 expectations、观察 MVT、解码模型或接受建筑。固定静态顺序为 `jiading-shanghai-auto-museum`、`minhang-baoyugang-library`，29 条导航；源 registry 为 15 owners / 9 macros / 13 near。Museum 保留 735、797；Library 保留 35、60、299、333、375、466、947。候选 ordinary catalog 仍为 8 records / 6 macros；共享静态检查后才成为 10 / 8。

每栋完整视图、斜向细节、远处 LOD、返回各一图，最后 owner 退出、返回、城市清单重置三图，总计 11 图。最后三图的全局动作中，两张返回/重置近图仅归属最后的 Library，不能充当 Museum 证据。之后每个新宏独立执行 static adoption、dynamic only、bad index 三阶段和五张图；导航计数依次 29 / 28 / 28。原 owner、邻居、模型字节、卸载释放、对象复用、错误和源组件门槛保留。

`model-inputs.pending.json` 和 `osm-evidence-set.pending.json` 不可用于实际 profile。真实输入同时绑定 ready app spec、其真实 dependencies、逐建筑工具选择，再绑定两栋的现代 registration、input-lock、source delivery、package、decoded、三图 root native review、当前 raw/source 导航和独立实际 MVT fixture。本版使用 `reviewed-modern-tools.json` 的逐建筑 `selected_freezes`：Library 保留 f1f714…，Museum 必须给出独立受审的实际工具冻结。旧全局 `selected_freeze` / `modern_tool_source_freeze` dependencies 字段被拒绝；任一选项为 null 或 pending，均不能生成实际 profile。本版与 NEW app 的共享 `reviewed_tool_selection.py` 保持原字节一致。private 参考像素不由此工具打包。

准备真实输入与 profile（均须新输出路径）：

```sh
python -B prepare_model_inputs.py --integration-spec ACTUAL_READY_APP_SPEC --project ACTUAL_CANDIDATE29 --output NEW_MODEL_INPUTS.json
python -B prepare_expectations.py --project ACTUAL_CANDIDATE29 --allow-asset-root /workspace/shanghai_project --targets jiading-shanghai-auto-museum minhang-baoyugang-library --expected-record-count 29 --model-inputs NEW_MODEL_INPUTS.json --output NEW_EXPECTATIONS.json
python -B browser-next-v3.py --url ACTUAL_CANDIDATE_URL --output NEW_STATIC_OUTPUT --targets jiading-shanghai-auto-museum minhang-baoyugang-library --expected-record-count 29 --expectations NEW_EXPECTATIONS.json --osm-evidence-set ACTUAL_FIXTURE_SET.json --force-osm --use-env-proxy --width 1040 --height 760 --dpr 1 --timeout-ms 360000
```

原 `precise-v7-browser-expectations-v1` API 保留，附加 `modern_contract`、`modern_input_binding`、实际完整 candidate record 和按角色的 material/extension JSON。prepare 只读 GLB 容器/元数据，不宣称重做 GLTFLoader 几何解码；真正 decoded 证据来自绑定的已执行检查。静态浏览器重新核对实际 web/LOD 字节、三角数、现代玻璃材质与 extension JSON。无瓦、斗拱、古建门扇数量或旧模型三角数/高度常量。

`runtime-reference.json` 指向当前 31 文件基线；本工具不修改 runtime。profile 和实际报告携带该 descriptor / `runtime_baseline_sha256`；实际浏览器另以 HTTP 逐个核对这 31 文件的字节/SHA。root 静态和目录视觉报告也必须给出相同 `runtime_baseline_sha256`，与 app gate 一致。旧 V10 阴影修复不重放。现有只读 shadow 检查观察已经冻结的当前 runtime。

静态检查实际通过且 root 看过全部 11 图后，才使用已接受的 candidate 元数据生成每宏输入：

```sh
python -B catalog/prepare_catalog_inputs.py --project ACTUAL_STATIC_ACCEPTED_CANDIDATE --target jiading-shanghai-auto-museum --model-inputs NEW_MODEL_INPUTS.json --output NEW_MUSEUM_CATALOG_INPUTS.json
python -B catalog/browser-catalog.py --url ACTUAL_ACCEPTED_URL --output NEW_MUSEUM_CATALOG_OUTPUT --target jiading-shanghai-auto-museum --inputs NEW_MUSEUM_CATALOG_INPUTS.json --osm-evidence ACTUAL_MUSEUM_FIXTURE.json --use-env-proxy --width 1040 --height 760 --dpr 1 --timeout-ms 360000
```

Museum 完成后，再对 Library 使用另一份输入、其真实 fixture 和新输出目录。`ordinary-macro-browser-inputs-v1` 与 `ordinary-macro-catalog-browser-v7` 保留；`validate_record`、`validate_registry`、`macro_contract` 参数 API 与 app 导入点兼容。公开图名和顺序不变。两次目录结果不能相互代替。

`capture_journal.py` 使每次已返回的 before/after OSM 原始值先写报告，再执行通过断言；失败值也保留。每张截图返回后立刻记录文件名、bytes/SHA，然后才进行 after 观察。成功记录仍含原 `osm_capture_before` / `osm_capture_after` 字段；未完成条目保留 `capture_completed=false`，不能参与通过。错误图单独保留。只观察有返回值的调用，不制造未完成观测。

`parent-candidate-baseline.json` 保留原 QA 67ad95… / 65c6db… 的冻结身份；新差分记录将单独生成，不改原版本。16 个继承控制、15 个逐模型选择控制和 11 个 Museum transfer 控制只验证 pending/缺省/全局回退/对调工具选择拒绝、实际依赖字节绑定、固定目标/邻居、原 API、runtime 绑定及失败/截图保存顺序，不是浏览器或模型 PASS。此工具不运行 Node、Blender、Git 或写入 MAIN。实际模型、MVT、浏览器和 root 审核须由协调者依次执行并保留失败记录。所有单文件严格小于 100 MB。

最终工具选择已分别绑定：Museum 8fc0c7aa…cfc2（112依赖），Library f1f71403…cd26（67依赖）。模型输入仍 pending；工具冻结不代表模型或浏览器验收。已取得 `osm-observation/selected-fixture-set-v2/fixture-set.json` 的实际身份（SHA 1d5a58d1…aa871），仅代表观察输入身份，不代表遮蔽、导航或浏览器通过。`tool-selection.pending-template.json` 保留这种待定状态供负控；它永远不能作为正式受审选择。

Museum 专属 transfer gate 与 app 保持原字节一致：四类实际原始补充证明通过真实解码同一套 finite suite 转移到 raw/web/LOD，每类保留 12,378 件、0.05° 法向策略、无省略。它核对现有报告链，不在浏览器准备阶段重做网格计算；Library 原三类补充证明分支保持不变。


V3 root revision: the actual static-v1 attempt failed before its first OSM observation because a main-local variable shadowed the imported observation function. The renamed local fixes that Python scope error. The static31-file HTTP audit now uses the same browser-context request interface as the already-frozen catalog runner; it still checks every complete served byte/hash in the original order. Original v2 tools and the real failed report/image remain unchanged. Copied test/history reports retain their historical meaning and are not claimed as newly run v3 browser evidence. New actual model inputs, expectations and all11+5+5 browser images remain required.


V4 follows an actual Library race: existing state snapshot was readiness generation31, then the independently evaluated before inspection was generation32 pending/busy. Both runners already had an earlier readiness guard. V4 retains every actual pre-capture inspect return while waiting only for ready=false to settle within the existing timeout. The first ready inspection is used directly as the original before observation; a ready but incorrect/missing component is never retried. Timeout keeps the actual false before value and fails its original assertion. The independent after inspection and all original geometry/source/asset/capture assertions are unchanged. Earlier failures and screenshots remain historical failures. No actual v4 browser acceptance is claimed.
