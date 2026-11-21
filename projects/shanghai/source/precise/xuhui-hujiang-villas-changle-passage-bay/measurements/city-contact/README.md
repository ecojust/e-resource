# 原城楼壳与交付模型测量

在上海项目目录中运行以下命令，使用 Python 3、NumPy、Shapely 2、Pillow 及支持 `module.registerHooks` 的 Node.js。程序从本地项目读取 Three.js 和加载器，优先采用库内已核散列的模型，缺失时按 signed-files.json 从固定提交取回并复查。

```sh
python source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact/measure.py --project . --output replay-352.json
```

将 levels 下三份投影、两个档位的每组12个截面和六条通行线与公开报告对应栏逐项比较。街道坐标来自 OpenStreetMap contributors，适用 ODbL，原图仍由各摄影者保有。运行时间与子进程号由每次实跑单独产生。
