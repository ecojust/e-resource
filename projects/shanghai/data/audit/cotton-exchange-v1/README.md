# 华商纱布交易所 · 上海自然博物馆旧馆

延安东路260号的交易所大楼于1923年建成。1943年的街景可辨西南转角穹顶、沿街山花与窗带，当时门前尚无高架。1958年自然博物馆迁入，2014年旧馆闭馆。2020年街照仍可辨七字门额、铁门中分圆盘和两枚椭圆花饰，模型采用这段博物馆使用史留下的入口形态。[历史与照片出处](../../../source/precise/huangpu-cotton-exchange-building/reference-review.json) · [制作范围与估计](../../../source/precise/huangpu-cotton-exchange-building/README.md)

模型沿南立面重建转角圆塔、开敞柱廊、八个有凹深的圆窗、穹顶和旗杆。街面的中央山花下方有弓形凸窗，博物馆门前两根爱奥尼柱和铁门保留实际可见的前后关系。后部两处低屋面按三期航片概化，屋面下方的原交易大厅以封闭地面表示。模型旗杆顶约31.69米，主体檐部约19.46米，细部尺寸依照片比例估计。[全景](huangpu-cotton-exchange-building-preview.png) · [馆门](museum-iron-gate.png) · [转角穹顶](southwest-cupola.png) · [画面复核](native-visual-review.json)

原始与网页近景各126,728个三角面，远景82,244个。Blender原生文件重开确认118个可编辑网格。三份GLB分别通过106项射线检查，覆盖柱间空隙、圆窗凹底与边框、主屋面和低屋面、门额字面和门扇。独立模型页在桌面与390像素手机各打开近、远两档，四种下载与清单的字节数和SHA-256一致。[模型页](../../../cotton-exchange.html) · [原生重开](geometry-native.json) · [318项表面检查](surface-checks.json) · [实际浏览与下载](viewer.json) · [手机近景](viewer-mobile-full.png)

现行具名建筑面对应冻结地块1602，面积约2,691.55平方米。地图以五个裁剪三角形覆盖该楼25,044个近景及24个远景旧面，同组49,456个近景和88个远景的其他建筑面均保留。最终模型距最近的相邻实际近景网格约4.98米。十二处地面验证涵盖街道、柱间、独立柱脚、关闭的铁门、后部大厅、西侧车道及东侧庭边。局部墙脚与主体之间有约2毫米的接缝，碰撞轮廓在该处闭合，总面积增加约0.86平方米。[建筑面和邻楼](../../../source/precise/huangpu-cotton-exchange-building/footprint-review.json) · [地图落位](final-placement-contract.json) · [实际网格与地面检查](placement-geometry.json)

## 城市地图

158处旧地图的同址画面保留原城市体块。159处地图经正式目录在390像素手机打开本楼，随后的870像素桌面、沿街和屋面取景均载入126,728面的近景。沿街图能辨西南圆塔、山花及四层窗带，门口的本楼标牌遮住部分柱身。目录展开的桌面画面中，本楼与中汇大楼两枚标牌遮住部分南立面。屋顶图可辨两级屋面和西南圆塔。[原址旧画面](final-159-map/map-before.png) · [手机](final-159-map/map-mobile.png) · [桌面](final-159-map/map-desktop.png) · [沿街](final-159-map/map-street-facade.png) · [屋面](final-159-map/map-roof.png)

首轮12个本楼和街道地面点均符合预期，4个相邻原楼的同址碰撞返回空。此时近景组已激活，五个裁片均属于1602号原楼。浏览器报告同时保留 Overture 和 OpenFreeMap 请求失败。独立请求建筑瓦片返回HTTP 503。服务恢复后，相同字节范围返回206，第二次实机在同四个坐标均碰到建筑，载入的3,332个矢量建筑特征包含四个独立UUID。此次近远两档、四种下载、原城市近远两份文件均符合签名，控制台和网络请求错误均为零。[首次实机记录](final-159-map/initial-main-browser.json) · [503响应](final-159-map/external-overture-range.json) · [206复查](final-159-map/external-overture-recovery.json) · [恢复后同址复查](final-159-map/recovery-main-browser.json) · [82,244面远景](final-159-map/map-distant.png) · [交付汇总](final-159-map/model-delivery.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/79de897805be91fbf0badaced62f558b1e255bb3/projects/shanghai/index.html#landmark=huangpu-cotton-exchange-building&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
