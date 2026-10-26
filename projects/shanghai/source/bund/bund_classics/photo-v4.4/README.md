# 外滩17号：共形墙体、实景玻璃与屋顶纠正

此包生成字林西报大楼的近景模型、可编辑Blender文件，以及用于远景压缩的无贴图变体。照片映射保留原有三维窗洞和凹进；模型仍是照片参照重建，不是摄影测量或测绘成果。

## 本次改动

- 修正结构石墙内部的共面重叠：原1,148个闭合墙盒按7组相同立面/厚度做精确占用并集，正面、背面和窗洞侧面共用网格节点。删去仅被相邻墙体覆盖的内部侧面，保留真正窗洞、凹进和外边界；原有正面长边的T接缝变为共形节点。此项涉及前、侧、后结构墙，不只是照片或屋顶修改。数值归并的最大坐标变化约0.0000034m。

- 检查5排×5个大窗，以各窗的可见玻璃内角分别配准。24窗使用Suicasmo的原始CC0照片；最低中央窗被石刻挡住，因此保留完整原窗材质。狭窗和其他未覆盖区域未做照片映射。
- 每块玻璃使用8×12网格承载透视UV，保留原有内退位置。照片范围向已核对玻璃内部收紧4%，避开石窗台和外框。原始JPEG像素与字节不变；所有照片玻璃共用一张纹理。
- 内部等距模板框条替换为照片可辨认的细框分布。中央三联窗原先相距约1cm的两根重复竖石条合为一根，消除重叠面闪烁。
- 两座透空亭纠正为厚实体方塔：前方各四根贴壁柱、深暗开口、层叠方檐和低浅弧冠。三角山花前移并补实体鼓面；旧塔基不再遮住山花。顶层中央三处后退玻璃改为暗内景材质。原40m包围高度（包含旗杆）、地理锚点和地面轮廓保留。

塔宽、分层、凹深、曲冠高度和隐藏侧后仍是照片比例估计。补充照片只核对建筑结构，旧天线没有复制。旧模型的其他尺寸与简化雕饰没有因此变成已测量数据。

## 重建与压缩

需要Blender4.3系列及gltfpack1.3。以下在本源码包目录运行，`--project`指向完整上海项目根目录：

```sh
python rebuild_all.py --project /path/to/shanghai --output /path/to/exported/bund17-photo --gltfpack /path/to/gltfpack
```

`rebuild_all.py`先对随包旧基线`bund17-base.blend`执行`clean_wall_baseline.py`，把新基线存入输出目录，再应用照片与屋顶校正，最后压缩。旧基线SHA与新基线SHA在`SOURCE.json`分开记录。随包`bund17-clean-base.blend`是本次已核验的新基线快照，不能把它的哈希冒称旧基线哈希。

加`--render`会输出正面、斜视和窗细节预览。也可直接运行`blender --background --threads 1 --python build_photo_windows.py -- --project /path/to/shanghai --output /path/to/exported`，默认使用新基线快照；`--base-model`可指定另一份已清理基线。预览灯光、相机不属于导出的建筑GLB。不得以当前已应用照片/屋顶的最终模型作为基线，否则会重复处理。

核心输入为本包`window-controls.json`、`news-footprint.json`、`bund17-base.blend`和墙拓扑清理脚本，以及项目原图`assets/references/bund/bund17.jpg`。`SOURCE.json`记录来源与SHA256，`roof-reference.json`区分观察和推定。`compress_models.py`固定压缩参数，并在gltfpack重写asset字段后恢复作者、许可与来源；不得省略该步骤。

网页近景使用`bund17-photo-web.glb`。`bund17-photo-lod.glb`从本次相同修正几何生成，省略照片并恢复原蓝灰玻璃颜色；不能只删除白色照片材质的map。其余输出为`bund17-photo.glb`、`bund17-photo.blend`和`bund17-untextured.glb`。

## EXIF与资源

源JPEG存储尺寸5184×3456、EXIF Orientation6，正常显示尺寸3456×5184。Blender读取存储方向；本包UV按存储像素生成。材质`extras.photographicSource`记录方向、尺寸和原图SHA。网页应使用项目`src/photographic-texture.js`：仅当解码器已旋转图片时补偿UV。不得依赖Chromium的`imageOrientation:none`忽略EXIF；实际浏览器验证表明该选项仍旋转图像。

原图压缩后约6.94MB，解码RGBA全mip链约95.6MB GPU。24窗共享一个texture，远景模型不带图片。近景切换到远景时必须释放原模型的自有纹理；文件小于100MB不等于GPU内存同样小。

## 核验与许可

墙拓扑生成器逐组检查封闭边、相邻面边向、正体积、正背面积守恒；独立GLB审计中，中部正面反向共面侧面重叠由40.950051平方米变为0。所有非limestone材质的58,968个三角形位置与照片UV逐一精确保持。照片/屋顶生成器继续检查24窗内退、塔窗暗后壁、山花前置和闭合构件面序；其“原有顶点”指标仅相对清理后的新基线，不能理解为旧墙拓扑不变。压缩检查比较全部定向三角形、法线方向误差和照片UV；原图SHA在raw/web中应一致，LOD图片数量应为0。从原始冻结基线重新执行墙并集、照片/屋顶和压缩的完整迁移重建结果见`rebuild-validation.json`。这些检查验证实现，不证明现场尺寸精度。

原创几何与代码保留项目MIT许可；OSM轮廓保留ODbL1.0署名 **© OpenStreetMap contributors**。实际嵌入的Suicasmo照片为[CC0](https://commons.wikimedia.org/wiki/File:North_China_Daily_News_Building_20250501.jpg)。`references/onedesign23.jpg`由Onedesign23提供、CC BY-SA4.0；`references/2012.jpg`由Ferox Seneca提供、CC BY-SA3.0，准确链接与SHA见`roof-reference.json`。这两张补充参考未嵌入模型，仍保留各自许可，不属于代码MIT许可。
