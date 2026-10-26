# 汽车博物馆与包玉刚图书馆：原建筑分组和近景来源

本目录投递已经实际检查的源身份、近景变体、生成代码与证据。范围为 15 个 owner、9 个宏、13 个近景块、186 个源对象，保留其中 171 个邻居对象。只新增博物馆和图书馆两个近景变体；原 13 个 owner 和 11 个变体保持原字节。本来源清单不授予模型外观、导航、网页抑制、目录或发布验收。

| 目标 | 源宏 / owner | 原样保留的同块邻居 |
|---|---|---|
| jiading-shanghai-auto-museum | 14-13706-6691 / 870 | 735、797 |
| minhang-baoyugang-library | 14-13718-6705 / 201 | 35、60、299、333、375、466、947 |

博物馆宏的 12 个 residual 保持不变。图书馆 201 与邻馆 375 的原始简化轮廓约 0.0761915008 平方米重叠保留，没有裁剪或合并 375。这里的 local ID 是冻结城市数据的身份，不是浏览器矢量 source ID；实际 MVT 分量观察由应用的独立证据集提供。

两个新变体分别为 37,810 和 97,694 字节。真实 Three/Meshopt 检查确认位置、材质、绕序、owner 与保留邻居一致。严格法线逐位比较分别有 424 / 2062 个三角面不相同，原报告中的 false 保留；既有 1e-7 分量、1e-5 度方向限值内的检查通过，没有改变容差。之后实际读取全部 15 个目标的 far/near，检查独立可见、邻居保留、near 退出、恢复与销毁，见 `evidence/runtime-owner-validation.json`。投递组装只复核哈希和报告绑定，没有重跑生成或解码。

## 证据时序和公开路径

`evidence/geometry-validation.json`、`evidence/runtime-owner-validation.json` 和 `evidence/post-runtime-preservation.json` 是对应实际阶段的原始结果。`history/`、`baseline-lock.json`、`evidence/composition-report.json` 及 `evidence/runtime-handoff.json` 保留形成时的 pending/false 状态，不能把这些历史状态当成后续模型或网页结论。早期 README 写的“runtime 等待”和“公开 commit 未绑定”没有被改写；后续实际运行见 runtime 报告，原 27 导航应用的真实提交引用见 `baseline-publication-reference.json`。这不是新应用的发布记录。

原报告保留真实工作目录绝对路径。`public-path-mapping.json` 映射本次明确投递的原路径、公开路径、字节数和 SHA；没有宣称 108 个基线快照或全部历史工作目录均被复制。新宏的原始数据、near/far、源生成代码和本次 11 个源对象的审计引用分别来自冻结清单或明确的实际比较输入。旧 11 个变体、项目 vendor/运行时代码仍使用项目原文件，不重复交付。现代精模源包、照片、当前 raw 导航提案、MVT 观察与最终网页证据由各自投递流程提供，未递归加入研究目录。

## 复核与重建

本目录 `inputs/` 含全部 15 个原始 geometry-input 和解析器需要的两份 provider mapping。`tools/build_precise_overrides.py` 可配合仓库现有冻结城市数据重建；Python 依赖见 `baseline/project/source/city/detail/requirements.lock`，压缩器精确依赖见 `external-tool-lock.json`，真实运行时依赖见 `runtime-dependency-lock.json`。使用新的仓库外输出目录，不能让检查器覆盖这里已审核的证据。

从本目录运行下列命令前，将 PROJECT、NEW、GLTFPACK 替换成自己的绝对路径；NEW 必须是新建的隔离目录。这是重建方法说明，本投递阶段没有执行：

```bash
python tools/build_precise_overrides.py --project PROJECT --output NEW --geometry-input-root inputs --ids bund05 bund06 bund07 bund09 bund14 hongkou-hongde-church jiading-shanghai-auto-museum minhang-baoyugang-library putuo-zhenru-main-hall qingpu-beidajie-208-212 qingpu-beidajie-222 songjiang-fangta-pagoda xuhui-longhua-pagoda xuhui-wukang-129 xuhui-wukang-210 --asset-prefix assets/city-overrides-v6 --gltfpack GLTFPACK
node tools/verify_override_geometry.mjs NEW/geometry-comparison-input.json
node tools/verify_override_runtime.mjs PROJECT NEW/precise-buildings-v6.json
```

只有实际检查完成才能产生新的结果。`compose_incremental.py`、`preflight.py` 和 `delivery/prepare_manifest.py` 保留原工作区流程，依赖明确的历史目录和基线，不是可以在任意机器无参数运行的便携入口。重放旧报告需在新目录映射路径，不得修改原证据后沿用原 SHA。完整重建入口会生成新的逐对象比较引用，不依赖旧版本的全部审计工作文件。

项目原创代码沿用 MIT。城市轮廓及派生数据保留 OpenStreetMap contributors / Overture Maps 的原来源和 ODbL 署名；高度来源沿用原冻结城市资料中的 CMAB、CNBH、GHSL 等记录及许可。本来源包不改变或重新授权这些数据，没有照片像素、全量网页或私有参考图。每个投递文件严格小于 100,000,000 字节。
