# 世界书局福州路立面与外文书店店面

福州路390号世界书局旧址列入上海市第五批优秀历史建筑，编号黄浦区5A048。本件主要依据2015年4月4日外文书店街景，参考2016年3月17日登记照片建模。沿街共五跨，上部五排，每排18个窗洞。五跨分别开四、三、五、三、三个洞口，下扇合计150扇。照片中向外开的五片扇框分别围绕自己的铰轴转出。建筑前方的四尊人物石像沿原照的轮廓与手臂位置起形，第二尊上身受树枝遮挡，其背部、石像体厚与手臂横断面为估计。

石像下方的黑色窗楣、底层橱窗和中间入口与上方办公窗同属临街面。中间黑楣上可读出三组草写金属笔形，右侧被树枝遮住，只按可见部分立体描绘。2015年画面中的斜玻璃雨篷为当次店面状态。模型保留树和电线遮挡处的资料说明。立面后方的楼层、内部书架和毗邻墙面未获足够观测。来源、材料范围和可供复查的照片列于 [照片与许可](SOURCES-LICENSE.md)。

四片浅色窗裙的可读卧缝、竖缝和收边分别建模，重复部位沿同一墙段铺排。深红面砖以长砖行和长短砖混合行交替，灰缝底色较砖身浅，448像素的原创材质按横向1.664米、纵向2.128米循环。原宏观城市中，具名商户落在3000号既有建筑，OSM轮廓交并比约0.978。其福州路侧边长26.492米。整个模型在独立查看页展示，原城地块维持原数据。详细依据见 [原地块复核](measurements/footprint-review.json)。

## 从源码重建

在仓库的 projects/shanghai 目录中运行。构建需仓库的建筑模型工具、Python环境和 Blender。查看下列程序的帮助可使用同一工具打包压缩网页模型与可编辑文件。

```sh
python source/precise/huangpu-world-book-company-fuzhou-front/source/paint.py
python source/precise/huangpu-world-book-company-fuzhou-front/source/build_model.py --output /tmp/bookshop-full.glb
python source/precise/huangpu-world-book-company-fuzhou-front/source/build_model.py --lod --output /tmp/bookshop-low.glb
python source/precise/huangpu-world-book-company-fuzhou-front/source/build_model.py --help
```

结构和表面着色程序读取同目录的 measurements 资料。复验程序位于 data/audit/world-book-company-fuzhou-front-v1。verify-export.py 对原网与两个实解码网检验店窗、雨篷、石像、门洞和可见字迹。verify-render-uv.py 对嵌入的原创贴图逐三角核实米制纹理坐标。
