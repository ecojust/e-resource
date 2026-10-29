# 上海16区地面与水系：平面模型第一批

[打开模型查看页](../../surfaces.html) · [逐区资产与校验值](../../assets/surfaces/manifest.json) · [几何验收](../../data/audit/surfaces-v1/geometry.json) · [Blender重新打开记录](../../data/audit/surfaces-v1/native.json) · [网页验收](../../data/audit/surfaces-v1/browser.json)

新增16套可编辑的地面／水面模型，每套包括GLB、Blender和GIS分区边界。查看页可选择各区或合并显示16区，分别开关非水域底面和地图水面，并下载对应模型。下载后用本地HTTP服务器打开网页，无需在线地图服务。

这是对地面及江河建模的推进，不计入建筑逐栋照片复原数量。既有38处建筑目录保持；1,796,419个建筑及部件要素仍未全部逐栋复原。新资产在独立查看页展示，尚未替换建筑漫游中的地面、在线水面或碰撞代理。

## 已有依据与范围

- 行政范围沿用 `data/districts.geojson` 的16区WGS84边界，含海域、岛屿及外地飞地；没有把包围盒当作陆地边界。边界SHA256绑定在清单内。
- 水面来自OpenFreeMap / OpenMapTiles的 `20261025_080012_pt` 固定版本、z14 `water` 多边形层。4,062个与行政范围相交的瓦片全部取得，缺失任何瓦片即停止构建。
- 下载响应的URL、大小、SHA256和实际取得时间保存在 [sources.json](sources.json)。共有10,728条裁切前水面要素，包含同一河流跨瓦片的重复表示，**不能称为10,728条独立江河**。
- [water-tiles.zip](water-tiles.zip) 保存各原始响应中复制出的water protobuf层，移除了其他图层；不是原始完整PBF下载包。每个冻结成员另有大小及SHA256。模型重建只使用该冻结包，不需重新联网取图。
- 记录源水面多边形和孔洞，不根据水道中心线推定宽度，不生成未知河床、堤岸、铺装、台阶或建筑。水系中未收录的细小河渠、暗渠和地图年代之后的变化尚未复原。
- 非水域底面是“行政范围减去已收录水面”的几何补集；缺失水体可能仍落在底面中。它不是经实测确认的全市陆地分类。

## 高程、精度与几何

两种薄面都位于展示零平面，**没有DEM、测量水位或河床深度依据，不是三维地形实测成果**。颜色仅用于识别水陆，不是现场采样PBR材质；没有植被、道路铺装、潮汐及流水模拟。

先裁掉MVT缓冲区，再合并水面，行政区裁切后生成底面补集。内部瓦片切线不会被当作新增堤岸。源水面内环、江心岛、离散池塘均进入拓扑处理。投影为Web Mercator，以各区原点纬度余弦缩放成局部米：GLB为X东、Y上、Z南。查看页合并16区时转换到共同原点，不能把不同区的原点直接叠在一起。

投影拓扑先按1毫米网格归并，局部网格再按二进制可精确表示的1/32米（3.125厘米）归并，随后进行保留内环约束的Delaunay三角化。这样避免单精度导出把长而接近共线的边翻转。它是数值处理精度，不代表地图有厘米级真实准确度。z14原始水面顶点本身约有半米量级网格，且存在地图绘制误差。所有数值归并都应通过导出后的几何比较；少量退化薄片处理记录在GLB网格metadata中。

导出核验逐个检查全部三角形。源GIS分区与导出网格之间存在数值归并差异，检查采用“差异面积预算＋差异区域经半径4厘米向内缓冲后无显著残留”，**不是每个边界点位移小于4厘米的证明**。被归并的长而极窄碎片尖端可能有较大点位距离。16区水陆网格合计仍有约4.55平方米极窄数值重叠，单区最大约4.14平方米；逐区实值保留在验收JSON中，不宣称严格零重叠或测绘级无缝网格。

所有GLB薄面明确双面显示，正面朝上。每个交付文件严格小于100 MB。各区原始水陆GIS分区以 `*.geojson.gz` 提供，可以解压编辑；用于对照网格，不能当作实测数据。源及派生数据采用ODbL-1.0，原创代码采用仓库MIT许可；Three.js和OrbitControls使用随附MIT许可。

## 重建与验证

从 `projects/shanghai` 目录运行；参考环境Python 3.12、Blender 4.3.2，Python依赖版本见 [requirements.txt](requirements.txt)。没有捆绑第三方二进制依赖。

```sh
python -m pip install -r source/surfaces/requirements.txt
python source/surfaces/build.py
blender --background --python source/surfaces/save_native.py
python source/surfaces/verify.py
python tests/surface-mesh.test.py
python -m http.server 8000 --bind 127.0.0.1
# 另一个终端，需安装Playwright并提供Chromium：
node tools/qa/surfaces-browser.cjs
```

重建GLB和GIS分区是确定性的；Blender原生文件可能因保存时间等内部信息不同而产生不同字节。`save_native.py` 实际重新打开每个保存的文件，核对网格与三角数量，并更新清单哈希。

仅在需要重新取得同版地图输入时运行 `python source/surfaces/fetch_water.py`。该脚本保留已冻结的tilejson版本并支持逐瓦片缓存续传；远程旧版本未来可能不再可用，但不会影响从仓库冻结包重建。

## 尚未完成

下一步需要具有来源许可和垂直基准的高程、河岸、铺装及桥梁衔接资料，并将经过验证的地面与水域碰撞接入建筑漫游。建筑逐栋补全仍必须遵守[逐栋细化标准](../../data/audit/precise-buildings-v6/DETAIL_STANDARD.md)，不能由这批地面模型替代照片与尺度证据。
