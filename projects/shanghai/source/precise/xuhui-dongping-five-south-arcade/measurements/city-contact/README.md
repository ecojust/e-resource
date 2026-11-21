# 东平路5号南廊与原城楼体对照

在上海项目目录用 Python 3、NumPy、Shapely 2 及支持 module.registerHooks 的 Node.js 执行下列命令。程序核对本地模型与底图。缺少相应文件时从 signed-files.json 的固定公开提交取回，再校验 SHA-256。

```sh
python source/precise/xuhui-dongping-five-south-arcade/measurements/city-contact/measure.py --project . --output dongping-contact.json
```

东平路南侧、花砖庭院以北的主楼对应 OpenStreetMap 674362974 和城市模型4267。2023年刊出的立面照可辨中央券洞、红阶和花砖，俯视图显示有关房间位于东半侧前缘。两幅俯视影像及立面照片的出处和量测见上级目录 courtyard-paving.json。以20级影像的白色檐带、其南侧最外可见边和二者中部各试一处，用11个开间横坐标、14个高度比较实际射线。三处位置都要保留原主体。输入的原近景同瓦片还有七户，远景能用 feature id 单独选中4267；侧边和楼壳高出的部分也列入比较。原照片、卫星图及提供商瓦片按来源权属查阅。
