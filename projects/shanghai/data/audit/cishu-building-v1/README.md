# 慈淑大楼东北街角与塔亭

市房管局第二批2A027在南京东路353号登记慈淑大楼、东海商都。中国国货公司于1933年开幕。杨浦区图书馆的资料记1934年在南京路侧加建顶层，并描述转角的三层塔楼。直至2024年的多角度街面影像可见下层浅弧大窗、扇形镶饰、上部成组矩形窗和街角双窗带；模型以这些现存街面和塔亭为范围。[登记、史料与历史及当代照片](../../../source/precise/huangpu-cishu-building/reference-review.json) · [制作边界](../../../source/precise/huangpu-cishu-building/README.md)

原始和网页模型均为45,930个三角面，简化模型29,766个。三份GLB独立解码，逐一检查了99条沿两街、斜角与塔顶的材料和深度射线；Blender重开131个可编辑构件并比对三角面及材质。七层街墙底层有内退的玻璃，第二层浅拱之上布置分段镶饰，最上方钢环与玻璃灯体之间留有空隙。[四文件](../../../assets/models/candidates/huangpu-cishu-building/manifest.json) · [原生与压缩核验](geometry-native.json) · [射线](opening-rays.json) · [渲染](huangpu-cishu-building-preview.png)

固定宏块14-13720-6694的1015号与实名现状OSM重合99.37%。裁剪沿两个近角街段呈L形，只占原生屋顶的一小部分，近景保留95.93%，远景保留95.98%。同近景瓦片的1845号与裁剪边界至少相距12.50米。实际三角形核对六处地面点，商场原有十字通道的净宽与通行现状留待现场验证。固定周边楼体的视线检查覆及桌面、手机两种视高。[固定坐标和归属](../../../source/precise/huangpu-cishu-building/footprint-review.json) · [地面点及保留比例](footprint-review.json) · [放置合同](final-placement-contract.json) · [视线](overview-sightlines.json)

独立页面分别以桌面及390×844手机打开近景和简化模型。浏览器读取的GLB及Blender四个文件与清单哈希相符。[独立页浏览器报告](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [逐图观察](visual-review.json)

127处与128处的本地发布副本通过HTTP核对。新增慈淑大楼后，原有87条精细候选记录保持一致。冻结的128处站点在普通登记缓存更新后共绑定441个输入文件。[两版目录及模型对照](predecessor-controls.json) · [生产文件指纹](production-snapshot.json)

若要重验，从上海项目目录指向原生宏块及空白解码目录运行下列命令。

    python -B data/audit/cishu-building-v1/verify-placement.py --macro "$MACRO" --work "$WORK" --out /tmp/cishu-review
    python -B data/audit/cishu-building-v1/check-openings.py --work "$WORK" --report /tmp/cishu-review/opening-rays.json

在128处入口的地图上，通过 HTTP 实取带版本号的三份地图登记表，以及按 SHA-256 寻址的普通建筑总表、分区索引和替换表。共核对15个请求，返回字节与冻结清单一致。[逐次请求](metadata-cache-http.json) · [本次调整涉及的文件](runtime-input-changes.json)

当前两站从页面入口读取实际主模块和登记表，另外逐一核对本站冻结清单的441个文件。[当前两站实际入口与登记表](current-predecessor-http.json)

在提篮桥镜头校正后的正式127处和128处地图上，桌面和390×844手机均由正常目录点入慈淑大楼。两端首屏都看见东北街角塔亭、两侧街墙及对应灯牌，四种文件逐一通过 HTTP 校验。[桌面首屏](main-desktop.png) · [手机首屏](main-mobile.png) · [前后目录、四种文件和浏览器记录](default-views-browser.json)

沿街骑楼近景可辨首层内退门窗、浅拱与上层窗带，塔亭近景可辨逐层收分及透空的金属灯架。随后实测保留原楼的视角及切换为29,766面的远景。此次浏览器实际读取的164个文件和四份目录生成记录均通过哈希核验。[骑楼](street-arcades.png) · [塔亭](stepped-lantern.png) · [原楼与模型交接处](retained-source.png) · [远景](distant.png) · [六个视角与运行状态](main-map-browser.json) · [现场请求](main-map-inputs.json) · [实盘对照](map-input-compare.json)

合并密集灯牌后，从两份128处地图的页面入口分别下载登记行、模型清单、配准合同及四件模型。相机、单体位置、1015号源的裁剪与碰撞、多档切换阈值和所有文件字节一致。主场景代码唯一的变更行是灯牌模块的版本引用；前版已实测的桌面和手机相机姿态也写入对照。[两站22次HTTP请求与前版所选模型](label-release-http.json) · [复核脚本](check-label-release-http.py)
