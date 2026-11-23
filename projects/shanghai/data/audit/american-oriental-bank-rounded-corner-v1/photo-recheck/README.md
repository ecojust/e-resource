# 美丰银行弧形街面的照片与网格复核

重读 2015 年街照和 2023 年黄浦区报道的原图。以宁波路与弧面的切点为零，沿街比较两张照片各自估算的七条窗轴，位置差的中位数为 0.08 米，最大为 0.74 米，出现在宁波路直街段。四个原足印节点约束的转角半径为 7.91 米，弧长为 13.56 米。2025 年文章使用了与 2023 年报道同一画面的衍生图，两者缩略彩图相关系数为 0.99946。[独立街照](https://commons.wikimedia.org/wiki/File:Former_American_Oriental_Banking_Corporation_Building.JPG) · [黄浦区报道](https://www.thepaper.cn/newsDetail_forward_22089072)

按发布清单读取原始 GLB，另解码网页和远景 GLB。每档的 282 条射线均与保存的原始复核逐条吻合，共 846 条，覆盖砖纹、窗梃、店面入口构件、室外机与弯管。三档保留相同的砖纹图像。[新复核数值](photo-and-mesh-recheck.json) · [逐道射线](../preflight/rays.json)

在此目录运行 `python verify-photos-and-meshes.py /tmp/meifeng-review` 可重新获取三张原图并检查本仓库中的模型。模型覆盖转角及与其相连的两段街面。其余两翼、后墙和室内待补资料。
