# 中国通商银行旧址临江二层窗柱

中山东一路6号，上海市第二批优秀历史建筑2A003。两张在不同日期拍摄的正面照片都能辨认出，东立面中央三樘二层窗左右各有一根细石柱，柱身呈圆弧，顶部有小型浮雕与分层方形压顶。V6已经制作首层三拱廊、三层中央四窗及窗间细柱。逐面检查其二层原始网格时，三窗六侧仅有进出墙面0.085米、0.115米的平券套。[照片及登记原件](reference-review.json) · [原模型384条断面射线](../../../../../data/audit/tongshang-east-window-columns-v1/previous-jamb-profiles.json) · [照片与原模型比照](../../../../../data/audit/tongshang-east-window-columns-v1/photos-and-v6.jpg)

六件新增构件沿既有三樘窗的边缘布置。柱身直径约0.15至0.16米，柱头宽约0.31米。半径、凸度、被阳台挡住的柱脚及柱头浮雕均据比例近似。2014年照片可见实体阳台矮墙与压顶，2025年照片还可见其后的透明玻璃挡板，两次拍摄之间的安装时间未知。当前模型的阳台沿用V6实体矮墙和压顶。圆柱、窗框和石墙用实体几何表现。V6的127片取样窗玻璃继续使用Suicasmo的2025年原图。[2014年照片](https://commons.wikimedia.org/wiki/File:China_Merchants_Bank_Building,_Shanghai.JPG) · [2025年照片](https://commons.wikimedia.org/wiki/File:China_Merchants_Bank_Building,_Shanghai_20250501.jpg)

三档GLB继续以既有场景的本地坐标和地图锚点定位，每一根新增贴柱使用独立命名网格。Blender原始主体、场景相机、材质、打包照片和灯具保留，六根新柱各可单独编辑。四件文件的相对路径、字节数、SHA-256及GLB面数见[修订清单](manifest.json)。修订前的可编辑源码和模型由原始版本保存。[既有V6源码](../../../../bund/photo-rebuild-v6/bund06/README.md) · [四件原资产的固定版本与散列](baseline.json)

## 重新构建

从本目录执行下列命令。几何步骤需要Python 3和NumPy，原生文件使用Blender 4.3.2。基础输入使用固定提交的四份公开文件，下载后逐个检查Git对象和SHA-256。

```sh
python fetch_baseline.py /tmp/bund06-base
python build_window_shafts.py /tmp/bund06-base /tmp/bund06-new
blender -b -t 1 --python-exit-code 5 -P native_shafts.py -- /tmp/bund06-base/native.blend /tmp/bund06-new/native.blend /tmp/bund06-new/native-reopen.json
```

三档GLB的每个旧二进制区原字节保留。网页及远景的旧MeshOptimizer压缩区继续使用同一份二进制。新构件按GLB标准追加，包含普通浮点位置与法线及16位索引。远景降低柱身环段和柱头浮雕的分段数。项目自带的外滩LOD检查器可以直接核对三种资产及其原有边界。[逐档解码与射线](../../../../../data/audit/tongshang-east-window-columns-v1/geometry-comparison.json) · [Blender重开](../../../../../data/audit/tongshang-east-window-columns-v1/native-reopen.json)

原创代码和新增几何采用MIT。地图足迹来自OpenStreetMap贡献者，采用ODbL 1.0。2014比照图依CC BY-SA 3.0署名，2025年色彩取样原图依CC0 1.0发布。[比照图署名与许可](../../../../../data/audit/tongshang-east-window-columns-v1/image-credits.md)
