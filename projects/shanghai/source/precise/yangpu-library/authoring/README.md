# 杨浦区图书馆整馆模型

2018 年修缮扩建后整馆外观，包括历史 I 形馆体、四角现代翼部、两个真实露天内院和南端现代入口。坐标单位米，源模型 x 东/y 北/z 上；GLB x 东/y 上/z 南；锚点 WGS84 `[121.51878770435401,31.310840957391402]`，旋转 0。

主门按公开照片细化了双层歇山琉璃瓦屋顶、连续瓦垄、脊端轮廓、两道斗拱和彩画带、上层三拱窗、下层三高窗、两八角窗、双扇格栅门、石栏和灯座。两个旧长翼的东端采用单高窗、底部拱门和小石阳台。现代部分有窄竖窗、内向横框玻璃、屋面条带绿化及南入口的真实宽门窗洞。门窗不是贴在完整墙上的色块，墙体实际扣除对应洞口。

这是照片和地图约束的可编辑外观模型，非测绘复原。18.49m 是规划图檐口值，将其解释为上层檐口属于建模假设；实际模型最高顶饰约22.481m，公告高度登记采用22.51m包络。墙线随底图拟合，局部尺寸、背面/内院窗数、彩画纹样与小脊兽轮廓仍为推估。现代规划图10.8m与H11.05基准差异未解决。门框包边最低约−0.02m，为名义地面0以下的2cm收口；不会将整楼降低。室内孔雀门、室内陈设、不可见设备不在本次范围，外部拱门只称入口格栅。

原始与网页版同为365,524三角形；作者控制的LOD为122,688三角形，移除细石缝/竖槽并减少瓦垄与弧面采样，保留主要体量与真实门窗。LOD不是原模型三角面的严格子集。网页版采用现有 gltfpack 1.3.0 的 Meshopt 压缩，保留浮点坐标，不进行全局减面。独立实际解码验证和浏览器验收由场景集成记录另行提供，不以此说明冒充通过。

## 重建

环境：Python 3、NumPy、Shapely 2.1+（需要 constrained_delaunay_triangles），Blender 4.3；可选 gltfpack 1.3.0。工作目录必须新建，避免覆盖发布文件。

```bash
python build_model.py --out /tmp/yangpu-work/full-v6
python build_model.py --lod --out /tmp/yangpu-work/lod-v6
python package_assets.py --root /tmp/yangpu-work --gltfpack /path/to/gltfpack
blender -b -t 2 --python render_previews.py -- --glb /tmp/yangpu-work/package-v6/yangpu-library-raw.glb --out /tmp/yangpu-work/native-v6 --samples 16
```

`calibration.json` 给出锚点、地图足迹及两内院、比例假设与未解决事项。`build_model.py` 和 `common/photo_architecture.py` 生成几何；`package_assets.py` 压缩并保留来源元数据；`render_previews.py` 从最终 RAW 导入 Blender，保留三台预览相机并另存可编辑压缩 `.blend`。预览地面/太阳/相机在单独集合，不属于导出的建筑 GLB。渲染并非照片标定，不能用渲染图证明实测精度。

代码及原创几何 MIT，地图 ODbL，参考照片各自保留许可，见 ATTRIBUTION.md。无图片贴图，无字体依赖，无政府图片像素。
