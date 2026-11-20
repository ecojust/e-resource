# 仁济医院西院2号住院楼庭院入口

山东中路145号，市房管局第二批2A028麦家圈医院。2010年的楼号、2020年乔争月的4240×2832庭院正面与2024年上海黄浦现场报道先后记录本次入口。同一院区的门诊楼、综合楼及照片右侧另编号3的楼翼分别记录。建模范围为原住院楼正对内院的灰砖墙、白色楼梯塔、上层栏廊和2号圆牌的庭院门廊。[史料、照片及登记核对](../../../source/precise/huangpu-renji-hospital-ward-entrance/reference-review.json)

原始与网页模型有31,008个三角面，简化版17,124个。Blender重开66个可编辑网格，正面六道上层窗带与底层基座分开。按正面实照收薄了普通窗台，东侧栏廊中段有四个窄窗，中央楼梯塔的三组窗列均有逐格凹入的玻璃。三份GLB的60个材料与深度样本分别穿过门弧、号牌及字样、阶梯窗、凹入门、栏杆和砖墙。[四文件与字节](../../../assets/models/candidates/huangpu-renji-hospital-ward-entrance/manifest.json) · [原生核验](geometry-native.json) · [正面预览](huangpu-renji-hospital-ward-entrance-preview.png) · [射线实测](opening-rays.json) · [图像复核](visual-review.json)

底图1977所含内庭端墙长约24.74米，与目前OSM轮廓重合约98.05%。2号楼及2号楼南门的两个地址点均在该源，门诊和4号两个点则位于740号。原生1977近景投影保留97.97%，远景保留98.02%；同瓦片其余3个所有者均未裁剪。验证了开敞庭院、拱门下、后退门扇、拱脚等六处碰撞。默认镜头的静态视线检查包括同一所有者留下的两翼。[固定底图及地址点](../../../source/precise/huangpu-renji-hospital-ward-entrance/footprint-review.json) · [近远网格与碰撞](footprint-review.json) · [放置合同](final-placement-contract.json) · [视线](overview-sightlines.json)

从上海项目目录运行，MACRO为原生14-13720-6694宏区目录，WORK为空目录。

    python -B data/audit/renji-ward-entrance-v1/verify-placement.py --macro "$MACRO" --work "$WORK" --out /tmp/renji-review
    python -B data/audit/renji-ward-entrance-v1/check-openings.py --work "$WORK" --report /tmp/renji-review/opening-rays.json

单体页面已在桌面和390×844手机视口实际打开。近、远景都显示完整庭院入口及旗杆，四个下载文件逐一匹配清单哈希。[浏览器和下载记录](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png)

两次场景之间，董家渡天主堂的默认镜头有调整。其余可拟合镜头的建筑在三种窗口尺寸下共有249组计算，取景参数一致。[场景输入及目录差异](camera-input-revision/input-difference.json) · [逐栋镜头核对](camera-input-revision/camera-arguments.json)

最终场景又通过HTTP逐项读取了14个文件，其中包括本次修改涉及的文件和这栋建筑的四种资产。实收5,331,253字节，均与冻结清单或原文件签名一致。[逐文件核对](revised-scene-http.json)

在124处入口的地图上，通过 HTTP 实取带版本号的三份地图登记表，以及按 SHA-256 寻址的普通建筑总表、分区索引和替换表。共核对14个请求，返回字节与冻结清单一致。[逐次请求](metadata-cache-http.json) · [本次调整涉及的文件](runtime-input-changes.json)

当前两站从页面入口读取实际主模块和登记表，另外逐一核对本站冻结清单的379个文件。[当前两站实际入口与登记表](current-predecessor-http.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/4b2a8f70549ce1221512b190615ad735edfb1623/projects/shanghai/index.html#landmark=huangpu-renji-hospital-ward-entrance&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 11 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)

在123处和124处的实际网页中，以相同中心、朝向、俯角、缩放、标高和边距查看同一内庭。前项显示原生病房楼连续墙面，后项在原位置出现白色塔身、六排窗和庭院门廊。旧版从默认步行切换至城市俯瞰，索引重试后加载了含1977、1515、313、2559的原生近瓦片，近远文件均逐一比对签名。新版由桌面和手机的区目录正常进入，四件下载与清单一致。[前后并排](previous-and-current.jpg) · [123处完整地图](previous-native-desktop.png) · [前态近瓦片实收与相机](previous-native-desktop.json) · [124处桌面及手机记录](default-views-browser.json) · [庭院门近景](numbered-entrance.png)

城区实测中，院内与券下可以通行，后退门扇、拱脚、砖基座以及截面后仍保留的病房楼均阻挡行人。首次测试把最后一点沿用了单体的预期值，记录停在第三张图。将同一地面坐标分别与原生1977、裁剪多边形及新增立面碰撞多边形比较，六个实际读数均与整城边界相符。独立页的远近模型均有成图，城区本次实拍涵盖两个默认入口及门牌近景。[六点逐项核对](city-ground-probes.json) · [首次实测与停止位置](first-city-observation.json) · [初始粗模](initial-visible-map.png) · [真实索引重试](detail-retry.json)
