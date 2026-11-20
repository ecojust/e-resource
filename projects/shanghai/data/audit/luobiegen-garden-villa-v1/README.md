# 罗别根花园主宅模型检查

## 藏品身份和外观依据

上海市房屋管理局首批名单 1M004 记载「虹桥路2310号住宅／海南置地上海公司／虹桥路2310号」。城市底图对应宏块 14-13715-6696 的 1431 号。其原始 OSM way 1316079023 第 2 版的门牌、旧名、公司名、两层及 1989 年第 48 号登记与同一主宅吻合。与正式源面的面积交并比为 97.53%。地方志区分此宅与虹桥路 2409 号的另一项沙逊地产。[地址、版本和屋顶证据](../../../source/precise/changning-luobiegen-garden-villa/footprint-review.json) · [照片、年代与文献](../../../source/precise/changning-luobiegen-garden-villa/reference-review.json)

## 实体几何与原生文件

完整与原始 GLB 为 18,834 个三角面，远景版为 9,276 个。四件文件共 1,792,017 字节。Blender 4.3.2 重开工程后检查了 223 个可编辑网格，并按材质核对全部有向三角面。三份 GLB 另各有 30 条射线测量，检查上、下层窗格和玻璃之间的深度，中央廊内退后的门窗，两座烟囱的真实内腔，以及西侧保留连接段和南向廊口的空地。[模型及原生核查](geometry-native.json) · [90 条射线记录](surface-checks.json) · [射线程序](check-surfaces.py)

初版的原生照相机以旧地块质心构图，裁去了东侧窗室和烟囱。最终机身原点向主立面东端平移 2.7 米，地图登记锚点作等量转换。对照区规划局存档的 1998 年花园照后，模型加宽了木构上下层间的花格带，重做了山墙窗下的深色纹样与边柱。正面图由最终原生工程实际重开并以 Cycles 48 采样渲染。[修正前](preflight/initial-framing.png) · [最终花园立面](changning-luobiegen-garden-villa-preview.png)

花园斜视与后方俯视显示，主屋交叉屋面的六处端头曾露出阁楼内部。修正时沿瓦面边缘的挑檐增加了七片素灰泥封墙。侧向探针从原来穿过整段阁楼，变为逐点在 0.86 至 1.21 米处碰到对应端墙。中心屋脊与前方两座山墙、东侧低屋面和南北向后屋面的交接均可从同一机位复查。阁楼端墙饰面及后屋面形式据影像推定。[修正前花园斜面](preflight/open-gable-garden-oblique.png) · [修正前后屋面](preflight/open-gable-rear-roofs.png) · [原缺口的六条射线](preflight/open-gable-rays.json) · [修正后花园斜面](garden-oblique.png) · [修正后屋面](rear-roofs.png) · [原生二次渲染记录](native-views.json)

## 局部替换与邻楼

1431 号源面东侧包含主宅，西侧伸出较窄的连接段。近景原生包内共有 13 栋房屋；按组内原始面逐三角形识别，本栋最近与次近归属的最小间隔为 2.72 米。远景按源面顶点的 feature ID 识别。两种包中主宅一侧的原始几何均被替换，西侧连接段保留约 38.93 平方米，近景含突出窗饰时约 41.09 平方米。新模型距最近的独立东侧建筑约 10.35 米。受遮蔽的屋面与后侧墙体按影像估计。[登记契约](final-placement-contract.json) · [三角面、六个地面探针与邻楼间距](placement-geometry.json) · [测量程序](verify-placement.py)

2026 年 11 月 15 日的 OpenFreeMap 回退瓦片把本宅和多个远处建筑收入同一高度聚合对象。实测保留的连接段在布尔差前后均为 38.928 平方米。生产 JavaScript 再分别处理原始聚合与 Overture 单栋要素，两个提供方均只隐藏目标原形并显示余下的连接段。另两组近景建筑的裁切数量均为零。[实际瓦片面积](fallback-vector.json) · [生产模块核验](runtime-source-checks.json) · [矢量检查程序](check-sources.mjs)

```sh
python data/audit/luobiegen-garden-villa-v1/check-map-fallback.py --geojson /tmp/luobiegen-fallback.json
node data/audit/luobiegen-garden-villa-v1/check-sources.mjs /tmp/luobiegen-fallback.json
```

辅助预览在桌面及手机分别加载并切换两份 GLB，南花园面的两座山墙、中央门廊和东端窗口均实际可见。桌面点击四个文件链接，逐件核对下载内容与清单。[预览及下载结果](viewer.json) · [桌面近景](viewer-desktop-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机近景](viewer-mobile-full.png) · [手机远景](viewer-mobile-lod.png)

## 上海主图

在第 97 处的冻结地图中，手机按区目录能打开罗别根花园主宅。桌面默认机位能见两处前山墙和西侧保留段。花园近景与斜上机位中，地图地点卡遮住少量一层细部；独立预览可看全貌。主图确实切换到 9,276 面的远景文件。九个地面探针覆盖入口、花园、中央门厅、两侧房间和西侧连接段，同时核对城市 2291、2565 和 1901 的邻楼碰撞。西侧连接段仍有建筑碰撞，中央南廊入口及花园可通行。[主图实际操作记录](main-browser.json) · [桌面默认](map-desktop.png) · [手机目录入口](map-mobile.png) · [花园近景](map-street-facade.png) · [斜上屋面](map-roof.png) · [真实远景](map-distant.png)

97 处目录与上一版的前 96 处逐模型比较一致。120 项冻结输入和六份原始城市文件共 126 次 HTTP GET，返回 11,216,540 字节。[生产输入指纹](production-snapshot.json) · [HTTP 文件实收记录](map-http-bindings.json)

320 × 568 像素的手机上，选择宏恩医院的三行地点名称后，地点卡顶边为 328 像素。图例、工具按钮与地点卡之间留下 243 × 138 像素，97 个 22 × 15 像素的独立编号均可点击，字号为 12 像素。重新读取截图，97 个编号的墨绿色底板和金色描边全部已绘制；点击第 97 号后进入罗别根花园主宅，读取的完整模型哈希与登记一致。[正式窄屏截图](map-97-markers.png) · [实际点击与像素检查](compact-browser.json) · [复核程序](check-compact-map.cjs)

地点卡较低时，97 个 20 × 16 像素的编号也可独立选中。初次检查较高地点卡的截图只绘出了引线；正式程序增加了地图图符就绪及逐格截图像素检查，再复核点击。[普通地点卡对照](preflight/existing-cards/compact-browser.json) · [图符载入前的首帧](preflight/before-symbols/map-97-markers.png)
