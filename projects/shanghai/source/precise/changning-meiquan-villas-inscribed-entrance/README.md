# 新华路593弄梅泉别墅东北入口

上海市优秀历史建筑第三批 3M018，名录地址为新华路593弄。20幢住宅从1933年起由吴其达出资、奚福泉设计，李顺记营造厂施工，1935年建成。这里制作具名东北入口和相接的一段公共围栏。门柱、栏杆和灯球的初造年份尚无实证。[上海长宁历史资料](http://sh.people.com.cn/n2/2021/1004/c134768-34943565.html) · [房管局原名录](http://fgj.sh.gov.cn/yxlsjz/20210922/bc5957926d80432b8bea0157eb16bb94.html)

模型保存2013年和2015年街站所见的两座球灯、敞开的两扇铁门、左侧行人门，以及四块逐字建模的「梅泉別墅」石牌。照片中的窗户、附近住宅以及另一入口需要逐栋归属，暂处于本件范围之外。2020年2月照片中两扇门已关闭、柱头出现浅色压顶，同时保留两期度量，供校核时区别。[摄影站与逐点读数](measurements/gate-survey.json) · [两期独立报道中的入口](https://m.thepaper.cn/baijiahao_8356585)

## 重建

在具备 NumPy、SciPy、Shapely 2.1 和 Pillow 的项目环境中运行以下命令。

```sh
python measurements/fit_gate.py measurements/gate-cameras.json
python measurements/make_gate_cameras.py
python measurements/check_mesh.py /tmp/meiquan-gate
```

## 七个实景摄影站与尺度

五处2013年至2020年的街站共同定位两根方柱，相距4.64米、柱宽约0.75米；取刻名柱临街面中心脚为局部原点。向右指向真方位284.89°。两处朝外的2015年2月弄内反打用于独立检查折开门扇的端点和园沿返栏。返栏第一根矮砖柱顶约在局部坐标(0.75, 4.81, 1.60)米。砖横缝由三张不同照片独立量得每皮约0.117、0.124与0.127米，程序纹理采用0.125米。[街面多站联合解](measurements/gate-cameras.json) · [反向交会](measurements/gate-return-sections.json) · [砖缝逐行测读](measurements/brick-course-readings.json)

首版已包含四块刻名和实际贯入的凹槽。细化版增加园沿砖基返栏与转角小柱、铁门铰轴、石牌固定件、原创砖面与石面两组色纹和法线，并根据弄内照片修正两扇门的开启角和上缘。三档模型的40个留验位置均在原帧4像素范围内出现预期构件或透空，33处直接命中。原近远场景与新物件的实际三角投影均无交叠，最近原户为1187，边缘净距约4.67米。[实射程序](measurements/check_gate_views.py) · [邻屋与平面测量](measurements/gate-original-city-clearance.json)

重建程序纹理、复算弄内朝外的两个摄站、生成三张原视角模型图及一张合图，分别运行以下命令。

```sh
python source/gate_finishes.py
python measurements/fit_inside.py measurements/gate-return-sections.json
python measurements/check_gate_views.py /tmp/meiquan-gate/full-source.glb /tmp/meiquan-gate/controls.json
python measurements/check_nine_cameras.py /tmp/meiquan-gate/full-source.glb /tmp/meiquan-gate/frames.json
python measurements/render_gate_views.py /tmp/meiquan-gate/full-source.glb /tmp/meiquan-gate/views --width 512
```

[独立模型页与下载](../../../meiquan-villas-inscribed-entrance.html)
