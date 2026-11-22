# 外滩5号西墙南端外梯

市房管局第三批优秀历史建筑名录以3A003登记日清大楼，地址为中山东一路5号，曾用名锦都大楼。原模型已经制作临江山花、窗组、门柱、题字与广东路沿街立面。本次沿用地图中的 `bund05`，复原从广东路西端转入西墙时可见的室外楼梯。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/bc5957926d80432b8bea0157eb16bb94.html) · [旧模型制作记录](../../../../bund/photo-rebuild-v6/bund05/README.md)

2015年5月公开的组照中，近照可辨上行梯段、平台、连续金属扶手、两扇街窗的弧形气窗及其下的矩形窗扇。从广东路向东拍摄的一幅远照把梯脚定位到大楼西端。2020年2月和2021年1月的街景露出浅色踏步，两期还可辨外侧铁栏和梯旁小道。2015年近照里曾有绿色覆面。模型采用后期可见的浅色阶面。来源照片保留在原出版方，目录内收录图片地址、地点、实际字节数及校验值。[2015年外观组照](http://www.shsyzxzx.sh.cn/article/articlecontent.aspx?q_ChannelId=104101&Id=8053) · [照片与街景取证](reference-review.json)

以原轮廓西南端为楼梯的定位基准。模型沿西墙向北上行，采用14级踏步、约1.67米的梯宽与约2.17米的高差，这些尺度据照片估计。梯段与平台各有可选取的实体，水平窗槛、弧形气窗中央框、栏杆的竖条与卷草均有厚度。梯侧入口暗部与室内走向仍待核实。西侧屋顶加层年代有不同记载，此次只记录两期航片及出处。[几何源码](west_return.py) · [实测开窗与踏步](../../../../../data/audit/nissin-west-stair-v1/geometry-comparison.json)

西墙施工范围之外的旧构件由原始建筑生成程序继续创建。临江正面中央三至五层的六组窗使用原来112片逐片校准的玻璃。CC0原始JPEG由Suicasmo于2025年5月1日拍摄，玻璃片的位置、朝向和纹理坐标按原数据逐片核对。新的2015年与2020至2021年资料仅用于几何判读。[原照片和许可](https://commons.wikimedia.org/wiki/File:Nissin_Building_20250501.jpg) · [玻璃解码比较](../../../../../data/audit/nissin-west-stair-v1/registered-glass.json)

## 重建

从仓库的 `projects/shanghai` 目录运行下列命令。完整检出包含 `source/bund/photo-rebuild-v6/bund05` 的原始校准和同级 `common` 工具。若稀疏检出只包含此前已发布的网页GLB，可用第一条命令提取相同的原版JPEG。构造采用Python、NumPy、Shapely和原生成器的字体依赖，压缩沿用gltfpack 1.3，原生文件由Blender生成并重新打开。[原有输入的校验值](baseline.json) · [压缩器发行包](gltfpack-distribution.json)

```sh
revision_dir=source/precise/bund05/revisions/west-service-stair
python "$revision_dir/recover_glazing.py" assets/models/bund/web/bund05.glb
python "$revision_dir/build_model.py" --output work/bund05-stair
python "$revision_dir/pack_models.py" work/bund05-stair/bund05.glb work/bund05-stair
blender -b --threads 1 --python-exit-code 1 --python "$revision_dir/build_native.py" -- \
  work/bund05-stair/bund05.glb source/bund/photo-rebuild-v6/bund05/geometry-input.json \
  work/bund05-stair/bund05-west-service-stair-native.blend \
  work/bund05-stair/west-stair.png work/bund05-stair/native-reopen.json
```

原脚本先按SHA-256核验，再在临时目录应用四处定点修改。远档继续采用原有的无照片有色玻璃材质。登记器核实四个文件后更新原目的地及其元数据镜像，可重复执行。[生成程序的实际改动](west-stair.patch) · [四件成品](manifest.json) · [登记程序](register_revision.py)
