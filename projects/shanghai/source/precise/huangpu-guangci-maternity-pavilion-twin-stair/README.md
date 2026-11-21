# 广慈医院原产科楼庭院立面与双梯门廊

旧广慈医院25舍原为产科病房，今为瑞金医院8号楼。楼前市政府铭牌记载建于1921年，医院2020年院史记为1922年建成。模型从庭院一侧看中央入口，七个窗轴从题名山花一直延伸到两旁的曲线山花。两跑石梯在侧面半平台转向，通往上层券门；下层深色木门设在平台正下方。[市政府铭牌现场照片](https://s15.sinaimg.cn/mw690/003216vszy7nKRVcWjs2e&690) · [院方建筑史](https://www.thepaper.cn/newsDetail_forward_7738435) · [1930年代旧照](https://commons.wikimedia.org/wiki/File:Sainte_Marie_Hospital_-_maternity_pavilion.jpg)

中央匾额的法文为 **MATERNITÉ**，末字母带重音。观察者面向山花，从左到右可见「慈」「科」「產」「廣」。原照还可辨出屋檐下四根成组的木托、灰绿相间的拼砖带、中央楼号和高窗的石梃。模型以独立几何表现这些构件，砖面使用程序生成的连续纹理。[2018年现场照片](https://blog.sina.com.cn/s/blog_a598306e0102yxe9.html) · [图像出处和文件校验](reference-review.json)

## 尺度和范围

同一天在庭院远近两个位置拍摄的照片，可用券门拱肩、阁楼窗、两层门和石栏柱帽对位。近照中券门宽约39皮砖。以每皮含灰缝约65毫米估算，券门净宽约2.53米，中央平台高约3.80米，题名山花最高点约16.7米。前两张照片的控制点单坐标均方根误差为1.28像素。绝对尺度、平台进深、屋面截深与受栏板遮挡的上段踏步数仍为估计。[双机位拟合](measurements/courtyard-camera-fit.json) · [立面观测点](measurements/courtyard-elevation-picks.json)

上海市第四批优秀历史建筑名录在今名栏列“8号楼、3号楼”，在地址栏列“8号楼、9号楼”。本件只对应院史可以辨认的原产科楼。两翼其余开间、背立面和内部分隔留待后续资料。校园地块和整院地址不能确定这栋楼的城市模型归属。[市房管局原表](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [建筑院史](https://www.sohu.com/a/190181698_375956)

2018年正面照片可见山花前方狭窄的瓦檐，侧照可见曲线山花后方的瓦垄转向主坡。模型在中央题名和左右曲线山花背后分别接入两片交坡，保留前檐、窗台和汇入主坡的斜沟。背坡交点的深度按可见檐线估计。[2018年正面和斜面实照](https://blog.sina.com.cn/s/blog_a598306e0102yxe9.html)

## 源文件

执行 `python source/generate_brick.py` 可重制砖面图案。模型生成入口为 `source/build_model.py`，支持项目既有的 GLB、Blender、网格解码和预览导出参数。石阶、石瓶栏杆、窗框、双语浮雕和木托都保留独立构件组。[生成程序](source/build_model.py) · [浮雕字形来源和许可](source/lettering/provenance.json)
