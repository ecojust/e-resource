# 旧上海市博物馆江湾馆舍：来源与外观范围

模型 ID：`yangpu-former-shanghai-city-museum`；名录 `sh-historic-b2-012`。对象为杨浦区长海路174号长海医院内的旧上海市博物馆江湾馆舍（影像楼）。四川北路1844号1946年复馆地点、人民广场上海博物馆及同院飞机楼均是不同对象。

本轮制作现存馆舍的有界外观。地图主源1860与重叠门楼1931整体现状接入，正面、两层外翼、中央门楼依据照片细化。主源东中后厅仅作简化估计体量：地方志证明原馆曾有后厅，但没有证明现状东中凸出段全部范围、年代、屋面和门窗。凹院独立小源510/1262保留原状；不把它们直接归入历史楼梯或连廊。`sh-historic-b2-012` 的后厅细化、小源调查待办保留。

实际阅读的材料包括[建筑条目](https://zh.wikipedia.org/wiki/上海市立博物馆)、[上海地方志目标小节](https://web.archive.org/web/20120101173212id_/http://www.shtong.gov.cn/newsite/node2/node2245/node4467/node20490/node20492/node63796/userobject1ai16055.html)、[杨浦政府配图页](https://www.shyp.gov.cn/shypq/bnsz-jbwg/20171116/50310.html)，以及搜狐文章的博物馆相关段落、扩建手绘文件说明和新浪图注。地方志为《上海文物博物馆志》第二编第一章第一节中的“四、上海市博物馆”，没有声称完整审读其余条目。

实际查看了5张外观照片（4张现代、1张历史）、7张室内照片和1张扩建设想图，共13张视觉参考。2010正面照及政府配图支持中央5道高竖窗、底层单拱门、两八角小窗、上层红柱敞廊/内退窗墙、浅门槛、双重黄瓦屋面和现代两层翼部。室内照片不能证明后厅现状外轮廓；扩建设想图没有实施证明，图上的大院和高阶不复制。所有来源照片拍摄年代与页面发布日期分别记录。

24米为百科所记门楼离地最高点，10.5米为百科所记外墙高度。两值只核到次级文字，未取得其杨浦图书馆原文或原设计图；不得称为本轮实测，不将10.5米机械套作全部现代翼部檐高。地方志“四层、1900平方米、约3400平方米”和百科“两层、1700平方米、3430平方米”保留口径差异；名录1935、条目1934开工/1936完成、1937开馆、地图built1933亦不混为一个日期。地方志目标小节内部筹备年月前后不一致，原样保留而不默改。

原历史单层翼与上部少窗墙面只用于沿革对照，现状按现代照片两层翼部制作。缺乏现状后侧全貌、测绘平面与官方修缮技术图，后厅、隐藏面及微小构件仍有估计，不能宣称纯1935年复原或全立面照片验收。

`source-register.json` 逐项列出真实阅读/看图范围、版权、私缓存哈希和未核内容；`documentary-review.json`、`photo-review.json` 用于审计目录。地图切片、覆盖集合及重叠去重以独立 `footprint-review.json` 为准。第三方网页、照片和手绘只存私缓存，公开文件只发布独立事实摘要、出处、链接与哈希，不发布原图或全文。

## 最终资产、许可与重建

[全局主图直达](https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#landmark=yangpu-former-shanghai-city-museum&mode=overview)

原始档96,016个三角面，网页档96,016个，远景档48,348个；四资产共13,809,214字节，含可编辑Blender。模型外包高度约23.962米，仍为作者估计。 [四资产清单](../../../assets/models/candidates/yangpu-former-shanghai-city-museum/manifest.json)逐件绑定大小与SHA256；[作者说明](AUTHOR_NOTES.md)给出组件、未建范围、重建命令与验证限制。

原创几何与代码采用[MIT许可](LICENSE)，地图参考为ODbL-1.0；通用辅助代码来源、原提交与许可见[source/HELPER_PROVENANCE.json](source/HELPER_PROVENANCE.json)。源码与参数位于[source/](source/)。作者在独立复制目录实际重建原始与未压缩远景输出并逐字节核对；网页与远景压缩后按有向FLOAT32材质三角摘要验证，详见[重建记录](../../../data/audit/city-museum-v1/author-portable-rebuild.json)和[压缩几何核验](../../../data/audit/city-museum-v1/author-packaged-geometry-checks.json)。

最终Blender保存后实际重开，由同一最终文件输出front、oblique、rear、roof、entrance、gallery、roofdetail、wing八图；Root逐张实际查看并绑定最终四资产，见[原生图审查](../../../data/audit/city-museum-v1/native-visual-review.json)。网页检查另行记录，原生图通过不代表后厅范围或隐藏立面已获得新的来源证明。

现存地图主源1860完整轮廓与重叠门楼1931接入；西正面、现存两层南北翼部和黄瓦重檐门楼按照片详化。东中后厅仅作同低翼级的简化估计体量，当前具体范围、年代、屋面和门窗细部未核。院凹小源510/1262独立保留，室内、医院邻楼及院区地面不并入。 北院上方原粗模的悬置边片按高度补充裁剪，保留独立邻体及其屋檐；原模型资产和地面碰撞不变，范围与残量见[足迹审查](../../../data/audit/city-museum-v1/footprint-review.json)。24米与10.5米仍是次级文字口径，不是现场测量。后厅细化与小源调查两任务继续列在b2-012下。
