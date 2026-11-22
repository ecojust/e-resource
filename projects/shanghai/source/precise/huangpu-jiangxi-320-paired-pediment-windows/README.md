# 道达大楼江西中路立面双三角窗楣与托座

上海市第五批优秀历史建筑名录第 5A004 项的原名是道达大楼，列名珠江大楼，地址江西中路 320 号。本模型选取临街正立面照片右侧并列的两扇竖窗。每扇窗的两道斜檐相交成尖角，檐脚转成水平石线。三角形下方可以辨认一块向前突出的宽楔和两侧的凹框。[市表记录](measurements/register-row.json) · [打开模型](../../../jiangxi-320-paired-pediment-windows.html)

Antigng 于 2015 年 7 月 20 日拍摄的原图还能辨认尘蓝和赭黄相间的遮阳布。左窗布面较平，右窗布前沿向内聚拢，四片垂布的宽度、色带间隔和末端各不相同。电线和立管遮住了局部檐脚，布篷也遮住部分窗顶。模型中的窗洞深度、墙厚和会聚面尺度为估算。[署名原照](https://commons.wikimedia.org/wiki/File:%E9%81%93%E8%BE%BE%E5%A4%A7%E6%A5%BC.jpg) · [四片布带](measurements/curtain-band-heights.json)

测量使用旋正后的 2988 × 5312 像素原图。窗楣的轮廓以独立估读的角点和未用于建模的边缘采样复核。三个档位均通过84束几何首交。四片垂布各留两条独立采样线，共60个高对比点。原始、近景各有58点与原照片的蓝赭色别相符，远景59点相符，差异集中在折痕边缘。[色带复核](measurements/final-curtain-colour-review.json)。原城建筑 278 的轮廓与具名地址相合，本期两扇窗的准确定位尚待现场测绘，模型独立展示。[照片和坐标](measurements/photographic-reference.json) · [窗楣边缘](measurements/observed-raking-edges.json) · [地块复核](measurements/footprint-review.json) · [来源及许可](SOURCES-LICENSE.md)

普通网页复核使用实际 WebGL 绘制。四片垂布在窗楣两侧前后翻折，蓝、赭、深灰三种薄布材质均能从两面观察，凸石斜檐朝街的一面沿外轮廓连续。

## 重新生成

安装项目使用的 Python 依赖后，从本目录运行以下命令可生成完整网格和简化网格，再检查原生适配器能否读回原始网格的纹理。

```sh
python source/build_model.py --output full-source.glb
python source/build_model.py --lod --output low-source.glb
python source/build_blender_source.py --check-raw full-source.glb
```

常规四件打包通过项目通用入口和本栋的 Blender 适配器运行，可在 `python source/build_model.py --help` 查看参数。相机位置在 [cameras.json](source/cameras.json)，两种窗楣与布篷结构在 [window_details.py](source/window_details.py)。
