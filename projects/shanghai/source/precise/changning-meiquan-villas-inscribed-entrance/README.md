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
