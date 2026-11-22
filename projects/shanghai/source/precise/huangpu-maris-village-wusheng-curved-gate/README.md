# 马立斯新村武胜路北门弧形铁架与四字门牌

上海市第五批优秀历史建筑名录的 5A020 项记作“马立斯新村”，地址为武胜路 429 号。2017 年 10 月和 2020 年 2 月的街景可以读到北门上“重新小区”四个金字，2017 年同一画面的绿色门牌可以读到“429弄”。登记点与现代北门点分列。重庆北路 216 弄的另一座入口距这里约 142 米，两座门的结构和石柱外观均有区别。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [历年现场依据](measurements/street-sign-sources.json) · [位置复核](measurements/footprint-review.json)

两道弧形铁架之间悬着四枚黑底描金圆牌。“重、新、小、区”的笔画取自 2017 年、2020 年两次街景中可以相互对照的描金边界。“重”字留有两处笔画围成的黑色空间。以上方字牌为参照，武胜路 2021 年正面街景记录了两扇关闭的铁门。门扇下部各有圆花心和左右卷枝。前两年的斜向街景还分别记录了敞开的门扇、左侧贴瓷砖的矮墙和折回门洞的矛头栏杆。右侧砖墩留有绿色 429 弄门牌。三块素色公告板表示 2021 年遮住扇面竖杆的实际位置，原图上的公告内容省略。[门扇测量](measurements/gate-leaf-trace.json) · [四字轮廓](measurements/gate-medallions.json) · [弧形门架测线](measurements/gate-frame-trace.json) · [查看三维](../../../maris-village-wusheng-curved-gate.html)

模型以门洞名义宽度 3.05 米定标，沿地面取 X 轴，朝弄内为正 Y。两根门柱和门扇合缝用于估算街景的俯仰与侧倾。门扇和铁架的截面、砖墙进深、左侧短墙长度属于估算。门架的现状有 2017 至 2021 年的街景依据，建造年代尚待档案确认。近景和远景都保留门牌笔画、左右门扇及其花心和窗隙。每档导出均用 134 条射线复核，含 32 个金漆和 16 个黑底位置。[字牌逐点首交](measurements/released-gate-letter-review.json)

## 从源码重建

在本项目的完整工作树内，从本目录执行以下命令。七个镜位可在相机清单中检查；两种分辨率采用同一套现场坐标。

```sh
python source/paint.py
python source/build_model.py --output maris-full.glb
python source/build_model.py --lod --output maris-low.glb
python source/build_blender_source.py --check-raw maris-full.glb
```

[弧形铁架与街面墙栏](source/gate_head.py) · [双扇铁门](source/gate_leaves.py) · [四块描金字牌](source/measured_medallions.py) · [七个镜位](source/cameras.json) · [来源与许可](SOURCES-LICENSE.md)
