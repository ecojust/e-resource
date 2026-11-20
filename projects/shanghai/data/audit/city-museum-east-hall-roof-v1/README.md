# 旧市博物馆东中厅屋面修订

两张清晰的航片都显示，东中厅平屋面偏西部有一处约 10.8 米长、5.3 米宽的矩形分格顶盖。2019 年发布的影像中已有轮廓，2022 年和 2026 年发布的影像能辨出分格。2024 年影像存在明显阴影和斜向投影。影像日期依据航片服务的公布批次，四期的个别拍摄日期均未给出。[四期瓦片与量取](roof-observation.json) · [地方志与档案来源](archive-sources.json)

原始档与网页近景各 96,160 个三角面，远景 48,492 个，四件资产合计 13,824,740 字节。对上版已发行的原始、网页和远景分别逐材质核对绕序、顶点位置、连接与 glTF 材质参数。每档仅增加顶盖板和分格边框共 144 个三角面。另对三档各作 23 项向下射线，检查六块板面、四边框和三道分隔、周边六处原始平屋面与两院四个空点。[原始档差异](raw-delta.json) · [网页差异](web-delta.json) · [远景差异](lod-delta.json) · [原始档射线](raw-roof-check.json) · [网页射线](web-roof-check.json) · [远景射线](lod-roof-check.json)

Blender 4.3.2 重开后，场景中可分别编辑原建筑、顶盖底板和分格边框。两个最终截图均从重开后的文件输出。屋面近图可见贯穿长轴的中线及两道横隔；院区斜图可见构件处在门楼东侧，位于南北空院之间。根据航片复核后提高了顶盖的相对明度。[屋面近图](native-eastcover.png) · [东南斜视](native-eastcourt.png) · [原生核验](native.json) · [明度修订记录](finish-review.json)

地方志记有战前后面大厅的用途，本次据航片重建的是现存屋面可辨的顶盖。其材料、功能、安装年代、旧馆与当代后厅构件之间的具体关系、南北侧立面仍待资料。主模型继续沿用江湾馆舍现有 ID、单体入口和两个城市源，庭院小源 510 与 1262 另行待核。[建模参数与重建步骤](../../../source/precise/yangpu-former-shanghai-city-museum/revisions/east-hall-roof/README.md) · [修订四件资产](../../../assets/models/candidates/yangpu-former-shanghai-city-museum/manifest-east-hall-roof.json)

两次场景之间，尚贤坊门楼、董家渡天主堂、原犹太人总会的默认镜头有调整。其余可拟合镜头的建筑在三种窗口尺寸下共有234组计算，取景参数一致。[场景输入及目录差异](camera-input-revision/input-difference.json) · [逐栋镜头核对](camera-input-revision/camera-arguments.json)

最终场景又通过HTTP逐项读取了14个文件，其中包括本次修改涉及的文件和这栋建筑的四种资产。实收16,152,771字节，均与冻结清单或原文件签名一致。[逐文件核对](revised-scene-http.json)

14075与14076两套冻结城市页面分别保持121个入口。校验对照站321个HTTP文件和更新站334个HTTP文件后，从原有地标卡进入旧市博物馆。旧版东厅与远景均已在浏览器读取；同一入口在新版手机视口载入96,160面近景，并显示东厅屋面的矩形分格。图内地标名称、两侧院落和西侧门楼可用于定位。[旧站收据](camera-input-revision/121-before-http.json) · [新站收据](camera-input-revision/121-revised-http.json) · [原屋面](final-city/before-east-roof.png) · [手机实图](final-city/map-mobile.png) · [新近景签名](final-city/first-new-view.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 37 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/ee22a22efac3a1b32e1f1909e2835a610449b555/projects/shanghai/index.html#landmark=yangpu-former-shanghai-city-museum&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 37 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
