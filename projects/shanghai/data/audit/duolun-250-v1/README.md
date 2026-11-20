# 多伦路250号住宅

模型依据2014年及2024年的两张正面照片、2008年已上传的端部窗组照片和现状屋面影像制作。原地图中的建筑面约352平方米。西北角按照片校为弧面后，模型在两米行人高度内投影约311平方米。圆角外原先由方形粗楼挡住的一段步行空间已经留出。[照片、门牌与范围](../../../source/precise/hongkou-duolun-250/README.md) · [场地证据](../../../source/precise/hongkou-duolun-250/footprint-review.json)

实际解码近景113,856个三角面，远景51,804个。三档分别核对35个表面与留空位置，包括中央门和两侧下窗、上层三拱、邻侧双拱、两端五连窗、门廊石柱与中央女儿墙。直射曲墙外的西北角没有碰到建筑。[三档105条射线](surface-probes.json)

原始近远档分别解码了编号808与同一近景组的其他对象。所有目标原楼三角面均由专属掩膜覆盖。邻栋554、2136、2942的原始面积全部保留，最接近的独立小楼2136距新模型至少2.46米。路口名称中带“西北门”的兴趣点位于另一栋附近，因此未用作入口位置。[完整几何核验](placement-geometry.json) · [登记契约](final-placement-contract.json) · [街面与三栋邻楼测试点](map-probes.json)

备用 OpenMapTiles 图块把多栋房屋合并成同一个要素。调用交付的矢量裁剪模块后，该要素在目标独立建筑面内的残留面积降至零，三栋邻楼范围内的原有覆盖分别保持原值。其中2136来自独立的另一地图资料，该备用要素本来就不覆盖它。[真实图块结果](vector-source-checks.json)

```bash
cd projects/shanghai
python data/audit/duolun-250-v1/verify-placement.py --macro /tmp/macro-14-13720-6692 --work /tmp/duolun-check --out /tmp/duolun-check
python data/audit/duolun-250-v1/check-surfaces.py --out /tmp/duolun-surfaces.json
python data/audit/duolun-250-v1/prepare-vector.py --out /tmp/duolun-vector.json
node data/audit/duolun-250-v1/check-vector.mjs /tmp/duolun-vector.json /tmp/duolun-vector-result.json
```

## 单体实测

1250×820 桌面和 390×844 手机的正面机位均能看见开敞的中门、弧形街面、中央三拱阳台及两侧拱窗。网页近景呈现较密的饰带、杆件，远景保留院门与窗组轮廓。手机面板占画面下部。四件真实下载的字节、文件名与 SHA256 均匹配最终清单。[查看器记录](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png)

原先从方位 132°、俯仰 62° 进入，街对面的高楼遮住了住宅。改从方位 100°、俯仰 49° 查看，住宅的地图位置、朝向和三档模型保持一致。在俯瞰模式单选一栋且画面仅有一块灯牌时，名称牌移向视口空白区域的边缘，仍可点选。[首次进入的实际画面](preflight/first-overview-obstructed.png) · [变更前后逐项比对](preflight/camera-and-transfer-changes.json)

本次实测还发现，模型传输在 35 秒内未结束时，原页面会记住失败状态。复验让本地 HTTP 服务先发送 16 字节并暂停，第二次请求才发送完整文件。修订后的页面加载器自动请求了一次，核实全部 3,726,512 字节的 SHA-256 后，模型解析器收到 113,856 个三角面。用户中止请求、HTTP 404、文件摘要不符和连续两次超时均有专项回归。[原始传输](preflight/http-timeout-original.json) · [修订后的传输](preflight/http-timeout-retry.json) · [实测程序](preflight/check-network-timeout.mjs) · [113 项相关测试](preflight/runtime-regression.log)

## 全市主图实测

从实际虹口区目录用鼠标及触控进入，1280×800与390×844均选择地标103。默认镜头朝100°、俯角49°。两张默认图中，弧形街面、中门及两翼窗组可见。完整名称移到了房屋上方，在手机上名称中心距建筑地面投影约201个屏幕像素。初始画面先显示正在加载的周边简化楼体。[桌面默认图](main-desktop.png) · [手机默认图](main-mobile.png) · [逐视角实测](main-map-browser.json)

原生高精度图块就绪后，包含13栋房屋的共享组仅裁掉808，保留另12个对象。街面、圆角释放的步行空间及554、2136、2942三栋邻楼在七处地面实测中均符合预期。135°特写覆盖了真实弧墙，前景邻楼的窗框线遮挡部分立面。140°屋顶机位被保留高楼的屋面遮挡，无法用该图辨认住宅的屋面细部。远景切到51,804面的LOD，四件下载的文件尺寸及摘要全部相符。[带邻楼的街面图](northwest-door-and-arcades.png) · [屋顶遮挡对照](curved-roof-and-neighbors.png) · [真实远档](distant.png) · [145项HTTP与运行输入](main-map-inputs.json)

原132°机位在窄桌面主要显示街对面楼墙。调整预设时用旧版同一真实场景保留了对照图。老版手机的完整名称盖住部分上层窗，促成了选中单栋时的名称避让。[旧桌面默认图](preflight/original-overview/original-desktop.png) · [旧名称位置](preflight/original-overview/calibrated-phone-old-label.png)
