# 原南林师范学校旧址模型复核

整栋保留沿河排窗、东面两座山花、挑台、向南的七开间两层券廊、西南角砖盲券以及合围天井的四翼瓦顶。面向庭院的墙体和树后两面按可见轮廓建造，室内、遮挡处的门窗、屋顶高度和挑台进深有估计成分。[模型浏览与下载](../../../nanlin-normal-school-brick-villa.html) · [原始资料与建模程序](../../../source/precise/putuo-nanlin-normal-school-brick-villa/README.md)

| 视角 | 能核对的部位 |
| --- | --- |
| [东南转角](building-views/southeast-corner.jpg) | 临河窗墙与南侧券廊的交接、最外侧红柱、两道砖带 |
| [排窗立面](building-views/whole-window-wall.jpg) | 双木弓挑台、中央三窗和北段阶梯形窗冠 |
| [上层窗近景](building-views/upper-sashes.jpg) | 放射排列的券砖、上亮与下扇、浅石窗台、窗下饰板 |
| [山花与阳台](building-views/balcony-and-parapet.jpg) | 木肘托、曲面山花、瓶栏与灰砖高低墙 |
| [天井与屋脊](building-views/court-and-roofs.jpg) | 露天天井、四翼瓦顶和两道横脊 |

近景及原始 GLB 各有113,128个三角面。远景有62,080个。近景1,823个实体和远景1,560个实体的有向边成对，体积为正。两档网页文件都经过实际解码，源网和解码网的三角面、朝向、材料分配和纹理坐标一致。三张原创材质随文件内嵌。[实体闭合](closed-solids.json) · [网页两档解码](web-model-verification.json)

重新打开 Blender 工程后，读回1,823个可独立编辑的网格、30种材质和9台相机。对照25,212个使用纹理的面角及三张内嵌图片，与原始网格一致。[Blender 复开记录](editable/native-reopened.json)

东窗面的39个原像标记在两档源网及两档解码网上都命中37个，另两束分别先碰到窗梃和券砖灰缝。四翼瓦面和天井的23条垂直射线在四个模型上均命中，院内9条首先碰到地坪。两座曲线山花与两条航片脊线的轴差分别为0.54和0.39米。[原像首交、天井及屋脊实测](window-wall-and-roofs.json) · [三张原照下的南廊读数](south-arcade/three-station-first-hits.json) · [山花和木挑台](garden-ornaments/README.md) · [西南盲券](south-arcade/west-return-first-hits.json)

早期只完成东南两面时的模型单独留存，可与四翼接入后的全楼比较。[早期转角两档](east-south-corner/README.md) · [五个渲染机位参数](building-views/render-record.json)

南廊三张照片各取27束，合计81束在每个最终模型上命中74束。荒置照片另取西南角18束，命中16束。其余原读数和最先碰到的材质全部保留。桌面和手机各实开9个机位，逐端切换两档模型并分别保存四件文件。18幅截图的画面与下载校验值可逐项核对。[南廊照片及误差](south-arcade/README.md) · [两端实测](ordinary-ui/ordinary-views.json) · [桌面全景](ordinary-ui/desktop-overview.jpg) · [手机天井](ordinary-ui/phone-courtyard.jpg)
