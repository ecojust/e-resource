# 董家渡天主堂历史南入口核验

第一版重开原生时发现匾额和楹联的字形落在地面高度。第二版在实际竖向字位布置顶匾和两段题字，并依据近照将顶部十字架改为相连的双边铁轨和斜向缀条。重渲图中顶匾、楹联与立面各自分明，两侧百叶可见间隙。[首次原生渲染](preflight/uncorrected-lettering.png) · [修正后原生渲染](huangpu-dongjiadu-cathedral-preview.png) · [2010至2018年照片与施工记录](../../../source/precise/huangpu-dongjiadu-cathedral/reference-review.json)

三份 GLB 中，原始及网页近景均为59,244个三角面，远景为21,884个。四件成品共5,412,896字节。原生工程含82个可编辑网格，Blender重新打开后逐材质与原始GLB核对。三种 GLB 各实测29条射线，检查三座门、两边上窗、百叶片与片后空隙、石龛人物、三个楹匾和十字架。87项均通过。[工程/序列化曲面哈希](geometry-native.json) · [三版本独立射线](surface-probes.json) · [检测脚本](check-surfaces.py)

第14-13721-6695宏块1831号具名建筑与OSM w206159773重叠约1,636.54平方米。局部仅涉及历史南入口及其3.2米浅进深，已解码城景近模保留约93.93%的水平投影，远模保留约94.04%。最近的同组邻体离切面超过5.54米；东邻1822号与堂内后段均有独立地面探针。后侧原体切面用实际源高和剖面两端闭合，临街门前院地可通行。[原始轮廓、影像及近景件](../../../source/precise/huangpu-dongjiadu-cathedral/footprint-review.json) · [近远景实测](placement-geometry.json) · [正式契约](final-placement-contract.json)

第110处私有站继承前109条目录记录，对新版231个实际HTTP响应核对了95,617,369字节，含冻结的工程目录、网页、近远历史模型与近远城市体块。[冻结清单](production-snapshot.json) · [实取字节与 SHA-256](map-http-bindings.json)

两次场景之间，尚贤坊门楼、董家渡天主堂的默认镜头有调整。其余可拟合镜头的建筑在三种窗口尺寸下共有204组计算，取景参数一致。[场景输入及目录差异](camera-input-revision/input-difference.json) · [逐栋镜头核对](camera-input-revision/camera-arguments.json)

本次发布同时修正了320像素宽手机上全市编号点到旁栋的问题。在108处和125处的实际页面逐点复核，修订后共2,097个测试位置全部指向正确的建筑。[小屏实拍和点选记录](compact-city-numbers/README.md)


原109处地图仍显示旧城体块。第110处首轮地图已载入三座门与双塔，前景854号原生屋顶却遮住中心门洞。两个实际目录签名及七张原始截图都保留下来；109与首轮110的街面诊断镜头相同。[109处的原场景](preflight/prior-109/map-before.png) · [109浏览记录](preflight/prior-109/control-browser.json) · [110原桌面](preflight/initial-default-camera/map-desktop-with-neighbors.png) · [110原手机](preflight/initial-default-camera/map-mobile-with-neighbors.png) · [原始七图、近远模型与地面检查](preflight/initial-default-camera/main-browser.json)

对59,244面教堂近景和实际底图三角面进行遮挡射线检查后，保持朝向1°，把倾角从67°改为60°。独立试站在原生邻楼就绪后用两个视口从目录进入，截图中三座门、两塔及钟面可辨。斜侧备选则使立面明显变窄。这里的实景对应镜头试站，最终110目录另有完整字节记录。[三组目录及最终目录签名](preflight/camera-evidence.json) · [逐视角遮挡比例](preflight/camera-ray-tracing/actual-front-measurements.json) · [桌面正面](preflight/frontal-and-oblique/desktop-frontal-warm.png) · [手机正面](preflight/frontal-and-oblique/mobile-frontal-warm.png) · [斜侧备选](preflight/frontal-and-oblique/desktop-oblique-warm.png) · [试站浏览签收](preflight/frontal-and-oblique/previews.json)

最终场景又通过HTTP逐项读取了13个文件，其中包括本次修改涉及的文件和这栋建筑的四种资产。实收7,453,649字节，均与冻结清单或原文件签名一致。[逐文件核对](revised-scene-http.json)

在正式110处目录（SHA-256 以 b0968aad 开头）内，用390像素宽的手机从分区目录点选董家渡天主堂。开场画面退去、邻楼近景加载完毕后，两侧小门、中央门额、双塔和钟面都在画面中，邻楼854的屋顶位于主入口下方。此处记录本次浏览器会话的两张手机截图。[手机正式取景](mobile-default/map-mobile-with-neighbors.png) · [到站时](mobile-default/map-mobile.png) · [截图时的浏览器记录](mobile-default/browser-at-capture.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 35 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/7215b7a121cec90a70c4680412eb6be7afe3c024/projects/shanghai/index.html#landmark=huangpu-dongjiadu-cathedral&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 35 项时，有 12 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)

最终110处的390×844手机和870×660桌面均由正常地点选择进入，朝向1°、倾角60°，原近景和前方854号楼加载后仍可辨三门、钟及双塔。另从保留邻体的街面、屋顶及远景分别拍摄，近景59,244面、远景21,884面。桌面五图同一会话完成，四件模型与两份原始城市体块均对上SHA，11个地面点包括854号楼、两门、后段、空院地和外侧道路。[手机暖态](mobile-default/map-mobile-with-neighbors.png) · [桌面暖态](final-run/map-desktop-with-neighbors.png) · [街面细节](final-run/map-street-facade.png) · [屋顶和邻楼](final-run/map-roof.png) · [远景](final-run/map-distant.png) · [最终浏览记录](final-run/main-browser.json)

手机首轮取图成功后，该会话的桌面重载遇到25秒原城市目录超时，系统退回粗档。通过原场景方法重发目录请求成功返回，但在该轮截图时限内还未得到暖态桌面图。随后一次独立桌面启动从同一最终目录完整取得五图，记录中无警告或失败请求。[含超时的原记录](preflight/final-city-fallback/main-browser.json) · [同会话人工触发的目录请求](preflight/final-city-fallback/desktop-native-recovery.json) · [两轮取图范围及签名](final-run/evidence.json)
