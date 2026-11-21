# 丽波花园南排1、2号分户阳台与原城两排住宅的实测

市表4D027登记衡山路300弄1–8号。院落东南侧照片同时可见两排房屋的檐角和1、2号阳台分界。沿用八个门牌、四个檐角和同一照片的六种焦距解，在原南排外缘向内0、0.5、0.9米的位置分别检验。近档使用旧城瓦片实际几何，远档按原3347的逐三角户号取出。北排2656、院内先前另建的343与南排独立对照。

在项目的 Shanghai 目录运行，需要 Python 3、NumPy、SciPy、Shapely 与支持 registerHooks 的 Node.js。

```sh
python -B source/precise/xuhui-libo-terrace-one-two-balconies/measurements/city-contact/measure.py --project . --output libo-terraces-result.json
```

脚本先按散列查本地模型与城图，缺少时读取 signed-files.json 所列固定 Git 版本。也可通过 `--source-cache DIRECTORY` 指定按同一表的键命名的原始下载。完整结果逐个给出旧墙和阳台到同一测试面的距离；各阶段进程号与运行时间随执行环境而变。正式坐标、逐档汇总和压缩的8,640条射线在本栋审计目录 preflight/south-and-north-terraces.json 及 two-terraces-376-rays.json.gz。原照通过上一级目录的来源索引查阅。
