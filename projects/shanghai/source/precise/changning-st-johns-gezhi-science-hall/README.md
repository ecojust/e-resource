# 圣约翰大学科学馆（格致楼42号）西院券廊

格致室于1898年11月20日奠基、1899年7月19日启用，供自然科学教学，亦称科学馆。1998年改名格致楼，校方在2018年完成约十个月文保修缮。上海市房屋管理局第二批优秀历史建筑2M006将科学馆和办公楼42号列为同一登记对象，名录地址为万航渡路1175号，校方现用1575号。[华东政法大学校方图文](http://www.ecupl.edu.cn/2022/1101/c13514a193943/page.htm) · [上海市房管局原表](https://fgj.sh.gov.cn/yxlsjz1/20200331/30c648cb811f401192bb61dd1dd487c9.html)

院面共有九个开间轴线。近正照可数出中央门上窗及左右六组宽窄券窗。北端圆窗和另一组宽窗位于这张照片的裁切线以外，九轴可在校方近正面和俯拍中逐一对应。模型包含西侧三层窗墙、地层券廊内可见的门扇和护栏、中央四级踏步、右起的格致樓题字、两处起翘小屋面及前部瓦带。树木遮住北端地层，模型将这段做成有限的实体墙身。屋后、沿河的墙面、天窗及南侧圆角构造可在校方照片中看到，超出本次西廊的制作范围。

南起斜看院面的另一张600×399照片，正文图说称“新科学馆”。照片中的三字匾位于宽券门上方，右边三窗依次窄、宽、窄，靠南的小檐居中压在宽窗上。三组特征与校方格致楼近正面、航摄相符。1923年6月30日启用的新科学馆在苏州河对岸光复西路1347号，后为司法鉴定科学研究院综合楼。三幅照片均作量测资料，原图未收入资产或离线包。[校史口述项目的原始说明](http://pr.sju.edu.tw/campusnews/sjuoldphoto/v001.html) · [《海上记忆》对河东新科学馆的沿革考证](https://www.sohu.com/a/657944355_121332532)

普通城市模型的2173号原户与标有科学馆的地图轮廓交并比约0.989。西院长边32.82–32.86米，侧向深约19.54米。2018和2025两期影像的长檐读数分别约38.1米和35.25米，受檐挑、树荫与高物位移影响。独册前部屋带只进楼3.84米，原城保留整个2173号楼和旁边的41号怀施堂。OSM的1924年标签和学校格致室落成档案冲突，模型年代采用1899年。

## 尺度与机位

西墙沿南偏东约19°，模型X向院面照片的右端，Y进楼，Z向上。近正面照片没有相机元数据。校正采用墙长、跨站同名点、圆窗的投影形状和主檐前后遮挡；18米前距和1.6米眼高是有误差的条件取值。两处斜站的控制点中位残差分别约1.30和1.45原像素。留验表逐点记录第一交及8像素内邻近命中。九镜中三镜对应摄影画幅，其余用于观察屋檐、窗扇、题字及全廊。

## 复建

```sh
python source/science_finishes.py
python measurements/register_science_hall.py
python measurements/make_science_cameras.py
python measurements/check_mesh.py rebuilt/whole
python measurements/check_science_views.py rebuilt/whole/full-source.glb rebuilt/held-out.json
python measurements/render_science_views.py rebuilt/whole/full-source.glb rebuilt/photos
```

模型、三字笔画和两对材质色纹、法线均以程序制作。源码按仓库MIT许可提供。建模需要Python、NumPy、SciPy、Shapely和Pillow。下载版源码包内有GLB、Blender、FBX、OBJ和STL复建程序及版本核对方法。[普通模型页](../../../st-johns-gezhi-science-hall.html)
