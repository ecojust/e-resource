# 上海科学会堂一号楼南花园

房管局2C008登记南昌路47号原法国总会（老）。1917年建成的会所在总会迁往茂名南路后改作法国学堂。1927年档案照清楚显示五处亭顶，2014年花园实照及修缮后侧亭正照显示中央露台、横向窗廊、成组木牛腿和原样补配的灰色卵石外墙。本次模型采用2012年12月工程竣工后的外观。北侧不同年代的门廊、两端较晚的平顶和其他院内楼栋保留原状。[建筑出处](../../../source/precise/huangpu-science-hall-building-one/README.md) · [照片与许可](../../../source/precise/huangpu-science-hall-building-one/reference-review.json) · [五亭照片控制点](../../../source/precise/huangpu-science-hall-building-one/pavilion-study.json)

原创近景和原始模型各有117,028个三角面，远景68,116面。重新打开Blender工程核对90个可编辑网格。三份GLB分别通过94项实测，共282项，涉及四段拱窗廊、三联门窗、五处实际坡面、小天窗、时钟、方柱、露台栏杆、石阶以及留空的花园。首次正面渲染发现亭顶之间缺少主脊下方的瓦坡，已按历史照片补齐连续屋面并重新构建、解码、渲染。[四份资产](../../../assets/models/candidates/huangpu-science-hall-building-one/manifest.json) · [独立预览](../../../science-hall-one.html) · [原生核验](geometry-native.json) · [各档检测](surface-checks.json) · [正面](huangpu-science-hall-building-one-preview.png) · [斜视](native-garden-oblique.png) · [照片核对](visual-review.json)

冻结城市来源4396对应有名称和门牌的一号楼，当前OSM来源w494305534与它的足迹交并比是98.50%。南园裁片只覆盖五个亭顶下的窗廊和前伸门廊，原城市楼体近景保留58.61%、远景保留58.49%。同组保留66,664个近景面，相距至少13.81米；另将三个不同组的近远档分别解码核对。地面的实体碰撞保留每根方柱，中央台阶、露台及檐廊下可走到门窗前。[科学会堂院内独立地块](../../../source/precise/huangpu-science-hall-building-one/footprint-review.json) · [实际城市几何](placement-geometry.json) · [配准合同](final-placement-contract.json) · [相机视线](overview-sightlines.json)

164处地标的完整目录中，原生裁切器合计751个三角片，分属16张宏块表，每张最多305片。777个冻结资源全部经HTTP重新取回并校验。[真实运行时](runtime-placement.json) · [实际传输](frozen-http-summary.json)

## 科学会堂一号楼在主地图中的实测

在旧版163处地图中，同一座一号楼由楼体底图表示。新版164处地图能从手机目录直接打开南花园立面，桌面默认能看到长廊、中央时钟与露台；地址灯牌挡住东端一部分亭顶。花园近景与屋面视角可看清五个亭顶及其间低瓦坡。周围楼栋、北面的既有楼体以及两头的平屋顶继续显示。[旧版同位置](map-before.png) [手机](map-mobile.png) [桌面](map-desktop.png) [花园近景](map-street-facade.png) [屋面](map-roof.png)

实际地图显示117,028面近景，拉远后切换为68,116面远景。18个地面位置分别核对可进入的台阶与廊下、门窗与方柱、保留的原楼及五栋邻楼。正式浏览器实取四件下载文件，核验了五处旧体量切面。六张PNG均完整解码并与采集时的文件签名一致。[远景](map-distant.png) [六图及运行报告](city-capture-files.json) [正式核验](main-browser.json) [旧版对照](control-browser.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/4b7e967bde11c5e3027cb5a36250f264a78c6e20/projects/shanghai/index.html#landmark=huangpu-science-hall-building-one&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
