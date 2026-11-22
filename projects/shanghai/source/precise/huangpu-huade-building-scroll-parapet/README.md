# 华德大楼四川中路立面双卷草栏板与圆饰托板

四川中路 620 号的华德大楼在上海市第五批优秀历史建筑名录中编号 5A008，登记用途为住宅。650 号公和洋行大楼在同一名录的列名也写作华德大楼。630 号为海青大楼，670 号为礼和大楼。[相邻四项原始名录](measurements/four-addresses.json) · [地块与门牌核对](measurements/footprint-review.json)

模型取自 Antigng 于 2015 年 7 月 20 日拍摄的《华德大楼》。两块石栏位于临街连续露台上，板肩展开后向上卷曲，一枚有折面的石楔压在两个小卷头之间。每块开大、小半圆孔各一个，栏板后的细横杆透过侧边镂空可见。每片挑板底部各有三行、三列浅凸圆饰，向上的观察角度可以看到它们的斜边和底面。[原始照片](https://commons.wikimedia.org/wiki/File:%E5%8D%8E%E5%BE%B7%E5%A4%A7%E6%A5%BC.jpg) · [打开模型](../../../huade-building-scroll-parapet.html)

原图旋正后为 2988 × 5312 像素，测量范围为左上角 (253, 2350) 至右下角 (1271, 2946)。用方柱和压顶边校正栏板正面，沿照片中两块挑板的侧边估计进深方向。每板以四个外角圆心确定阵列，另五个圆心独立核验。从2015年街拍方向向这四处孔洞中心投射31条射线时，交点都落在退入正面 0.002–0.076 米的侧壁上。照片中的深色包含孔内阴影，无法据此量出背板；模型按正视透空、斜看可见孔壁来处理。建模采用名义栏高 0.91 米；绝对尺寸、板材厚度、石楔与卷草突出的深度仍是估值。项目将这段构件独立展示。[照片依据](measurements/photographic-reference.json) · [圆心像素](measurements/roundel-measurements.json) · [源文件与许可](SOURCES-LICENSE.md)

原始、解码近景、解码远景各通过 92 条网格射线。四道半圆孔用 31 个独立照片列核对 62 个边点，三档的第 95 百分位误差分别为 1.792、1.792 和 1.777 个原图像素。十八枚圆饰的暗边与较亮底面分别取点，各档 36 次首交均命中圆盘或转角。[原图与解码网格的逐点结果](measurements/released-parapet-photo-review.json)

## 重新生成

在完整仓库的本目录运行下列命令，生成两档网格并读取原始网格的贴图坐标。普通四件打包使用同一入口，参数可通过 `python source/build_model.py --help` 查阅。

```sh
python source/build_model.py --output huade-full.glb
python source/build_model.py --lod --output huade-low.glb
python source/build_blender_source.py --check-raw huade-full.glb
```

[栏板与水平托板几何](source/parapet.py) · [摄影投影与尺度](source/photo_plane.py) · [七个观察视点](source/cameras.json)
