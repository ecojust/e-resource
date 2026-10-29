# 武康大楼主楼：建模源码与范围

本模型采用 post-2019 的现代修缮外观，只对应武康大楼老主楼；东北新楼、辅楼以及其他住宅未并入。它是一栋多户住宅，也是一座公开地标，不代表普通街区或全上海住宅已经完成。

采用冻结地图源的东/北/上米制坐标，GLB 输出为东/上/南；anchor 不变、rotation_y=0。八个主体楼层有正文及照片依据。出版物记录“30 米”未定义测量端点；本模型女儿墙 30.10 米、推定屋顶构筑物最高 31.37 米均为建模值，不是实测高度。层高、阳台出挑、屋面服务设施位置及不可见连接墙为推定。

两处西北凹口、三翼、圆端、后退窗廊保持真实空间。淮海街面是可见开放券廊，武康街面底层为有窗台的扇形格栅拱窗。圆端仅局部平滑，距来源外边最大约 0.334 米；内侧店面采用真实内缩多边形上的平面短片，避免深度曲面偏移折回。玻璃后退、钢窗格、石栏杆、金属栏杆、第三层窗山花、卷涡托架和百叶空调罩均为实际几何。

砖 PBR 为 agent 原创通用程序材质，CC0；不是武康大楼扫描或精确实测砖色。主立面 UV 为沿墙距离/1.984、高度/1.184；垂直返面用墙深/1.984、高度/1.184；水平端面用沿墙/1.984、墙深/1.184，避免退化切线。basecolor 为 sRGB，normal 与 ORM 为线性；normalScale=0.65，ORM 蓝为 0。没有使用私有照片像素作贴图。

复建依赖 Python 3、numpy、scipy、Shapely 2.1+，渲染需要 Blender 4.3+。保持 `source/` 与 `materials/wukang-brick-v1/` 同级，参考命令：

```sh
python source/rebuild.py --input source/geometry-input.json --out rebuilt-full
python source/rebuild.py --input source/geometry-input.json --out rebuilt-lod --lod
blender -b -t 2 --python source/render_detailed_v1.py -- --glb rebuilt-full/wukang-mansion-raw.glb --out rebuilt-previews --samples 24
```

`build_detailed_v1.py` 文件名沿用初版名称，最终来源以交付清单的 SHA256 为准。`package_assets.py` 对 web/LOD 使用 gltfpack；原始几何、原生文件不重复复制。每个输出须严格小于 100 MB。独立验收与网页导航由集成记录提供。

源码与手工几何 MIT；地图数据 © OpenStreetMap contributors / Overture，ODbL-1.0；原创材质 CC0。许可照片另按各自 register 署名。私有参考图不属于本源码交付。

最终 V5 只在东北共用边界裁去三处石饰端部，保留 2 毫米接缝，最大法向裁切约 8.095 厘米；主体及其他细节不变。`final-revision.json` 记录实际 GLB 差异核对，`trim_shared_end.py` 执行这项封闭裁切。四张 V4 全楼/圆端/屋面预览保留 V4 来源标识；两张 V5 东北接缝近照是从最终原生文件重新渲染，不将旧图冒充最终版本。
