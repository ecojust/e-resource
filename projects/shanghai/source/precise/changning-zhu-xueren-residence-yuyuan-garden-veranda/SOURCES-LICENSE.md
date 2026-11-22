# 朱学仁住宅南园廊与东入口

上海市房屋管理局第五批优秀历史建筑名录将愚园路684号登记为“朱学仁住宅／中共长宁区委党校／长宁区人民法院”，编号5M002。早期公示的编号为CN-J-002-V。原登记中的使用单位、旧机构和宅名分别保留。2018年人民法院报的口述回顾将长宁法院1984年10月设立少年法庭的地点记在684号。现有资料把建造年代约定在1920年前后，尚无竣工日或实测施工图。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [少年审判史回顾](https://www.thepaper.cn/newsDetail_forward_2555963) · [登记交叉核对与影像来源](measurements/registered-address-and-dated-views.json)

## 照片与几何

高参88的组照发表于2014年5月18日。第5、8、10等张的相机原文件将实拍时间记在2013年9月26日。西南、正南和东南方向给出三开间园廊、中间凸出的廊口、券顶、宝瓶栏杆和两侧花池。第8张正面可逐级读出五道弧形石阶，以及后墙两樘带上亮的双扇门。第11张从廊端望到相对端。相机标定、像素、外推误差和五级踏步的曲线均保留在测量文件中。[高参88原文](https://blog.sina.com.cn/s/blog_5d1bdf480101im2h.html) · [两向标定](measurements/south-garden-two-view-registration.json) · [第三相机与廊深](measurements/south-veranda-depth-and-third-camera.json) · [五道踏步读数](measurements/south-garden-five-curved-steps.json)

东入口依2013年宽景、入口近照、南廊东斜照及Antigng于2018年2月13日拍摄的照片。Commons原件有方向标记，转为直立后可见赭红双柱、矩形雨篷、正门和门北侧的两层弧墙。门两侧的平直折墙和弧墙随照片分段制作。东小窗只据可见的灰色坡座连接到主屋。向北树冠遮挡处保留一小段内退的封合剖面，标出制作范围。西墙及北墙的背面简化，上层受柱或树木遮挡的门洞按现有视线估计。[Antigng照片与授权](https://commons.wikimedia.org/wiki/File:愚园路684号.jpg) · [东入口多视图](measurements/east-porch-five-view-world.json) · [东墙折线与开口](measurements/east-entrance-surface-and-openings.json)

## 屋面定位

四期Esri World Imagery下的红瓦主檐约18.3–19.1米，瓦面主体进深约10.5米。东部红瓦短回折、东门口雨篷、旁边独立浅色屋面和更北的成排屋面可分别辨认。底图建筑轮廓1389用于找址，正射图上的檐线用于定屋盖比例。最终几何使用局部米制坐标，X从西向东，Y自南园廊指向屋后，Z向上。[四期描线](measurements/four-edition-original-roof-traces.json) · [屋面与相邻建筑判读](measurements/historic-roof-proportions.json) · [定位依据](measurements/placement-identity.json)

2021年7月发布的影像在此点的采集日期为2019年11月9日，2024年6月版采于2021年11月25日，当前影像采于2025年4月7日。2016年7月版的19级图块在建筑点缺少采集属性，17级图层返回2010年7月22日。各版的查询图层、日期、图块及像素核实结果可复读。[Esri发行和采集日期](measurements/imagery-acquisition-and-epochs.json) · [Wayback](https://livingatlas.arcgis.com/wayback/)

## 授权与重建

原创网格、代码和程序生成的两张纹理按MIT许可。红色平瓦按搭接和错缝生成，水磨石用浅红、灰白及暗色骨料生成。模型文件未嵌入参考照片、Esri瓦片或第三方建筑模型。高参88和报道照片保留其原有权利，Antigng的原照片采用CC BY-SA 4.0，Esri影像保留其供应方署名。[纹理生成和SHA-256](source/material-sources.json) · [MIT许可](../../../../../LICENSE)

在配有项目依赖的环境，运行下列命令重建未压缩近景和远景模型。四件套打包入口接受 `--out`、`--audit`、`--decoded` 和 `--blender`，相机定义与原生文件沿用同一份测量来源。

```sh
mkdir -p output
python source/build_model.py --output output/zhu-residence-raw.glb
python source/build_model.py --output output/zhu-residence-lod-source.glb --lod
```
