# 中孚银行北立面与爱奥尼柱廊

滇池路103号的原中孚银行大楼建于1922年，第五批上海市优秀历史建筑名单的编号为5A036，现有中国建设银行上海第四支行。北立面面向滇池路，四行窗下是有六根凹槽石柱的门廊。临街台阶两侧各有一对柱脚共用长方形石座，西端另有一扇高门、门上格窗和两道石罩。相邻105号为公平大楼。[登记、摄影和相邻门牌](measurements/street-observations.json)

模型用Fayhoo的近照读取窗扇、石质柱头与檐部，用2017年4月15日档案照片读取台阶、石座、纵深、背墙与街门。近照未注明拍摄日期，Commons的2015年1月19日是上传日期。近照中34个窗框及14台外机有各自量点。东端两处窗被银行招牌遮挡，其位置结合斜照和楼上同轴窗推算。[北墙测点](measurements/north-wall-openings.json) · [门廊背墙](measurements/rear-porch-openings.json)

普通城市模型内的建筑编号为736，相机登记使用原始局部坐标量得28.246米的北墙，另一次WGS84切平面测量得到28.272米，外向均约6.2°。两张照片的窗角用于相机估计，六根柱的位置、柱径与脚颈高度分别读取。两组背墙格窗的重复纹样最初给出两个可能纵深，屋顶第二、三道梁的独立两照交点排除了浅进深解。门罩出挑、单门退深和较远一根柱的细部仍为估计值。作品保留可见的北立面和短墙回折；照片未覆盖的南立面、完整屋顶与室内没有推建。[独立底图测量](measurements/footprint-review.json) · [相机使用的平面与朝向](measurements/north-front-footprint.json) · [相机与六柱轴线](measurements/north-portico-axes.json) · [后墙与梁底交点](measurements/coffer-cross-registration.json)

柱头两面的卷涡、梁间格板、三个半圆罩、窗玻璃与金属框、门槛和台阶都可单独编辑。浅色石面采用程序生成的1.52米重复纹理，模型没有嵌入原照像素。[卷涡轮廓](measurements/ionic-front-traces.json) · [梁底](measurements/coffered-soffit.json) · [许可与照片](SOURCES-LICENSE.md)

## 从源文件重建

从完整项目进入本目录，安装 Python、NumPy、SciPy、Shapely、Pillow、gltfpack 与 Blender。先生成程序石纹，再输出带米制 UV 的两档原始网格。

```sh
python source/paint.py
python source/build_model.py --output bank-full.glb
python source/build_model.py --lod --output bank-low.glb
python source/build_blender_source.py --check-raw bank-full.glb
```

[上部窗墙和入口](source/bank_elevation.py) · [爱奥尼柱](source/ionic_portico.py) · [格梁和灯罩](source/coffered_soffit.py) · [七个检查机位](source/cameras.json)
