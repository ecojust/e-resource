# 新老永安跨浙江中路北侧封闭天桥

北桥横跨浙江中路，连接南京东路 635 号老永安公司与 627 号新永安公司。2025 年 5 月 1 日从南京东路拍摄的照片能辨认两排窗带，每排六跨。模型保留窗间砖面、竖向分隔、深色双扇窗框、薄挑檐与悬空桥底。2011 年和 2024 年的街景提供另两个观察角度。[2025 年正面照片](https://commons.wikimedia.org/wiki/File:Wing_On_Department_Store_(Shanghai)_20250501-3.jpg) · [逐项资料、作者与许可](source-register.json)

两栋商场已有各自的模型。按两侧既有模型外墙确定北桥约 11.30 米的接合长度，桥深约 4.20 米，桥底标高估计为 13 米。面向南京东路的砖墙、开间及窗框有照片依据。重复的背向窗墙、屋面、桥底及入墙构造含作者估计。较南的另一座封闭桥、商场内部和桥梁实际通行条件仍需调查。[新永安大楼固定修订](https://zh.wikipedia.org/w/index.php?title=%E6%96%B0%E6%B0%B8%E5%AE%89%E5%A4%A7%E6%A5%BC&oldid=93563312) · [尺度、朝向与位置参数](source/dimensions.json)

## 模型与重建

原始模型与 Blender 源文件保留分跨的细部。近景表面的错缝砖、窗扇、压条和窗台采用原创网格，远景使用低面数砖色墙面。两种版本均保留两排六跨内凹窗及桥下净空。四份资产、哈希和当前范围见[资产清单](../../../assets/models/candidates/huangpu-wing-on-skybridges/manifest.json)。

从本目录运行以下命令。打包需要 Python 3、Blender 4.3 和 gltfpack 0.25。几何复核使用 NumPy。

```sh
python source/package.py --assets ../../../assets/models/candidates/huangpu-wing-on-skybridges --audit ../../../data/audit/wing-on-skybridges-v1
python source/check_bridge.py --assets ../../../assets/models/candidates/huangpu-wing-on-skybridges --report ../../../data/audit/wing-on-skybridges-v1/geometry.json
```

代码与模型使用仓库 MIT 许可。照片用于研究，未作为纹理分发。地图及相邻模型定位中的 OpenStreetMap 来源保留 ODbL 1.0 署名。[模型预览](../../../wing-on-north-skybridge.html)
