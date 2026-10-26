# 北大街222号：照片支持的相对比例

本次可以核对上廊三开间的相对宽度；没有建立可靠的地面基准绝对高度。`calibration-independent.json` 明确设 `absolute_height_calibrated=false`，`ground_referenced_metric_homography=null`。这不是测绘或现场摄影测量成果。

主图为 Fayhoo 于 2016-02-07 拍摄的 [Commons 原图](https://commons.wikimedia.org/wiki/File:Zhujiajiaozhen_Beidajie_222_Hao_Minzhai.JPG)，CC BY-SA 3.0。保留原 JPEG 字节，SHA-256 为 `0de9bdfd14748cbb624e3847bdff68d7a5adb4d18ff9027b25e3a71d5e72584b`。比较图是加线标注的分析派生图，同样按 CC BY-SA 3.0 归属 Fayhoo；未把它作为模型墙面贴图。

照片 EXIF 为 Nikon D90 / 18 mm，Orientation 1。实际存储 1424×2144，EXIF 声明 2848×4288，比例相同且恰好减半；这支持短传感器轴对应竖幅图像宽度，但不证明具体处理链或无裁切历史。不得再次旋转图像。Nikon 的[官方 D90 规格公告](https://www.nikon.com/company/news/2008/0827_d90_01/)列出“23.6 × 15.8 mm CMOS sensor”，本次 K 使用存储轴对应 `[15.8,23.6] mm`。`camera-source/nikon-d90-source.json` 保存官方 URL、短规格引用及响应 SHA，不依赖分发整页 HTML。

以可见横向构件和立柱作为两组正交方向，在相机归一化射线中拟合。四个开间边界与同一上廊扶手线相交后，透视校正得到照片从左到右三跨宽度比例：

| 跨 | 名义比例 | 256 次扰动的 5–95% 敏感性范围 |
| --- | ---: | ---: |
| 左 | 0.337 | 0.321–0.358 |
| 中 | 0.345 | 0.326–0.362 |
| 右 | 0.319 | 0.293–0.340 |

结果支持近似三等开间。不能用倾斜照片的屏幕宽度直接分配三跨。控制线端点 RMS 约 5.93 原图像素；扶手方向单线残差较大，约 15.43 像素，反映人工拾点、木构非理想直线和未标定镜头的限制。范围仅是控制点/相机假设的敏感性，不是测量置信区间。

报告包含原图像素↔任意单位正面平面的互逆矩阵，以及一个明确有条件的米制变换：只有把卫星来源约 11.98 m 的屋顶边宽等同于上廊端柱平面宽度时才成立。这个等同关系并未获得现场证明。其 z=0 是上廊扶手中点，**不是地面**，不能当世界高度 H 或整面玻璃采样映射。上廊、檐口、首层柱子、后退门面各处于不同深度，不能直接把条件柱段数值相加为楼高。

2022 钉钉的 CC BY-SA 4.0 照片提供独立形态佐证：三开间、两根上层独立木柱、四根首层白柱、弧托、回纹栏杆及双狮。它使用 Samsung SM-A5160 的约 13 mm 等效超广角，顶端被裁去且畸变校正未知，未用作第二个绝对高度相机。两个原图都已实际查看。

两层建筑的檐高 7–9 m 仅是供建模选择的宽泛建筑形态推定，未由摄影恢复；屋脊、出檐和上廊进深也未独立测定。旧 GHSL 8.579 m 没有作为拟合约束。建模若选择单一值，应继续标作估计。

## 复算及范围

在 `next` 目录执行：

```bash
python common/photo_plane_proportions.py qingpu-beidajie-222/calibration-independent-controls.json --samples 256
```

新模块复用既有 `photo_metric.py` 数学函数，后者 SHA-256 仍为 `dcab74584b59a7c891bbf13125b9c693908bb8ffcdac50444489d834abc8019c`，没有改动已发布的 05/06/14 或 07/09 标定。`next/common` 在当前工作区是公共目录的符号链接，发布时应带上这些新增模块及其依赖，不依赖工作区绝对路径。

所需原图、短相机来源记录和控制点均使用相对路径。`calibration-independent-comparison.png` 已人工查看，原图矩阵与逆矩阵最大数值误差约 1.4e-16。完整文件 SHA 和验证结果见 `geometry-metric-files.json`、`geometry-metric-validation.json`；不涵盖并行建模器仍在修改的模型输出。
