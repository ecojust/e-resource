# 主项目验证范围与原始记录

root确认`main20-npm-test.txt`对应session71812退出码0，`main20-asset-check.txt`对应session25351退出码0后才归档。日志保留原字节。资产检查当时统计3876文件、91个GLB（含完整source副本）、15个Bund LOD、12个表面贴图；最大76,875,072 B，严格小于100,000,000 B。不要套用候选应用55个GLB的统计。本次明确跳过另行冻结的全城detail审计；新增本审计/文档文件后，目录文件总数自然可能增加。

`mask-rebind-review.json`是修复阶段的原始报告，当时浏览器视觉仍pending。`mask-targeted-tests.txt`原名`targeted-tests.log`，65项通过；`mask-baseline-negative.txt`原名`baseline-negative.log`，同一7项回归在旧实现上按预期失败。这不是发布失败；它证明测试能够发现旧bug。两个`.txt`只改归档文件名，字节与原log SHA均未改变。最终实际浏览器和root视觉结论在[目录验收](../catalog/README.md)。

三份main安装报告分别记录street47、support58、catalog51的实际apply；07/09四项相同元数据在support中跳过。129独立包另有68文件create-only安装和独立复核，未加入20项导航或accepted目录，`browser_accepted:false`如实保留。原始报告中的绝对源路径只用于追溯当时的stage，不要求发布仓库重建该绝对路径。

最终[运行时代码阶段验证](../../ordinary-runtime/validation.json)与[工具阶段验证](../../ordinary-launcher/validation.json)已有公共副本，不再重复。这里另保留`integration-files.json`原字节，满足发布文档对16文件局部证据的绑定。

[audit-files.json](audit-files.json)给出每个归档文件的实际来源、原SHA、大小和有限用途；它不包含自身，外部完整install-manifest对它另行绑定。所有JSON均原样复制，没有修订内部SHA、passed字段或stage路径。新增README与本清单是范围说明，不伪装成新的测试运行。没有运行额外测试、浏览器或Blender，没有远程发布。
