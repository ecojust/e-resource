# V11：从真实 MAIN 27/13 基线追加两个 owner

`baseline-lock.json` 已在 root 确认 V10 最终342文件安装完成后，从实际 MAIN 读取并冻结。基线为27导航、8普通精细记录、6 catalog宏、13精细owner、7 owner宏、11 near；光照源码 SHA 为 `6cb2fb4dc1cca564d70f2718014c11600ba5846915df4d707caa5b56a873838c`。公开提交尚未绑定，不能把待发布commit填成已发布。

108个精确字节快照共约6MB，包含现有元数据/运行时、11个旧near、13份owner几何与必要mapping报告、两个新目标的原始宏/near资料。另有独立代理只读复核 `../baseline-independent-review/baseline-review.json`。冻结阶段只做JSON/原始gzip字节检查；随后经root安排独占窗口，实际生成并解码两个新near，见下节。没有MVT或浏览器观察。

## 新块范围

| ID | 宏 / near | 只分离替换的源owner | 保留邻居 |
|---|---|---|---|
| jiading-shanghai-auto-museum | 14-13706-6691 / -1_3 | 870 | 735、797 |
| minhang-baoyugang-library | 14-13718-6705 / -3_0 | 201 | 35、60、299、333、375、466、947 |

博物馆宏的12个residual保留。图书馆201/375的原始简化sliver保留，绝不裁剪、吸收375或按半径删邻居。两个新near共11个原源对象。实际几何审计完成后，合并期望为15 owner、9宏、13 near、186源对象，其中171邻居保留。之后两个模型和app分别实际验收完成才可能成为29导航、10普通记录、8catalog宏；本预备阶段没有创建此类运行时结果。

## 工具来源与唯一修改

`upstream-v10/` 保存未改的已安装V10工具。`tools/verify_override_geometry.mjs` 与 `verify_override_runtime.mjs` 原字节复制，目前未运行。

`tools/build_precise_overrides.py` 只扩展两个新、固定SHA的OSM geometry-input审计字段：博物馆使用 `linked_parts`，图书馆使用 `linked_source_parts` 与明确的375重叠证明。13个旧owner仍使用原来的输入约束。没有向冻结geometry-input添加旧schema别名，没有改地理环、源生成算法、压缩参数、邻居分组或验证容差。

`compose_incremental.py` 实现与V10相同，仅更新范围说明。历史审计 `prior-root` 必须为 `building-by-building-v10/two-district-integration/thirteen-targets`，不能直接传 MAIN/data。MAIN的最终registry验证文件使用项目相对路径，而历史审计根使用本地 `geometry-validation.json`。合并时仍以真实MAIN保留当前六宏/八记录catalog descriptor，绝不能恢复历史prior-root里的四宏catalog。旧11near原字节复用、不重新生成；旧runtime报告仅为明确历史证明，不说本轮重跑。

## 当前实际运行与后续命令

生成前实际运行 `preflight.py`：108对原始/快照SHA匹配；解析全部15个源输入为9宏/15owner；旧13个boundary与实际MAIN完全相同。`preflight-report.json` 与同SHA的 `preflight-before-generation.json` 保存生成前历史状态和完整argv数组，不应把其中 `output_currently_exists:false` 当成生成后的状态。

随后在root批准的独占窗口，博物馆生成/Three+Meshopt解码、图书馆生成/解码均实际退出0。博物馆46,978三角面、37,810压缩字节；图书馆111,724三角面、97,694压缩字节。每源对象/目标分组/保留邻居的Float64位置、材料与winding均与原始近景一致，无未分配三角面。严格法线数值相等比较分别有424/2062面不相等，报告保留 `pass:false`；按原有冻结策略的方向比较仍通过，最大方向差分别1.4976755e-6°与4.1947233e-7°，没有放宽1e-5°/1e-7分量限制。

轻量Python合并已实际退出0，`fifteen-targets/` 为15owner/9宏/13near；旧11near总937,208字节原样复用，旧13owner/7宏对象、27导航及8记录/6catalog字节保持一致。`post-generation-preservation.json` 是运行后的实际守恒检查。模型外观、导航、浏览器没有接受；全15owner实际runtime生命周期检查等待root下一个独占窗口。

预检首尝试发现旧文档里的项目内gltfpack路径不存在，失败脚本/原因保存在 `preflight-history/attempt1`。实际安装入口为 `/workspace/shanghai_tools/node_modules/.bin/gltfpack`；现在绑定共享 `external-tool-lock.json` 中全部五个真实JS/WASM/包信息/许可证文件，不下载依赖。

```bash
python preflight.py --report preflight-fresh.json
```

`preflight-report.json` 的argv保留本轮准确执行方法。两个target-only生成、逐个真实Three/Meshopt几何验证与合并现已完成，不要重新覆盖 `fresh/<ID>` 或 `fifteen-targets/`。下一个动作是 `runtime_owner_check_after_composition_argv`，须由root安排独占窗口。生成器最初只输出draft；实际几何检查成功后才成为source-geometry complete registry，这不表示新精细模型或浏览器接受。

重放生成须使用新隔离输出目录；当前 `preflight.py` 故意拒绝既有fresh目录。对于已生成批次，运行 `verify_composition_preservation.py --report NEW-REPORT.json` 做运行后SHA/旧owner与邻居守恒检查。MAIN、旧source、工具或输入漂移即停止并重新核对；本目录不授权修改MAIN，不启动浏览器或Blender，不生成registration accepted。

## 导航仍未完成

`navigation-proposals/*.pending.json` 都是 `modern-source-bound-navigation-proposal-v11` 的pending记录，registrar必须拒绝。库馆首版真实raw最高27.3999996米，不再使用早期25.7米女儿墙估计作为整体高度。首版raw存在窗框约18mm墙缝/13mm台缝，作者正在geometry-v2修正；旧raw及失败证据不重写。初校只读取B独立真实raw bounds报告并核对raw SHA，不扩展成真实三角面足印/碰撞验收。

最终导航须绑定修正后actualraw和现行源freeze；重新检查角色、相机臂、入口及邻居构件，明确map/实体source组件和真实浏览器观察。博物馆源freeze尚未完成，西前场候选同样不能提前登记。
