# 棂星门照片左侧门候选检查（2026-10-29）

范围为照片左侧门的历史双柱框架与近全开门叶；绝对方位未核验。1990年代框架与2021年姿态明确组合，不是单一日期实物复原。右上柱纹饰、柱高和门面细分为估计；未城市配准或完整照片复原验收。

- [实际导出几何](geometry.json)：近景5,900三角面、65个源构件；远景1,420三角面、57个源构件。逐构件封闭、正体积、法向一致，导出无退化面、顶点有限、面数与源相同。石框射线测得净开口约2.3×3.2米，中央空隙与两扇门的栅条间隙均畅通；右上柱几何存在，避免把2021年的树叶遮挡误建成短柱。
- [Blender重开](native.json)：保存重开后模型几何哈希一致，预览舞台不计入建筑。
- 实际Cycles渲染：[正面](native-front.png)、[斜侧](native-oblique.png)、[背面](native-rear.png)，已对照两个年代来源检查柱框关系与门叶近全开姿态。
- [网页检查](browser.json)、[截图](browser.png)：SHA256校验加载，近景/远景/近景切换，四视角与室外漫游进入、行走及Esc退出。外围碰撞不提供穿门入院。

所有模型文件各自小于100 MB；大小与SHA256见[资产清单](../../../assets/models/candidates/chongming-lingxing-photo-left-gate/manifest.json)。照片不再分发或贴图。来源差异与估计范围见[来源README](../../../source/precise/chongming-lingxing-photo-left-gate/README.md)。

复测网页：在`projects/shanghai`运行`python -m http.server 8768`，仓库根目录运行`node projects/shanghai/data/audit/lingxing-left-gate-v1/qa-browser.cjs`；需Playwright及`/usr/bin/chromium`，输出位于`/tmp/lingxing-left-gate-browser.*`。
