# 鲁迅故居正立面与院门：交付验证

范围为2010/2011年照片参照的局部外观候选，所有尺寸估计。未确认独立地图源对象，未制作整栋屋顶、侧后立面或室内，也没有城市替换或行走验收。验证结果不增加全市逐要素复原完成量。

- `geometry.json`：实际Meshopt解码后的完整/远景三角形坐标与各自原始模型逐项相同；无非有限值、退化面或重复索引面。
- `pbr.json`：实际顶点/UV组合与解码结果一致；三张嵌入PNG逐字节一致，ORM金属通道为零，法线尺度0.35。
- `structure-full.json`、`structure-lod.json`：各10项真实射线探测，覆盖入口退进、窗玻璃、门柱凹槽、阳台板及开启窗扇。
- `negative-structure.json`：人工封住入口、填平门柱凹槽的两个反例均被几何检查拒绝。
- `rebuild.json`：第二次独立生成的原始/远景GLB及三张PNG与交付源文件字节相同。
- `native.json`、`native-geometry.json`：Blender保存重开前后几何哈希一致；保存文件的三角形与GLB完全一致，UV及打包PNG也通过检查；展示舞台排除在建筑几何统计外。
- `browser.json`：实际Chromium验证完整/远景加载及PBR、手动/自动远近切换、损坏文件保留前一模型、重试恢复、390×844手机布局；无页面异常或横向溢出。
- `visual-review.json`：实际查看原生和网页截图后的有限外观检查。未做测绘精度或当前现场一致性认证。
- `source-files.json`：代码、输入、网页和最终资产清单的SHA-256绑定。

网页检查复现：仓库根目录运行`python -m http.server 8000 --directory projects/shanghai`，另一个终端运行`node projects/shanghai/data/audit/luxun-residence-facade-v1/qa-browser.cjs`。需要Playwright及`/usr/bin/chromium`。公开页面可通过`LUXUN_URL`覆盖地址；githack首次访问需要先处理其确认页面。

模型与原生下载见[清单](../../../assets/models/candidates/hongkou-luxun-residence-facade/manifest.json)，来源与估计见[建模说明](../../../source/precise/hongkou-luxun-residence-facade/README.md)。
