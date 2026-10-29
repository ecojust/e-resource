# 孙中山故居主楼候选验收

范围：独立外观模型、原生文件、PBR及独立网页；没有城市替换、漫游或精确复原验收。完整/远景分别81,088/8,084面，所有交付文件严格小于100,000,000字节。

- `geometry.json`：真实Meshopt解码后的三角坐标与源文件逐项一致；有限数值、非退化及重复索引检查。
- `pbr.json`：解码前后墙面每个三角角点的坐标/UV对一致，三张512×512嵌入PNG与源码纹理字节完全相同；法线强度0.35、无TANGENT、ORM金属通道为零。
- `structure-full.json` / `structure-lod.json`：四个外拱开口通向2.3米内退门面、三组上窗玻璃内退0.22米、六级踏步高度、正面天花没有共面穿出；12个侧墙探针确认转角及内墙端部只保留一层外表面。
- `overlap-regression.json`：旧版本会分别在浅色天花与墙共面、侧墙与端部重复面处失败，修正版通过同一检查。
- `native.json` / `native-geometry.json`：Blender导入面数、保存重开网格哈希、原生三角坐标、实际UV翻转和三张嵌入PNG核验。
- `rebuild.json`：另一个输出目录从源码重建完整/远景GLB及三张程序纹理，字节一致。原生文件不承诺字节确定性。
- `source-context.json`：3433号源对象身份/轮廓一致。同宏块距源轮廓50米内11个邻近要素与模型凸包没有平面重叠。凸包是保守包络，越出原源轮廓约7.74平方米；不代表实测墙线，也不是跨宏块邻域、碰撞或步行验收。
- `browser.json`：真实Chromium加载完整/远景网格、PBR图像和法线强度；损坏文件保留旧模型与重试；自动距离切换、回近、移动端布局及页面异常检查。
- `visual-review.json`：最终原生、网页和移动截图的人工观察及文件哈希。侧后墙缺少完整参考，仍为明确标记的封闭估计面。
- `source-files.json`：本批源码、输入、网页与实际资产清单的字节绑定。照片作者/许可见源码目录的README及登记JSON。

先在`projects/shanghai`运行`python -m http.server 8000`，再运行`node data/audit/sun-yatsen-residence-v1/qa-browser.cjs`（Playwright与`/usr/bin/chromium`）。其余核验脚本位于`source/precise/huangpu-sun-yatsen-residence/source/`，均提供命令行参数。脚本通过不等同于照片外观完整或测绘准确。
