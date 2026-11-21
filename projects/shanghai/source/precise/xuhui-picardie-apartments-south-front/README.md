# 毕卡迪公寓南向阶梯塔楼与534号入口

从衡山路534号的南花园望向酒店，两列内凹阳台夹着中央竖窗向上延伸，深米色外墙逐级退到顶部，楼脚则是黑色方砖。2023年修缮恢复了阶梯轮廓，拆除了入口雨篷外柱，并将悬挑雨篷从历史一层位置提高到二层。模型按修后外观制作，中央双扇木门与两侧窄门之间悬着门灯。雨篷上方较短的横栏有三个开口，中间宽、两侧窄；从篷下可以看到朝挑出方向排列的三列凹格。[查看可旋转模型](../../../picardie-apartments.html) · [上海市住建委发布的修前与修后照片](https://m.thepaper.cn/newsDetail_forward_23041937)

市房管局第二批名录2D022的原名为「毕卡迪公寓」，登记现名为「衡山宾馆」。资料中另有「比卡迪」「毕卡第」写法。历史资料记1934年建成和中塔十五层，工作名录记1935年及十四层。两者均保留。2011、2013和2018年的街景反映了修复前一段时期的外形，后加的肩部轮廓与2023年照片有明显区别。[市房管局原始名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [旧照与历史资料](https://m.thepaper.cn/newsDetail_forward_13742318) · [1935年版面及其他历史图像](https://m.thepaper.cn/newsDetail_forward_8172196) · [逐件图像出处与哈希](reference-review.json)

原生底图将约4953平方米的主楼及后部合为一个地块。酒店及入口的两个具名坐标均落在地块内。南边约39.81米，朝向真方位181.47°。两期航片中雨篷相对边线的位置存在约2米差异，采用距中点偏西约4米的轴线。模型截取南边中段约31米宽、进深约4.4米的外立面。檐高、窗距、阳台进深、雨篷挑出距离与单元尺寸依据照片比例估算。街翼余段、行政楼、后部院落、地库及室内留待另行研究。[地块与邻楼](footprint-review.json) · [三期航片及定位参数](roof-registration.json)

Blender中可分别编辑阳台板、栏杆、门窗、竖向壁柱、黑砖勾缝、门灯、雨篷格栅和栏板。近景保留细窗框和密排栏杆，远景保留通透阳台、完整的阶梯体量和雨篷下空间。几何与材质为原创，未嵌入照片或第三方模型。[模型参数](source/parameters.json) · [参数化几何](source/south_front.py)

在上海项目目录执行以下命令。工具包括 Python、NumPy、Shapely、Node.js、Blender、gltfpack、Open Image Denoise 与 ImageMagick。

```sh
python source/precise/xuhui-picardie-apartments-south-front/source/build_model.py \
  --out assets/models/candidates/xuhui-picardie-apartments-south-front \
  --audit data/audit/picardie-apartments-v1 \
  --decoded /tmp/picardie-apartments-decoded
```

[近景](../../../assets/models/candidates/xuhui-picardie-apartments-south-front/xuhui-picardie-apartments-south-front-web.glb) · [远景](../../../assets/models/candidates/xuhui-picardie-apartments-south-front/xuhui-picardie-apartments-south-front-lod.glb) · [无压缩GLB](../../../assets/models/candidates/xuhui-picardie-apartments-south-front/xuhui-picardie-apartments-south-front-raw.glb) · [可编辑Blender工程](../../../assets/models/candidates/xuhui-picardie-apartments-south-front/xuhui-picardie-apartments-south-front.blend)
