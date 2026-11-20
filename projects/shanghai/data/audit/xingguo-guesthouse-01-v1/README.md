# 兴国宾馆1号楼几何与配准核验

两份照片分别记录2007年和2015年的花园立面。园侧模型含七开间底层长窗、二层退廊、两侧突出的端翼、园边宽台阶、五处阁楼窗和双烟囱。西侧上层拱廊留有真实洞口。北面、东面和遮挡处仅按城市屋面与照片轮廓建模，室内保留为后续调查。[原片来源、许可与市府名录](../../../source/precise/changning-xingguo-guesthouse-01/reference-review.json) · [西南视角预览](changning-xingguo-guesthouse-01-preview.png)

原始和压缩近景均有28,690个三角面，远景有14,222个。Blender 4.3.2重新打开107件可编辑网格，并将按材质划分的每个三角面与原始GLB核对。模型包含自行绘制的石柱、转角拱洞、扶栏、五处阁楼窗、铜皮坡屋面和成对烟囱。射线检查分别穿过七开间前窗、柱廊后的七个窗、阁楼窗、西侧拱上层与园前台阶。[可编辑文件与网格解码核验](geometry-native.json) · [建筑构件验证](surface-probes.json)

地块337源自OpenStreetMap第293518764号道路对象的第2版，城市源将其登记作「兴国路住宅」。地图远景按顶点来源ID核对，近景按真实三角形独立分出337与同瓦片内的11个其他来源。替换范围与最近相邻实体仍相隔3.21米。建筑碰撞止于底层外壁，园侧中央石阶与屋前草地保持可通行。[实际配准与碰撞](final-placement-contract.json) · [地图近、远景解码](placement-geometry.json) · [地块、园区航片与相邻来源](../../../source/precise/changning-xingguo-guesthouse-01/footprint-review.json)

106项真实站点的独立页已在1250×820桌面和390×844手机分别运行。近、远景切换、模型旋转入口与四个真实下载均核验。[单体页浏览器](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png)

105处旧站保留原城市体量。新版106处目录在手机实点后显示花园住宅，桌面近景可辨柱廊、石阶、五扇老虎窗和两个烟囱。远景实际切换到交付的简化GLB。两站均无页面错误和加载警告；16个地面核查点覆盖主体建筑、园侧可走区域和同一瓦片的11栋其他建筑。对照及五种新画面的输入与六张截图逐份核对散列。[105处对照](control-browser.json) · [106处主图及地面检查](main-browser.json) · [街面柱廊](map-street-facade.png) · [花园面屋顶](map-roof.png) · [正式站输入](production-snapshot.json) · [193项文件与实测报告复核](map-comparison-verification.json) · [实际对照命令](compare106-revised.sh)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 35 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/0961aa3474c43bae386f801d3a92c69c2d079eaa/projects/shanghai/index.html#landmark=changning-xingguo-guesthouse-01&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 35 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
