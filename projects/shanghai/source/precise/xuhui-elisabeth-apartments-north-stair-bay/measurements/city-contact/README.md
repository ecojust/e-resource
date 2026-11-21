# 原城楼壳与交付模型测量

在上海项目目录中运行以下命令，使用 Python 3、NumPy、Shapely 2、Pillow 及支持 `module.registerHooks` 的 Node.js。程序从本地项目读取 Three.js 和加载器，优先采用库内已核散列的模型，缺失时按 signed-files.json 从固定提交取回并复查。

```sh
python source/precise/xuhui-elisabeth-apartments-north-stair-bay/measurements/city-contact/measure.py --project . --output replay-360.json
```

将 results.near 和 results.far 的全部169对射线与公开报告相应两栏逐项比较。运行时间与子进程号由每次实跑单独产生。
