# 四川路桥三孔桥身与两侧人行道

四川路桥连接苏州河南岸四川中路和北岸四川北路。市房屋管理局第二批优秀历史建筑名录登记为2A014，地址四川中路。北岸邮政总局的钟楼和立面作为定位参照，东面乍浦路桥与更下游的外白渡桥属于独立建筑。[登记、年代与实照](reference-review.json)

上海市政工程志将四川路桥列为钢筋混凝土单悬臂梁加挂梁，建造年份1922。另有资料记1923年新桥建成。表列桥长70.97米，跨径组合17.14＋36.58＋17.14米，车行道12.8米，两侧人行道各2.7米。表列梁底标高6.4米，其参照基准与照片水面和项目地图高程尚未对齐。[市政志原表](https://web.archive.org/web/20160627185318/http://www.shtong.gov.cn/Newsite/node2/node2245/node68289/node68296/node68348/node68354/userobject1ai65878.html)

2010年2月17日高位实照可见两侧人行道、四座带灯具的塔柱、实腹侧面和斜角桥头。2014年1月27日从下游拍摄的照片可辨一大两小三孔及北岸邮政总局。两份照片均由作者自摄，以CC BY-SA 3.0公开。模型使用原创几何。塔柱高度、桥拱外观、侧板分格和灯具细节根据这两期照片估计。[2010年高位实照，Shanghainese](https://commons.wikimedia.org/wiki/File:Sichuan_Rd._Bridge_and_Suzhou_Creek_@2010.jpg) · [2014年沿河实照，Livelikerw](https://commons.wikimedia.org/wiki/File:Sichuan_Bridge_on_Soochow_Creek.JPG)

冻结的地图矢量中，8156319942为闭合的桥面，1775945602为道路中心线。两者分别与现行OSM的w815631994和w177594560对应。新旧桥面交并比98.05%，中心线最大偏差0.48米；两侧步道在现行图面内各长约72.4米。底图范围含桥头过渡，尺寸和桩位以市政志表中主桥为准。东面乍浦路桥的独立闭合范围距本桥最近164.15米。[地图测量与原始编号](map-evidence.json)

原生工程与三份GLB保留完整三孔、梁腹、四座灯柱与桥上的道路和人行道。模型高度相对于照片中的水面估计。网页独立页提供下游侧立面、斜视与俯视三个视角。[近远景与可编辑工程](../../../assets/models/candidates/huangpu-sichuan-road-bridge/manifest.json) · [独立查看](../../../sichuan-road-bridge.html) · [原生与射线核验](../../../data/audit/sichuan-road-bridge-v1/README.md)

按项目工程环境安装Python、Blender、gltfpack、ImageMagick 7、Node.js和Open Image Denoise后，可从上海项目目录运行以下命令。渲染使用单线程Cycles、12次采样，原图与航片均未嵌入模型。

```bash
python -B source/precise/huangpu-sichuan-road-bridge/source/build_model.py --out assets/models/candidates/huangpu-sichuan-road-bridge --audit data/audit/sichuan-road-bridge-v1
python -B data/audit/sichuan-road-bridge-v1/check-surfaces.py --manifest assets/models/candidates/huangpu-sichuan-road-bridge/manifest.json --out data/audit/sichuan-road-bridge-v1/surface-checks.json
```
