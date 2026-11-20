# 原上海犹太人总会南楼核验

首版将两侧拱廊的屋顶各自收成独立四坡。2020年俯拍可辨每翼的横向屋脊连续接入切角端翼，侧翼天沟回折。第二次以相连的坡面、屋脊和谷线重做两翼，并补上门廊的横向斩石纹理。修正后重开原生工程核对，庭院一侧十个拱券、四根入口柱、侧圆窗与二楼栏杆可辨。[首版原生渲染](preflight/disconnected-wings.png) · [修正后原生渲染](jingan-jewish-club-preview.png) · [照片](../../../source/precise/jingan-jewish-club/reference-review.json)

原生99个可编辑网格。原始和网页近景均为80,644个三角面，远景为36,830个。四件成品合计8,729,474字节。三份 GLB 各用39次真实射线核对两翼拱券及后退的二层门、双柱、圆窗、端翼、老虎窗与屋顶，共117项。[原生工程与几何](geometry-native.json) · [三版本射线](surface-probes.json)

实体定位于14-13719-6694宏块2124号。南楼沿庭院约56.85米宽，北面垂直翼夹在其他房屋之间；切南楼后，原生近景保留22.07%的水平投影、远景保留22.01%。西南侧2772号离原始2124仅约0.51米。对整份近景组各三角形的三个顶点和重心，分别比较至全部六处原始轮廓的距离，四次归属完全相同。该邻楼离最终裁边仍有0.18米以上，三个其他院边源也分别实测。[原体及影像](../../../source/precise/jingan-jewish-club/footprint-review.json) · [近远原件、探针与距离](placement-geometry.json) · [放置契约](final-placement-contract.json)

另实取同一宏块的OpenFreeMap矢量瓦片，逐一计算裁边前后的相邻楼体覆盖面积，检查地址722号以外的地面范围。[独立矢量记录](fallback-geometry.json) · [检测脚本](check-fallback.py)

背侧平顶与高坡之间添加浅色封口，对左右屋顶山墙及后檐共补九条实物射线。背后高机位可复核两侧封口、分支屋脊和中部平顶。[背侧屋面](native-roof.png) · [复开原生渲染脚本](render-roof.py)

第116处登记在南京西路722号，保留115处前身目录的全部记录。私有站279个HTTP实取合计155,076,134字节，含同一地址的原生城市宏块、几何组、模型四件和前身目录的文件。[冻结收据](production-snapshot.json) · [HTTP实取](map-http-bindings.json)

两次场景之间，尚贤坊门楼、董家渡天主堂、原犹太人总会的默认镜头有调整。其余可拟合镜头的建筑在三种窗口尺寸下共有219组计算，取景参数一致。[场景输入及目录差异](camera-input-revision/input-difference.json) · [逐栋镜头核对](camera-input-revision/camera-arguments.json)

最终场景又通过HTTP逐项读取了13个文件，其中包括本次修改涉及的文件和这栋建筑的四种资产。实收10,974,005字节，均与冻结清单或原文件签名一致。[逐文件核对](revised-scene-http.json)

最终116处地图从目录选择南京西路722号的庭院南楼。新的构图框覆盖中央门廊，原模型的尺寸、定位与两翼不变。390×844手机和870×660桌面上的初次画面与原邻楼加载后的暖态均已实际截图；暖态可辨双柱入口、拱券、上窗、栏杆与屋面。

[手机初次选择](final-defaults/map-mobile.png) · [手机暖态](final-defaults/map-mobile-with-neighbors.png) · [桌面初次选择](final-defaults/map-desktop.png) · [桌面暖态](final-defaults/map-desktop-with-neighbors.png) · [四张图取得时的真实状态](final-defaults/browser-at-capture.json)
