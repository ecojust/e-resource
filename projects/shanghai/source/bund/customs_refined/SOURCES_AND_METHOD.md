# 上海海关前楼 v3：厚墙、真实凹窗及源轮廓角亭

本版本是根据公开尺寸、OSM 轮廓和历史照片制作的可编辑建筑模型，**不是实测扫描或摄影测量成果**。几何没有嵌入参考照片、外部字体或纹理。钟盘细线、窗框、凹窗、门扇及装饰均为实体或网格几何。

## 文件与重建

- `customs-house-v3.glb`：米制，X 向东、Y 向上、Z 向南；地理朝向已经烘焙，不要再额外旋转。
- `customs-house-v3.blend`：可编辑网格、材质、相机与渲染照明。仅 GLB 导出的建筑对象是产品资产；场景中的预览地面、相机、灯光不在 GLB 中。
- `customs_house_v3.py` 和 `facade_geometry.py`：生成脚本，后者包含真正开孔的厚墙、内退窗扇及四个源多边形角亭。
- `customs-house-v3.json`：尺度、锚点、朝向、统计、校验和与限制。
- `full-building.png`、`facade-closeup.png`、`entrance-closeup.png`：最终全楼和街边细部渲染。
- `aperture-validation.json`：逐窗第一命中射线验证，证明窗前没有遮挡的实心外墙。
- `component-coverage-validation.json`、`customs-v3-confirmed-components.geojson`、`customs-v3-confirmed-coverage.geojson`：组件关系、实际网格覆盖及可精确替换的对象清单。

使用 Blender 4.3.2 验证。将两个 Python 文件放在同一目录，在该目录执行：

```bash
blender --background --threads 4 --python customs_house_v3.py
```

可用 `CUSTOMS_OUTPUT_DIR` 指定输出目录，`CUSTOMS_RENDER=0` 只生成与验证模型。渲染器使用 Cycles；本环境未编译 OpenImageDenoise，脚本明确关闭降噪。输出单文件均应小于 100 MB，GLB 目标小于 15 MB、三角形少于 200,000。

## 可核实的数据与推定项

### 官方尺寸

