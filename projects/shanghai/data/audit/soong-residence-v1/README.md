# 宋庆龄故居主楼候选：验证记录

本批为2013/2016/2019年照片参照的外观候选，所有尺寸、屋面曲率、入口门廊位置和隐藏构造估计。没有附楼、花园、室内、地图替换或行走验收，不增加全市逐要素复原完成量。

- `geometry.json`：实际Meshopt解码后完整/远景模型的三角形坐标与对应原始GLB完全一致；无退化面、非有限值及重复索引三角面。
- `pbr.json`：解码前后顶点/UV组合和三张嵌入PNG一致；512像素原创墙材质，ORM金属通道为零，法线尺度0.35。
- `structure-full.json`、`structure-lod.json`：各12项实际射线检查，覆盖三扇老虎窗玻璃前的屋面切口、开放柱廊、玻璃凹进、曲线阳台板和四处曲面屋顶高度。
- `negative-structure.json`：用屋面封住老虎窗、封闭柱廊的两个反例均被检查拒绝。
- `rebuild.json`：独立重建的原始/远景GLB与三张PNG字节完全相同。
- `native.json`、`native-geometry.json`：Blender保存重开几何哈希一致；保存文件真实三角面、UV及打包贴图与源GLB匹配；展示集合排除在建筑统计外。
- `browser.json`：真实Chromium验证完整/远景、PBR、手动及自动远近切换、损坏文件保留前模型及重试、手机布局，无页面异常或横向溢出。
- `public.json`、`public.png`：公开固定提交页面无拦截加载完整/远景/PBR成功，无页面异常；`node qa-public.cjs`包含githack首次访问确认处理，可复现。
- `visual-review.json`：实际查看最终原生与网页截图后的有限外观检查，不证明测绘精度或当前状态。
- `source-files.json`：交付代码、输入、预览网页和最终模型清单的SHA-256绑定。

浏览器检查：仓库根目录运行`python -m http.server 8000 --directory projects/shanghai`，另一个终端运行`node projects/shanghai/data/audit/soong-residence-v1/qa-browser.cjs`。需要Playwright与`/usr/bin/chromium`。

下载见[资产清单](../../../assets/models/candidates/xuhui-soong-ching-ling-residence/manifest.json)，原图、事实与估计见[来源说明](../../../source/precise/xuhui-soong-ching-ling-residence/README.md)。
