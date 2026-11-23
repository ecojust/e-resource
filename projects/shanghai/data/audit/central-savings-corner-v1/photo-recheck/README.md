# 中央储蓄会转角塔楼街面复核

Fayhoo 的天津路正面照片可辨八排窗，每排三扇。黄浦文博的街角旧影也能辨认三列窗和两街翼，现状照片显示门额和出挑装饰已经变化。本轮分别读取三张原照，原始文件尺寸和摘要见[照片记录](photo-reread.json)。[Fayhoo 正面照片](https://commons.wikimedia.org/wiki/File:The_Bank_of_Canton.jpg) · [黄浦文博](https://www.sohu.com/a/1005319047_121123854)

在两幅正面照片上分别记录 24 个玻璃开口中心，再从原始、网页和远景三档网格读取对应的 24 处窗玻璃。每幅图各用八个中心定位，余下 16 个用于复核。Fayhoo 照片取为 600 × 900 像素，三档的中位误差为 2.28 像素，最大 4.76 像素。黄浦文博近照的原文件横置，顺时针转正后以 600 × 800 像素取点，三档中位误差为 0.95 像素，最大 3.88 像素。下部街线经过三排窗，最底排的窗台有部分被门额遮挡。上述比较针对塔楼街面，另有两街翼及转角局部的网格检查。[原取点、模型点及残差](front-sash-registration.json) · [705 条几何射线](../surface-checks.json)

复算时将 Commons 正面原图和黄浦文博近照保存在本地，从仓库根目录运行下列命令。

```sh
python projects/shanghai/data/audit/central-savings-corner-v1/photo-recheck/check-street-windows.py projects/shanghai commons.jpg district.jpg window-check.json
```
