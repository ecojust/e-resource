# 圣约翰大学思颜堂四十号楼草坪前廊

1903年12月24日，思颜堂奠定隅石，次年10月1日落成，以颜永京命名。西翼曾作为学生宿舍，东翼的大会堂是1913年孙中山演讲处。市房管局2M006将思颜堂列为学生宿舍40号楼，登记地址万航渡路1175号。华东政法大学长宁校区现用1575号。钟楼所在的41号怀施堂在它东侧。[校方《40号楼》](https://www.ecupl.edu.cn/2022/1101/c13514a193945/page.htm) · [房管局第二批名录](https://fgj.sh.gov.cn/yxlsjz1/20200331/30c648cb811f401192bb61dd1dd487c9.html)

本件记录面向草坪的十一开间。西部七间通高三层，向东续接四间二层敞廊。灰砖墩上起红砖扁券，上层白色斜格栏板透空。三层瓦檐与二层女儿墙在第七间东端相接。2022年校方档案中的东西地面照片和两处航摄共同限定这一段外观，原摄影日期未载。成品的进深止于前廊及窄屋面带；后院、东北长厅、相邻怀施堂分属其他视面。摄影原作仅供量测。[照片、年代与权利记录](measurements/yen-hall-sources.json)

近似总宽42.8米取自原城市实体1435的南面两端。以十一开间展开，四站拟合拱顶、楼面和柱轴；檐深与遮蔽下的回廊内侧保留为近似。模型贴图按砖面实测色域重新绘制。[源像点](measurements/arcade-photo-observations.json) · [四站配准与误差](measurements/arcade-registration.json) · [实照断面](measurements/arcade-section-readings.json)

从本目录运行以下命令可复建近、远两种网格。

```sh
python measurements/register_arcade.py
python measurements/make_arcade_cameras.py
python source/arcade_finishes.py
python measurements/check_mesh.py /tmp/yen-hall
```
