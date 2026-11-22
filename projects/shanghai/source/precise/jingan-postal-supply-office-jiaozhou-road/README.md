# 胶州路邮政供应处西立面与南端墙

上海市第五批优秀历史建筑名录的 5B057 登记在胶州路 320 号，原名为交通部邮政总局驻沪办事处。1941 年《上海行名录》用中英文同列「郵政總局駐滬供應處」「Postal Supply Dept.」及胶州路 322 号。1942 年工商索引和门牌索引也分别收有该地址。今天的单位院门沿用 322 号。[1941 年原页](https://archive.org/details/1941-shanghai-desk-hong-list-july-edition/page/n253/mode/1up) · [1942 年工商索引](https://archive.org/details/shanghai-up-to-date-directory-1942/page/n227/mode/1up) · [1942 年门牌索引](https://archive.org/details/shanghai-up-to-date-directory-1942/page/n381/mode/1up)

52 个窗洞中，44 个朝向胶州路，8 个位于南端墙。模型保留主门石翼与雨篷、并窗共用的双层窗台、墙内嵌红饰带、南端窄单光窗、分级挑檐及升高的转角方台。门轴二层宽窗为三光，三、四层为四光。南端上部延伸到第三列可辨窗，底层回墙止于第一列。北侧三层 N3 右窗一带被树木和电箱遮住，模型在此保留截面。后部屋盖、院内其他建筑及树篱后的下窗台高度缺少完整实测。[窗洞表](measurements/west-front-openings.json) · [南端墙测读](measurements/southern-endwall-photo-registration.json) · [北窗取舍依据](measurements/north-third-storey-source-limits.json)

模型采用米制局部坐标。X 轴沿西墙指向东南，Y 轴向院内，Z 轴由街面向上。南端底层双窗楣中心连线中点为平面原点，窗心距约 1.406 米。八个西侧机位的 21 个同名点共形成 52 次观测，重投影误差中位数 1.43 像素，最大 9.09 像素。南角方台顶高约 19.05 米，普通女儿墙顶约 18.26–18.52 米。玻璃后退量、受遮端部和薄构件厚度均为影像估计。[西立面标定](measurements/west-courtyard-camera-registration.json) · [上层窗与屋沿](measurements/west-upper-photo-registration.json)

现有 2429 号轮廓的临街交线长约 31.35 米。北端可见窗越出旧轮廓约 0.84–2.79 米，南端实边在旧轮廓内约 4.18 米。两个端部和街面方向的独立观测支持院内这栋楼的定位，市级表格只登记地址。模型沿照片定位线建造。[底图对照](measurements/mapped-outline-and-photo-frontage.json) · [院内楼栋定位](measurements/courtyard-building-registration.json)

从仓库根运行以下命令可以重建近景、远景及材质和窗洞检查。依赖沿用上海项目的建模工具链。

```bash
model=projects/shanghai/source/precise/jingan-postal-supply-office-jiaozhou-road
out=postal-output
mkdir -p "$out"
python "$model/source/build_model.py" --output "$out/postal-full.glb"
python "$model/source/build_model.py" --lod --output "$out/postal-lod.glb"
python "$model/measurements/verify_postal_projection.py"
python "$model/measurements/check_postal_courtyard.py" "$out/postal-full.glb" "$out/postal-sections.json"
```
