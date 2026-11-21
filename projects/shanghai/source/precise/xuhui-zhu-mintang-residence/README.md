# 朱敏堂住宅乌鲁木齐南路151号街门与双石狮

从乌鲁木齐南路可见绿色151号门牌、两尊坐在方座上的石狮和闭合的双扇门。2011年9月26日的照片显示柱顶灯具。2019年5月的正面街景清楚拍到球形柱帽、四格门板和左柱旁的铭牌。模型取2019年形态，按现场照片概括狮鬃和门板浅浮雕，铭牌保留外形与固定钉。[2011年原照，Morgenmauer，CC BY-SA 3.0](https://commons.wikimedia.org/wiki/File:%C3%9Cr%C3%BCmqi_Lu_nr._151.jpg) · [街景日期、位置与各原图的校验值](street-registration.json)

上海市房屋管理局第二批优秀历史建筑表以2D039登记“朱敏堂住宅”，地址为乌鲁木齐南路151号。《上海住宅建设志》记1927年建三幢，主楼和附楼在北，313平方米出租楼在南，1995年依原造型翻建。《上海名建筑志》同记1927年，将现存住宅称为南部主楼，称1995年按原样大修。杨浦区图书馆转载的《上海老房子》记1948年建，正文称20世纪90年代中期拆除重建，仅门廊柱式等构件为原物。[市房管局第二批登记](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [三种资料的原文与来源](reference-review.json)

两根街门柱中心相距约3.80米，按多个公共道路机位的方位与门柱像点估算。2020、2021年街照还能辨认院中白色横向壁板、烟道与山墙阁窗，但两期位置估计相差数米。原底图4287邻楼和指向151乙的3702楼体分别保留。院内房屋、历史南门廊、原三宅的分期及庭院边界均另列研究。[道路交会与屋顶照片对照](street-registration.json) · [城市近、远景来源](footprint-review.json)

## 模型与重建

比例、材质、刻饰和凹凸结构由作者重建。原生场景可分别编辑两扇门、门垛、门牌、石座、狮身与鬃饰。模型使用原创的几何数字表示151门牌。复现需要 Python、Node、Blender、gltfpack、ImageMagick 与 Open Image Denoise。[构件源文件](source/street_gate.py)

在 `projects/shanghai` 下运行以下命令。独立校验会再次读取三份交付网格并在道路、石狮和门板各处投射射线。

```sh
python source/precise/xuhui-zhu-mintang-residence/source/build_model.py \
  --out assets/models/candidates/xuhui-zhu-mintang-residence \
  --audit data/audit/zhu-mintang-residence-v1 --decoded /tmp/zhu-mintang-decoded \
  --blender blender --gltfpack gltfpack --oidn oidnDenoise
python data/audit/zhu-mintang-residence-v1/check-gate.py --project . \
  --manifest assets/models/candidates/xuhui-zhu-mintang-residence/manifest.json \
  --decoded /tmp/zhu-mintang-decoded --out /tmp/zhu-mintang-shapes.json
python data/audit/zhu-mintang-residence-v1/verify-placement.py \
  --work /tmp/zhu-mintang-placement --out /tmp/zhu-mintang-placement
```

[单体查看](../../../zhu-mintang-residence.html) · [可编辑 Blender](../../../assets/models/candidates/xuhui-zhu-mintang-residence/xuhui-zhu-mintang-residence.blend) · [原始 GLB](../../../assets/models/candidates/xuhui-zhu-mintang-residence/xuhui-zhu-mintang-residence-raw.glb) · [网页近景](../../../assets/models/candidates/xuhui-zhu-mintang-residence/xuhui-zhu-mintang-residence-web.glb) · [网页远景](../../../assets/models/candidates/xuhui-zhu-mintang-residence/xuhui-zhu-mintang-residence-lod.glb)
