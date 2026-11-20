# 董家渡天主堂南入口

董家渡路北侧的圣方济各沙勿略堂于1847年奠基、1853年开堂，曾为上海教区主教座堂。第一批优秀历史建筑表以1A027（1E001）列董家渡路175号，项目工作表与具名地图建筑记作185号。此模型取2010至2012年照片可辨的南入口。2017年工程方记载地基出现下沉和开裂，准备主动托换。2018年工地照中仍可见中央山花和双塔，首层被围挡遮住。2019年报道讲述主体顶升方案与评估完成、附楼拟拆移；本项目尚未核实此后竣工日期、开放状态及立面配色。[历史、工程资料与各照片的日期及许可](reference-review.json)

两侧低门和窗、中央木门与曲线扇窗、人物壁龛、双钟塔百叶、凹曲塔帽、卷涡、赭红钟面底板、铁格十字架与中文竖匾以原创几何制作。照片中可读的左右十一字楹联用许可字形重新排布。门高、龛内衣褶、钟面中央色块及各檐线进深由外观估计。模型宽约30.62米；南侧外墙向北延伸3.2米收口。大厅其余各面、内坛、学校、附楼与院地另列。[具名城市建筑、南边定位和航片](footprint-review.json) · [独立查看器](../../../dongjiadu-cathedral.html)

[网页近景 GLB](../../../assets/models/candidates/huangpu-dongjiadu-cathedral/huangpu-dongjiadu-cathedral-web.glb) · [网页远景 GLB](../../../assets/models/candidates/huangpu-dongjiadu-cathedral/huangpu-dongjiadu-cathedral-lod.glb) · [原始 GLB](../../../assets/models/candidates/huangpu-dongjiadu-cathedral/huangpu-dongjiadu-cathedral-raw.glb) · [Blender 原生](../../../assets/models/candidates/huangpu-dongjiadu-cathedral/huangpu-dongjiadu-cathedral.blend) · [资产清单](../../../assets/models/candidates/huangpu-dongjiadu-cathedral/manifest.json)

## 重建

在 `projects/shanghai` 下运行。需要 Python 3、NumPy、Shapely 2.1、FontTools、Node.js、gltfpack、Blender 4.3、ImageMagick 与 Open Image Denoise。局部 X 朝向照片右手的东，Y 朝堂内北，Z 向上；导出的 GLB 使用标准 Y 向上。原生工程重新打开后在 Cycles 中实际渲染。

```sh
python source/precise/huangpu-dongjiadu-cathedral/source/build_model.py \
  --out /tmp/dongjiadu-assets --audit /tmp/dongjiadu-audit \
  --decoded /tmp/dongjiadu-decoded --gltfpack gltfpack --oidn oidnDenoise
python data/audit/dongjiadu-cathedral-v1/check-surfaces.py \
  --manifest /tmp/dongjiadu-assets/manifest.json --out /tmp/dongjiadu-audit/surface-probes.json
python data/audit/dongjiadu-cathedral-v1/verify-placement.py \
  --manifest /tmp/dongjiadu-assets/manifest.json --work /tmp/dongjiadu-sources \
  --output /tmp/dongjiadu-audit
```

配准脚本从固定 Git 版本获取清单中的四个城市文件，也可预先将对应文件按原文件名放入工作目录。它解码近、远城市三角面，核验保留主堂与东侧邻楼，测量剖口及行走碰撞。[配准记录](../../../data/audit/dongjiadu-cathedral-v1/README.md)
