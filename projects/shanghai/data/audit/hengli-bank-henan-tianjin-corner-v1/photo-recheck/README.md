# 恒利银行两条街面的窗轴复核

重读银行博物馆的历史图、2015 年转角照片和两条街面的逐门调查照片，共 16 张。河南中路一面较长，浅色竖窗带下方有一扇黄铜色门，靠边另有 503 号酒店入口。天津路的浅色窗带夹在两个棕砖端部之间，南京东路幼儿园的入口在两街交会的斜角。[原图与文件指纹](photograph-identities.json) · [历史照片与门牌依据](../../../../source/precise/huangpu-hengli-bank-henan-tianjin-corner/README.md)

在 2020 年街面调查的两张照片上，沿同一层窗洞取一条随透视倾斜的采样带。两张图分别可分辨 18 条和 6 条窗轴。保存的像素坐标以等比例缩小后的图像为准。原始、网页及远景网格各以 243 道射线重查街面，再各以 72 个采样点复核棕砖贴图。三档逐项输出与原审核相同。[采样位置和验证结果](window-axes-and-mesh.json) · [逐条射线记录](../surface-checks.json)

安装 ImageMagick、Node.js、NumPy、SciPy 和 Pillow 后，可在本目录运行 `python check-window-axes.py /tmp/hengli-window-axes.json` 重作两张调查照片和三档网格的检查。完整屋顶、背面和室内仍待补充资料。
