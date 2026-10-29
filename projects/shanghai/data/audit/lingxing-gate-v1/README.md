# 棂星门中央门框与门扇候选检查（2026-10-29）

仅中央石门框及两扇门叶；两侧门、院墙、石狮、字刻及精确龙雕未建模。2005年姿态与2021年下部实板参考组合，不是单一日期现状。尚未城市配准或完整照片复原验收。

- [几何检查](geometry.json)：近景15,692三角面、97个源构件；远景2,076三角面、77个源构件。顶点有限、无退化面，逐源构件封闭、正体积、法向一致，导出面数一致。对实际导出石框作射线量测，净开口约3.35×3.6米；中央通行空隙与两扇门的竖栅间隙均通过射线验证。
- [Blender保存重开](native.json)：Blender 4.3.2，建筑模型几何哈希重开一致；舞台不计入建筑。
- 实际Cycles预览：[正面](native-front.png)、[斜侧](native-oblique.png)、[背面](native-rear.png)。对照来源照片检查石柱、横梁与红门；雕纹为简化云纹，整体高度/柱截面为估计。斜侧采用负X方向，避免右侧开门被石柱完全遮挡。
- [网页检查](browser.json)、[最终截图](browser.png)：SHA256校验加载、完整/远景/完整切换、四个视角、室外漫游进入/行走/Esc退出。沿用外围碰撞，几何洞口不等于开放院内漫游。

各模型文件均小于100 MB；大小与哈希见[资产清单](../../../assets/models/candidates/chongming-lingxing-gate/manifest.json)。照片不再分发或嵌入；链接、许可、哈希及各参考日期见[来源说明](../../../source/precise/chongming-lingxing-gate/README.md)。

复测网页：在`projects/shanghai`运行`python -m http.server 8767`，仓库根目录运行`node projects/shanghai/data/audit/lingxing-gate-v1/qa-browser.cjs`，需Playwright和`/usr/bin/chromium`。输出到`/tmp/lingxing-gate-browser.*`。构建与几何验证命令见来源说明。

## 已发布页面

[公开页面检查](public-browser.json)针对固定提交`bee34f08d2b7c8b6e545f16691d2b8b06d81b0d9`：点击托管服务首次访问提示“Open the page”后，模型通过SHA256校验并加载近景，未记录页面错误。可在仓库根运行`node projects/shanghai/data/audit/lingxing-gate-v1/qa-public.cjs`复验；该记录不扩大几何或照片验收范围。
