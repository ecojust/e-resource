# 福州路44号正广和公司街翼核验

对照2014年1月街面和正射航片后，第二版将平直的两端屋顶收成四坡端部，山花瓦坡交接处留有金属谷槽。西侧底层长窗改成照片拍到的深色横百叶，砖与瓦的色差也按原照调小。[初版原生渲染](preflight/first-roof.png) · [重开最终工程后的渲染](huangpu-caldbeck-macgregor-building-preview.png) · [原照片及年代](../../../source/precise/huangpu-caldbeck-macgregor-building/reference-review.json)

Blender 4.3.2重新打开46个可编辑网格，18种材质的三角面构成与原始GLB对应。近景31,375面，远景13,773面。对原始、网页近景及远景分别进行37次独立射线检查，核实八扇山花窗、木柱、灰泥面、半木构窗带、外部遮板、坡向、烟囱、入口凹入和素面后断面。[可编辑工程与独立解码对比](geometry-native.json) · [111项逐点检查](street-checks.json) · [复核程序](check-street.py)

具名的1960号底图与独立西邻1787号在矢量平面上相交2.73平方米。实际裁切止于两栋的共界之前，与西邻整个近景瓦片仍相距0.474米，远景相距0.546米。西侧瓦片的所有三角面一并参与距离检测，避开共墙处可能有歧义的逐面归属。1960原近景保留74.82%，远景保留74.81%。三个开放剖面按原体6.4米的高度收口。[底图与影像依据](../../../source/precise/huangpu-caldbeck-macgregor-building/footprint-review.json) · [源几何与街面探针](placement-geometry.json) · [地图放置参数](final-placement-contract.json)

初始默认倾角53°时，对街原有屋顶遮住中央低层。保持面向福州路的−13°朝向，调至32°后，两个视口都能看到本次取样中全部自身可见的前立面点。统计包含中央开口、两翼山花及上部窗带；地图实拍另行记录。[双端逐视角射线结果](street-camera.json)

从132个地标的城市目录增至133个；原有记录逐项相同。对冻结站15391逐文件发起486次HTTP读取，含全部481项交付输入和5个原始城市数据文件，共368,699,457字节。[城市输入](production-snapshot.json) · [实际返回文件与校验和](frozen-http.json)

## 132处至133处的主图对照

在18090的132处版本保存同机位原状。地标登记后，18091的133处版本从手机目录点入，随后分别取得桌面默认、福州路街面、屋顶与远档。红色瓦顶、两侧山花和临街窗带在手机与桌面默认视角均可辨认。街面与屋面视角只裁1960号的两个三角，并有三段封边。主图从近景31,375面切换到远景13,773面，11个地面实测和四个文件下载均通过。原生体块的后部、相邻独栋及福州路入口按各自边界保留。[前态](final-map/map-before.png) · [手机默认](final-map/map-mobile.png) · [桌面默认](final-map/map-desktop.png) · [临街立面](final-map/map-street-facade.png) · [屋顶](final-map/map-roof.png) · [远档](final-map/map-distant.png)

外滩7号及9号也与此处使用同一个近景组。第131、132及133处的站点均从V6清单加载同一74,313字节的组。对照原始底图，10个源号共81,458个三角面的表面坐标在0.01毫米比对精度内一致。1960号原有2,712面，本次保留实际近景投影786.08平方米。旧检查在所有133处实图完成后仍要求页面访问早期原始近景文件，留下了一条失败断言。现场单独记录了浏览器实际加载的V6压缩响应体和散列，132处复验亦同时取得原始文件和正在使用的V6文件。最终汇总逐一核对实图、源码模块版本、下载、同一会话响应与三代城市清单。可在本目录运行 `python final-map/verify-map-bundle.py` 复查。[最终核验](final-map/verified-map.json) · [三代近景组实测](final-map/near-transport.json) · [同会话文件收据](final-map/live-resource-evidence.json) · [原始检查记录](final-map/main-browser.json)

第62至90项的29组已发表模型在同一个132处GitHub版本上复核通过。150次实际文件下载合计281,341,768字节，模型文件均与各自清单匹配。[132处版本公开下载收据](predecessor-public-downloads-132.json)
