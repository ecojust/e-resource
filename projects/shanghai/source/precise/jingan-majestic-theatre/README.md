# 美琪大戏院

模型采用 2017 年 9 月 9 日修缮后拍摄的江宁路、奉贤路街角日景和夜景，重建圆形门厅的五条竖窗、三组入口、弧形雨棚、两层红字招牌、沿街展橱和侧墙。后部观众厅、后台以及不可见立面的尺寸依据屋顶影像和地图轮廓估计。全部窗棂、字牌、檐线与门洞均为可编辑几何。[独立预览](../../../majestic-theatre.html) · [街角日景](https://commons.wikimedia.org/wiki/File:Majestic_Theatre_(20170909101737).jpg) · [同日夜景](https://commons.wikimedia.org/wiki/File:Majestic_Theatre_(20170909185536).jpg)

[原始 GLB](../../../assets/models/candidates/jingan-majestic-theatre/jingan-majestic-theatre-raw.glb) · [网页 GLB](../../../assets/models/candidates/jingan-majestic-theatre/jingan-majestic-theatre-web.glb) · [远景 LOD](../../../assets/models/candidates/jingan-majestic-theatre/jingan-majestic-theatre-lod.glb) · [可编辑 Blender 工程](../../../assets/models/candidates/jingan-majestic-theatre/jingan-majestic-theatre.blend)

## 地址和年代

范文照设计的戏院于 1941 年开业，1958 年转为演出为主，2016 年结束历时五年的修缮并重开。2024–2025 年的升级主要涉及舞台吊杆、承重、后台与乐池。模型将门厅与雨棚的外观年代标为 2017 年。[建筑沿革](https://zh.wikipedia.org/wiki/美琪大戏院) · [2017 年恢复电影放映](https://culture.people.com.cn/n1/2017/0510/c22219-29265158.html) · [2025 年静安区报道](https://www.jingan.gov.cn/rmtzx/003008/003008006/20250514/170f222e-2e8f-48a5-a698-50a20f2d410b.html?type=2)

2013 年至 2017 年的六张照片可比对屋顶独立字母、弧形雨棚、后移门扇和临街墙脚。2017 年夜景提供窗中竖向铅条与几何格纹的依据。屋顶、边墙、门窗比例、花饰纹样及字形均未实测。邻地塔楼、电线、临时海报和剧场内部未纳入工程。[逐图来源、作者及文件散列](reference-review.json) · [地形与源建筑依据](footprint-review.json)

上海市房屋管理局首批名单的 1B001 记载江宁路 66 号。区政府和剧院报道也使用 66 号。项目工作名录与 OpenStreetMap 另有 99 号，两种门牌均指向江宁路、奉贤路转角的圆形门厅。[市房屋管理局第一批名录](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html)

## 复建

在仓库的 `projects/shanghai` 下，安装 Python、NumPy、Shapely 2.1 以上、fontTools、Node.js、Blender 4.3、gltfpack、ImageMagick 和 Open Image Denoise。模型以米为单位。Blender 的 X、Y、Z 分别向东、北、上。GLB 的 X、Y、Z 分别向东、上、南。建筑原点是登记源面中心。以下命令在临时目录生成四件模型、清单、逐材质三角面比对及从重新打开的 Blender 工程输出的预览。

```sh
python -B source/precise/jingan-majestic-theatre/source/build_model.py \
  --out /tmp/majestic-assets --audit /tmp/majestic-audit \
  --gltfpack gltfpack --oidn oidnDenoise
```

几何程序将门厅、五条嵌入窗、门扇、雨棚、三组招牌、两条临街外墙以及屋顶分为独立部件。五条高窗、框架和店招在远景仍可读，小格窗、曲面分段与装饰细节随版本简化。[几何源文件](source/majestic_geometry.py) · [构建入口](source/build_model.py) · [字体来源](source/fonts/provenance.json)

模型、几何源文件和程序采用仓库 MIT 许可。标牌用 Noto Sans CJK SC 派生并改名的字体子集生成，保留 SIL OFL 1.1 许可。原照片、卫星影像仅供比对，包内未嵌入影像像素。地理登记数据来源为 © OpenStreetMap contributors 与 Overture。[MIT](../../../../../LICENSE) · [字体许可](source/fonts/OFL.txt) · [街角登记对象](https://www.openstreetmap.org/way/429868562)
