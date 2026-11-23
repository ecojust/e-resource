# 襄阳南路362号照片中的三券与圆端檐口

Antigng 于2018年8月2日拍摄了一幅题为《襄阳南路362号住宅》的照片，院侧可见三个拱头窗、圆端上下两层钢窗和带齿饰的弧形檐口。上海市房屋管理局的5D023登记行写“襄阳南路364号”。街景中的364号绿牌在另一幅图明确可见。此件以362号照片独立陈列，两处之间的屋界关系尚待核实。[署名原照](https://commons.wikimedia.org/wiki/File:襄阳南路362号住宅.jpg) · [市房屋管理局](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html)

中央券净宽暂按1.50米作展示标尺。其起拱点为零高，中轴为X0，X向画面右，Y进墙。相机拟合九处券缘，误差1.01至3.87像素，量图宽1000像素。圆端檐顶沿八个实见点拟合半径约1.90米。建筑内部及树遮的另一端留待实证。截面止于起拱线下0.30米，保留照片露出的窗头。齿数、弧面窗细横档和墙厚为局部估计。

模型由 `source/court_arcade.py` 的 `add_court_arcade(b,lod=False,layout=None)` 生成。用同文件的命令行传入输出GLB路径，远档另加 `--lod`。检测脚本 `measurements/check-court.py` 依次读取两份GLB和输出目录，传入 `--photo` 与原图路径可重绘图板。两档各自的23束构造取样全部命中；按原照固定的16个像点各命中15处，剩下一束在圆端窗的横钢梃与玻璃分界处。原图和图板中的裁片署名 Antigng，按 CC BY-SA 4.0 许可共享，图板亦按此许可发布。模型中使用原创纯色材质。[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

| 角色 | 闭合构件 | 三角面 | SHA-256 |
| --- | ---: | ---: | --- |
| near.glb | 79 | 8920 | c40fa4c39527db45d08cb9740ed6b0ed1415a23c7b76e1f295f586d7c60e91bd |
| far.glb | 79 | 4420 | 10b99c1af70ec4eb80243b229368d37c637d4fd609d70e62da6166a1acff8cb8 |

## 下载与对照

[近档GLB](../../../assets/models/candidates/xuhui-xiangyang-south-362-courtyard-arcade/xuhui-xiangyang-south-362-courtyard-arcade-near.glb) · [远档GLB](../../../assets/models/candidates/xuhui-xiangyang-south-362-courtyard-arcade/xuhui-xiangyang-south-362-courtyard-arcade-lod.glb) · [署名照片与模型投影](../../../data/audit/xiangyang-south-362-courtyard-arcade-v1/photographic-comparison.jpg)
