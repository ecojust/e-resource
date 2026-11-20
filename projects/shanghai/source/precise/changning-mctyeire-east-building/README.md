# 中西女中东楼（五一楼）院落立面

上海市房屋管理局第二批优秀历史建筑表将中西女中列为2M008，地址为江苏路155号东楼、北楼。大草坪东侧的五一楼过去称社交堂（Social Hall）。学校于1917年迁址，校舍条目记东楼建于1922年，现行地图则给该栋标注1917年。建筑本身的竣工年份有待原始档案确认。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [校史采访](https://www.thepaper.cn/newsDetail_forward_1494412) · [来源逐项记录](reference-review.json)

Ctny于2017年拍摄了五一楼的庭院正面与全景。两张照片均显示院面中央有一座浅色山墙，拱形正门上方为菱形带饰，两侧底层为铅条菱窗。左右各六孔拱廊，上有两排双窗及四扇老虎窗。模型以这组影像重建约70.7米的院面。端部伸向草坪的两排侧翼、后排房间和独立的五四楼保持原城市几何。[庭院照片](https://commons.wikimedia.org/wiki/File:Shanghai_No._3_Girls%27_High_School,_Five-One_lecture_hall.jpg) · [庭院全景](https://commons.wikimedia.org/wiki/File:Shanghai_No._3_Girls%27_High_School,_Five-One_lecture_hall_panorama.jpg) · [轮廓与航片](footprint-review.json)

局部X轴沿正面朝东南，Y轴朝楼内东北方向，Z轴向上。地块确定了约20.3米宽的中央突出段、两端接缝及其方向。檐高、门廊深度、瓦面、窗棂和石料颜色根据照片估计。两层窗框、铅条、拱券后壁、短侧墙、老虎窗与山墙盖石均为独立几何，外部照片只作对照。

在上海项目目录中使用Python、NumPy、Shapely 2.1、Blender、gltfpack、ImageMagick与OIDN生成三种GLB、可编辑工程和原生样图。

```sh
python source/precise/changning-mctyeire-east-building/source/build_model.py \
  --out assets/models/candidates/changning-mctyeire-east-building \
  --audit data/audit/mctyeire-east-building-v1 \
  --decoded /tmp/mctyeire-decoded --blender blender \
  --gltfpack gltfpack --oidn oidnDenoise
python data/audit/mctyeire-east-building-v1/check-court.py \
  --project . --decoded /tmp/mctyeire-decoded \
  --manifest assets/models/candidates/changning-mctyeire-east-building/manifest.json \
  --out data/audit/mctyeire-east-building-v1/court-checks.json
```

[打开独立模型](../../../mctyeire-east-building.html) · [Blender工程](../../../assets/models/candidates/changning-mctyeire-east-building/changning-mctyeire-east-building.blend) · [原始GLB](../../../assets/models/candidates/changning-mctyeire-east-building/changning-mctyeire-east-building-raw.glb) · [网页近景](../../../assets/models/candidates/changning-mctyeire-east-building/changning-mctyeire-east-building-web.glb) · [网页远景](../../../assets/models/candidates/changning-mctyeire-east-building/changning-mctyeire-east-building-lod.glb)
