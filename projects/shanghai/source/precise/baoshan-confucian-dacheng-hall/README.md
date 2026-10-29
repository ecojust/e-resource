# 宝山孔庙大成殿

单栋现代外观模型。主厅三组真实透空格扇、三段后白墙、环廊、0.48m栏凳、灰瓦重檐歇山屋面、御路石与前月台。2014旧纪念馆横匾不属于本次现代状态。

`geometry-input.json`是不可改动的底图owner冻结；`calibration.json`区分政府结构描述、二手13m高度与照片推估。不是测绘成果。`photo-observation-register.json`仅记录实际看过的来源与hash，不含私有照片像素；不使用贴图。

复现：Python3 + numpy + shapely>=2.1 + fontTools；`python build_model.py --out NEW_FULL`，另以`--lod`生成独立LOD。`blender -b -t 2 --python render_previews.py -- --glb FULL/baoshan-confucian-dacheng-hall.glb --out NEW_NATIVE --samples 32`生成可编辑Blender及实际Cycles渲染。`package_assets.py --raw ... --lod-source ... --native ... --out NEW_PACKAGE --gltfpack PATH`生成无位置量化Meshopt资产。输出目录必须是新路径。

原始模型、web、LOD、Blender每文件均必须小于100 MB。Blender内预览地面/灯光/相机在单独集合，不属于运行时模型。

几何与代码MIT；底图 © OpenStreetMap contributors / Overture，ODbL1.0；三字匾额使用Noto Serif CJK Bold的SIL OFL1.1字形子集。照片只提供事实/形态参考，其权利仍属于原作者。