[上海海关原官网说明的存档](https://web.archive.org/web/20100610110157/http://shanghai.customs.gov.cn/publish/portal27/tab8419/module26899/info82241.htm) 给出：主楼约 36.2 m、钟楼部分约 43 m、总高约 79.2 m、钟盘直径 5.4 m；分针包括配重总长 3.17 m，时针总长 2.3 m。本模型保留这些数值，总高包括旗杆。原始文字本身使用“约”，不应把这里的小数精度解释为现场测量精度。

原版本由已审阅照片估定的钟室宽 8.2 m、下部三窄窗塔段宽 10.6 m 和钟面造型均保留。仅把整套钟塔平移到 live OSM178407326 的平面轮廓重心：原建筑轴坐标 `(6.5024303, 1.9793415)` m。该调整不改变塔的外形、钟盘或总高。

### OSM 平面轮廓与具体替换关系

主前楼：[way178407318](https://www.openstreetmap.org/way/178407318)，原中心锚点保持为 **121.4854354265109°E、31.238615036350964°N**；前楼矩形主尺度保持 **36.3450488 × 23.4250527 m**，轮廓面积约 850.5477 m²。采用以该锚点为中心的 WGS84 椭球方位等距投影，原建筑轴转入真东/真北的角度保持 **从东逆时针 6.5653151067°**。

新增确认的四角亭并不是用缓冲区猜测。以下每个角亭都与主前楼复用 2 个 OSM 边界节点，同时与斜视照片可见的双前亭及后角亭相符。OSM 并未显式标 `building:part` 或 parent 关系；这里的归属判断综合了节点拓扑、四角布局和照片，保留这一证据限制。看不见的后方立面细部为同风格推定。

| OSM way | 角色 | 原 Overture 对象 ID |
| --- | --- | --- |
| 178407318 | 主前楼 | `6d8beca9-15a2-4a16-92ba-7f10f8ad6cc4` |
| 178407326 | 中央钟楼 | `70c7c81c-2fcb-449d-bb8f-d7b2c71a9e20` |
| 178407330 | 东南角亭 | `3272c4d2-21fc-4459-afd3-835d7b156493` |
| 178407333 | 东北角亭 | `3c97dcf8-b7df-43ee-a5af-7940168a4f2c` |
| 178407328 | 西北角亭 | `be49dcb4-eb0f-45d9-9e85-b7ca28834553` |
| 178407323 | 西南角亭 | `da79d4f8-d796-407c-b945-a5febe856f7f` |

四亭按 live OSM 原多边形建模，包括超出原主矩形的北侧约 3 m 部分：有对应的下部承接墙、窗洞、上部拱窗和屋冠，而不是把原角亭只放大成包围盒。四亭垂直高度仍按照片及官方主楼总高解释，不把源中 `building:levels=9` 机械乘成未知层高。源平面形状也不是经本项目实测认证的边界。

只允许依据表中六个具体对象 ID 替换相应一般化建筑。**西侧独立后翼 OSM380340023、380339914 不属于本模型，不在排除范围内。不要按半径删除附近建筑。**

OSM 数据与衍生轮廓按 [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) 署名 **© OpenStreetMap contributors**；来源为 [OpenStreetMap](https://www.openstreetmap.org/copyright)。源元数据及相对坐标保存在 `customs-components-source.json`、`osm-components-live.json`。

### 参考照片及照片许可

1. [ShanghaiBundCustomsHouse.jpg](https://commons.wikimedia.org/wiki/File:ShanghaiBundCustomsHouse.jpg)，**Diomidis Spinellis**，2006 年照片；选择作者提供的 **[CC BY 2.5](https://creativecommons.org/licenses/by/2.5/)** 许可。本目录的 `references/customs-tower.jpg` 用于钟面比例、三条窄窗、角亭和立面层次核对。
2. [Custom House Shanghai.jpg](https://commons.wikimedia.org/wiki/File:Custom_House_Shanghai.jpg)，**Onedesign23**，1994 年 7 月 15 日；**[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)**。本目录的 `references/customs-front.jpg` 用于入口、前侧墙窗带及角亭的斜视核对。

两张照片仅作为参考，未贴到模型上。它们仍按各自原许可分发，作者及出处见上文和 `references/photo-sources.json`。不能把下载照片称作可直接重建的精确三维资产。海关官网配图是铜钟，未用于外立面建模。

## 真实窗洞如何形成

原来的 `outline(...,1.55,33.20)` 整块主体已移除。每面墙按窗洞边界划分网格：只有窗洞外的墙格生成前后墙面，洞口周缘连接成实际厚度的侧壁。主墙厚度推定为 0.72 m，塔段为 0.60 m。

- 连续窗带的玻璃前表面退入外石面约 **0.43 m**；窗框也在洞内。层间深色装饰板同样内退，窗台向外凸出。
- 双侧墙和背面同样开洞；不是把玻璃移动到长方体表面之外。
- 四角亭是具有真实拱形洞口、拱券厚度和内退玻璃的多边形围护结构。
- 入口五个门洞约内退 **1.12 m**，有门扇/栅格、横档、门框、压顶与台阶。
- 栏杆具有独立竖杆、底座和横杆；檐口与齿饰有实体投影深度。

上述厚度、洞深、框宽、台阶、门扇分格和不可见后立面全部是照片解释与合理构造推定，**不是实测数据**。没有因窗口美化而改动已经核实的总高、钟盘尺寸或主楼地理朝向。

验证从每个抽样洞口外侧向内发射射线，要求第一次命中的是有正确退距的玻璃材质；被实心墙、柱或窗前贴面挡住会失败。角亭修正后共有 **199 条**抽样射线通过。另独立解码最终 GLB 的底面三角形，与六个源组件在同一投影中比较，所有组件覆盖率均高于 **99.99998%**；浮点坐标造成的微小差异记录在验证 JSON 中。
