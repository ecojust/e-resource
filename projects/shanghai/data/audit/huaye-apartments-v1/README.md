# 华业公寓主楼模型检查

## 识别与取材

原始航拍记录了 2019 年 12 月 8 日的相机位置、云台方位 50.8° 和俯角 22°。沿该方向约 75 米，在上海展览中心以东、酒店以南可辨红色八面塔顶和两侧平行的退台楼体。2015 年的院内照片提供了首层雨棚、窗扇与阳台铁栏的细节。上海市政协、静安区政府和地方志中的地点与体量描述，以及两幅历史照片，都支持陕西北路院内的位置。黄浦区的同名长方形住宅不属于此次建模对象。[原始来源及照片散列](../../../source/precise/jingan-huaye-apartments/reference-review.json) · [相机位置、土地轮廓和地图原件](../../../source/precise/jingan-huaye-apartments/footprint-review.json)

## 几何

完整模型有 105,170 个三角面，远景版 50,166 个。模型估计总高 42.76 米，包含顶针。原始和网页模型逐材质核对全部有向三角面，压缩后的远景版与简化的导出输入单独比对，重新打开 .blend 后复查了 1,136 个可编辑网格及 11 种材质。每一件 GLB 另作 38 条射线检查，覆盖宽窗、窄窗、前后顶层拱窗、中央阳台栏板、塔窗、入口雨棚和开敞院落。[几何与原生工程](geometry-native.json) · [114 条射线](surface-checks.json)

初版屋顶与臂楼侧墙的重合面在斜视角形成暗条。终版将侧墙后退至前后墙的内侧，把露台屋面抬离墙顶，并依据东面档案照补上园侧阳台、三联拱窗和屋顶角楼。正面预览使用原生工程的 Cycles 48 采样。另从同一文件渲染西南院侧和东侧花园视角，后者改变了灯光方向以便辨识窗洞。两张补充图均用 Cycles 32 采样及 Open Image Denoise 滤波。[初版](preflight/initial-front.png) · [终版正面](jingan-huaye-apartments-preview.png) · [西南院侧](native-southwest.png) · [东侧花园](native-garden.png) · [机位脚本](render-views.py) · [原生文件与渲染图绑定](native-views.json)

## 登记与检查

本体对应宏块 14-13719-6694 中两个独立的无名建筑。505 位于西北，2897 位于东南，两者之间的最高塔在原始源面中另有缺口。分别解码包含两栋的近景包，按其组内全部源面分配三角形，再用远景 GLB 的原生 feature ID 核对。两处粗模型替换边界内的所有三角面均被覆盖，其余同组建筑保留。院内另两条长形建筑 518、2148 与详细模型分别相距约 10 米、12 米。地面碰撞依据三份模型的 2 米以下结构投影，H 形端部敞口、东侧庭园和西面空地维持可通行。[配准几何](placement-geometry.json) · [登记契约](final-placement-contract.json) · [所有者和碰撞结果](runtime-source-checks.json)

2026 年 11 月 15 日版 OpenFreeMap z14 回退瓦片中，两块研究源面所在地缺少建筑。检查了 building 层的 26 个真实聚合要素，最近的几何距替换边界 10.65 米。城市场景两处实际源建筑来自 East Asian Buildings，与该 OSM 回退覆盖面有差异。[回退瓦片实测](fallback-vector.json)

本目录下的 check-surfaces.py、verify-placement.py 和 check-fallback.py 均支持 `--help`。运行 check-sources.mjs 时传入地图依据中记录的原始 feature-table.json.gz。Chromium 在 1,250 × 820 桌面和 390 × 844 手机视窗分别加载了近景与远景，点击四个链接下载共 9,496,163 字节，并逐件核对清单中的 SHA-256。[辅助预览检查](viewer.json) · [桌面近景](viewer-desktop-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机近景](viewer-mobile-full.png) · [手机远景](viewer-mobile-lod.png)

## 第 93 个主图入口

从 92 项地图目录顺序加入华业公寓，原有记录内容逐条保留。Chromium 实际从手机地标目录进入建筑，桌面加载同一入口，再查看西南立面、塔顶及远景。桌面默认构图可见整幢主楼，手机可辨中央八面红塔、两翼和圆弧阳台。所选西南视角的地点卡遮住一部分底层。两个近景源组在各自启用时均只裁到已选编号，另两座独立院楼的地面仍受阻。共检查八处真实主图碰撞。全程没有页面错误、HTTP 错误或 WebGL 错误。[主图记录及脚本](main-browser.json) · [运行脚本](check-main-map.cjs) · [实际机位与邻栋样点](map-case.json)

[手机](map-mobile.png) · [默认桌面](map-desktop.png) · [西南立面](map-southwest.png) · [塔顶](map-roof.png) · [城市远景](map-distant.png)

93 项正式登记与测试站的地图目录、入口、代码及资产内容一致。测试站以 HTTP 取得并校验了 150 份输入；其中五份为冻结的城市宏块源文件。145 份登记快照中有一份业务队列在正式工作区增加了先前建筑的发布记录，页面资源与地标目录的字节均一致。[HTTP 响应摘要](map-http-bindings.json) · [与第 93 项正式登记比对](registered-equivalence.json)
