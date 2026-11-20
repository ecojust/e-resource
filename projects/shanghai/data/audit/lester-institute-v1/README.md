# 雷氏德工学院旧址

1934年由雷士德基金会出资建造的工学院主楼位于虹口区东长治路505号，上海市优秀历史建筑编号2F004。2022年底修缮后，上海创新创意设计研究院入驻。园侧尖券和两翼钢窗保存了原建筑的布局。院名沿政府登记使用「雷氏德」，修缮报告写作「雷士德」。北京西路的雷氏德医学研究院另有独立登记。[修缮史与地块来源](../../../source/precise/hongkou-lester-institute/README.md) · [摄影说明](photo-credits.md)

正立面图中七孔门廊约占全宽31.1%，参数模型为31.18%。两翼各五开间，每开间每层三扇钢窗。原生源稿的中央塔身比穹顶宽，两肩高于身后的连接屋面，北部采光带做成三排、每排两跨的锯齿窗。穹肋数量、窗距、未测屋面和各层分高均按现有资料估计。[历史正面与网格比例对照](garden-front-comparison.jpg) · [立面图量取记录](../../../source/precise/hongkou-lester-institute/front-elevation-counts.json)

## 地面及地图

原生城市底图中，具名1131号粗面与当前OSM w1317964106@2的轮廓交并比99.19%。实际源码片中，归于本栋的近景47,728个、远景52个三角面均落在十二个剪裁三角之内。与它共用近景瓦片的1068、209和460号保留，北邻749、西邻1577和南园115也保持原数据。115对应的草坪边界在2022年影像与粗数据间存在差异。[注册足印](../../../source/precise/hongkou-lester-institute/footprint-source-review.json) · [城市两档网格复核](footprint-review.json)

从实际三档模型的行人高度横截面提取门廊石墩，七个尖券下方与侧向通道可通行。33个几何点见证了实体墙、各石墩、廊道、公共园地及两翼位置。模型在地面的投影包含可走的铺地，抽取后的碰撞面积约2411.56平方米。主模型只替换当前具名主楼。[碰撞和取景契约](final-placement-contract.json) · [实测地块、7孔和33个地面点](footprint-review.json) · [保留南侧粗楼后的相机视线](../../../source/precise/hongkou-lester-institute/garden-camera-preflight.json)

## 发布资产与原生核验

单体页提供园侧正视、折翼斜视、屋面三种取景，支持旋转和手动切换远近。原始GLB及网页近档各66,092个三角面，远档48,580个；Blender 4.3.2 重开原件后，共核得168个可编辑网格、15种材质，逐材质的定向三角面与原始GLB相同。两种网页资产解压后也与各自制作源吻合。[单体页及四件下载](../../../lester-institute.html) · [四件下载大小与完整SHA256](../../../assets/models/candidates/hongkou-lester-institute/manifest.json) · [Blender重开实图](hongkou-lester-institute-preview.png) · [逐材质核对](geometry-native.json)

三份GLB各用194个实际表面条件复核七处门廊、门扇铜饰与窗扇、左右翼钢窗、塔身和穹顶、三排锯齿窗与北堂屋面。园内道路、草坪和周围楼房保留原地图数据。[逐点距离与材质](surface-probes.json) · [工学院历史照片](completion-era-garden-front.jpg)

独立单体页已在1250×820桌面及390×844触屏窗口分别选择园侧正面，近档、远档均成功加载。两翼、七孔廊和塔穹都位于画面内；桌面四个下载按钮交付的实际字节与清单一致。[交互与下载记录](viewer.json) · [桌面近景](viewer-desktop-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机近景](viewer-mobile-full.png) · [手机远景](viewer-mobile-lod.png)

168处地图的聚焦标签版本共812个冻结输入，另核实本地块的4个实际城市文件。816次HTTP读取累计770,164,745字节，均与固定位元相同。在相同版本的渲染模块中核查两套矢量底图共14个结果、25处碰撞与邻界见证，1131号的十二个裁切三角均已登记。上述数值来自文件与运行模块，主图的双端实际画面另行验收。[HTTP字节核对](map-http-bindings-20130.json) · [客户端模块与地面](runtime-placement-20130.json) · [实际站点输入](focus-production-snapshot.json)

首个168处目录的SHA256以`9a814750`开头。随后发布的提篮桥相机修正把该处俯仰从61°调整为57°，同步了输入文件摘要，目录SHA256变为`ff4b58ae`。区域灯牌和最终聚焦标签两版均沿用了已校正目录。雷氏德工学院在四份目录中的登记行完全相同。最终版生产快照文件的SHA256以`9192d347`开头。[四个真实HTTP端点、两类散列与逐字段差异](catalog-layer-comparison.json)

聚焦标签及领馆镜头修订后的正式版本 21130 已核对 818 个真实HTTP响应，共 770,176,307 字节。前版的 167 处地标记录保持原值，登记后为 168 处。地面与可见范围采用该版本的正式地图模块验证；城市实拍按其自身记录归档。 [正式字节收据](map-http-bindings-21130.json) · [地面与可见范围](runtime-placement-21130.json)

24129和24130的同址实图分别对应167处和168处地标。真实目录入口在390像素手机与870像素桌面打开工学院，近景的七孔门廊和塔穹可以分辨，改从北面取景可看见三排蓝灰色采光窗。原城市底模的同址照片仍可对照。远处实际换到48,580面，街面近处为66,092面。六个后态下载、25个地面与邻楼见证通过；在两次浏览器会话内均无失败请求、页面错误或地图警告。该层819个冻结输入另外全量实取。[七张实图及逐张观察](city-24130/visual-review.json) · [同址原底模](city-24130/map-before.png) · [街侧拱廊](city-24130/map-street-facade.png) · [北向采光窗](city-24130/map-north-sawtooth.png) · [正式运行记录](city-24130/main-browser.json) · [完整输入](city-24130/130-all-http.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/f178e5ec296d1113067e6d4d047179ce78f0810c/projects/shanghai/index.html#landmark=hongkou-lester-institute&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
