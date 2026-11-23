# 隆昌公寓北院

隆昌路362号的五层住宅由四翼围成一座开敞庭院。临街红砖墙的西北角与北翼窗列可从两张2018年照片比对；院内四道连续外廊、混凝土梯塔和屋缘花带对应2012年多幅不同角度的院景。[普通模型页](../../../longchang-apartments-grant-road-barracks-courtyard.html) · [历史照片和文献](SOURCES-LICENSE.md)

## 模型范围

北院列入上海市第五批优秀历史建筑，编号5G002。临街长边采用航片屋檐估算，约65.7米。院内柱列与栏板的层距由2012年照片拟合，约3.73米。四边外廊采用文献所载的约两米宽。原始航片受屋檐视差和遮挡影响，单边误差约一至三米。[北院范围与影像日期](measurements/footprint-and-date.json) · [院内照片标定](measurements/court-short-end-photo-station.json)

2012年12月的街面近照可辨362号门牌、石套和分列的两扇绿色铁栅。2018年照片中街树与商铺遮挡了院门的沿街位置，展示采用长边中点32.86米，净宽2.80米、净高3.05米均为估值。北窗与南近段有实照支持；南翼较深处和东面按檐口与外墙范围收尾，街面店界仅具示意精度。院内普通门窗的重复节距用于表现外廊背墙。[街墙逐轴记录](measurements/street-and-returns.md) · [门套实样](measurements/west-entrance-documentation.json)

两条长翼各有一座向院内突出的梯塔。近照中相邻两面的斜板分别爬升约四分之一层和半层，折处有平直平台。模型保留柱、梯段、实心栏板、屋檐及压花边带，背阴面的遮挡、踏步数量和回接段按层高估算。[楼梯原像控制](measurements/stair-photo-points.json)

## 复建和下载

从项目根运行以下命令可重建两档几何。压缩和独立解码需要项目现有的 gltfpack、Node.js 以及 meshopt 解码器。

```bash
S=source/precise/yangpu-longchang-apartments-grant-road-barracks-courtyard/source
python "$S/build_model.py" --output exports/full-source.glb
python "$S/build_model.py" --lod --output exports/lod-source.glb
python "$S/package_model.py" exports packaged
python "$S/package_editable.py" prepare packaged editable
python "$S/package_editable.py" run packaged editable
```

下载菜单提供原始三角网、压缩近景与远景；编辑工程随实际版本清单载入。源内十个视角均以同一局部米制坐标保存。[相机参数](source/cameras.json) · [模型检查](../../../data/audit/longchang-apartments-grant-road-barracks-courtyard-v1/README.md)
