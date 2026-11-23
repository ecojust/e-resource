# 新华路231号住宅花园侧木构山墙与交叉瓦顶

上海市房屋管理局第三批优秀历史建筑名录在长宁区以3M012登记新华路231号住宅。央广网2017年的介绍称这里为荣漱仁旧居，并记有南面的花园。长宁区2024年的街区介绍称其为带有意大利风格的二层砖木英国乡村别墅。[市级登记](https://fgj.sh.gov.cn/yxlsjz/20210922/bc5957926d80432b8bea0157eb16bb94.html) · [央广网](https://travel.cnr.cn/list/20171121/t20171121_524034297.shtml) · [长宁区](https://www.shcn.gov.cn/col7343/20241009/1269297.html)

2023年人民网刊出的斜俯照片中，向花园突出的山墙有深色木格与浅色填面，邻侧坡屋面开宽老虎窗，后部有相交的瓦脊。原图紧邻门牌说明上方。2019年2月24日与2025年4月7日的正射影像可以复核长屋面和花园的前后方向。树冠覆盖了部分边沿，图上长屋面约20米，平面误差约2至3米。楼层标高和遮挡处墙面仍为比例估计。资料对建造年份有1925与1932两种说法，本研究采用各照片所见的外观。[人民网图文](https://sh.people.com.cn/n2/2023/0627/c350122-40472567.html) · [照片来源与原图控制点](measurements/published-sources.json) · [两期影像测量](measurements/roof-orientation.json)

公开文件包含文字、量取值和原创几何。外部照片与正射影像的版权归各自权利人。

## 花园立面和屋顶模型

从南面花园看，左侧凸出的山墙可辨浅色填面、深色横木和竖木，下部露出红砖色墙面。右侧的宽老虎窗从主瓦坡突出，屋顶后方还能辨认两处横向山尖。模型保留了这些屋面相交的斜线，以及花园山墙和相邻墙面的进退。树冠遮住了大部分首层和侧后墙，模型以简化的封面收合。首层窗数、侧后墙开口、木构分格和屋脊标高的精度都受此限制。[近景原网](../../../data/audit/xinhua-231-rong-garden-roof-v1/first-geometry/full-source.glb) · [远景原网](../../../data/audit/xinhua-231-rong-garden-roof-v1/first-geometry/lod-source.glb)

斜俯照片宽550像素。用花园山尖、两端檐口、木格下缘和老虎窗檐口的七点求相机，再用同张照片后部的两处山尖调整横坡。九点的均方根残差为3.97像素，最大6.35像素。照片和两期航片支持屋脊走向及花园一侧的认定，缺少现场标高和独立的背立面视角。对成网从上俯射和正面投射，每档有162个样点分别命中瓦、脊、木格、灰白墙面或玻璃。近档含62个闭合构件、1,088个三角面，远档为57件、980面。两档均嵌有同一幅原创瓦纹。[实际投影残差与首击结果](../../../data/audit/xinhua-231-rong-garden-roof-v1/first-geometry/mesh-and-photo-check.json) · [近远对照图](../../../data/audit/xinhua-231-rong-garden-roof-v1/first-geometry/model-comparison.jpg)

在本目录运行以下命令可复算原网及证据。环境需有本项目共用的建筑建模工具和 Python 依赖。

```sh
mkdir -p output
python source/build_model.py --output output/full-source.glb
python source/build_model.py --lod --output output/lod-source.glb
python measurements/check_actual_meshes.py output output/mesh-and-photo-check.json
python measurements/roof_views.py output
```
