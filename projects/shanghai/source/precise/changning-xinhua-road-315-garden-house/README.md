# 新华路315号花园住宅

花园一侧前凸的山墙以深色露明木构架分格，底层三扇高窗开在红砖墙上，旁边的起居室通过窄阳台面向草坪。北侧从新华路能看到两道进深不同的山墙。模型复原主屋及相连的北翼，按冻结城市地块校准长边约30.42米，位置和坡顶高度保留估算性质。[位置与屋面图像记录](site-and-roof.json) · [打开独立模型](../../../xinhua-road-315.html)

市房屋管理局第二批优秀历史建筑以2M002登记此住宅，使用单位栏为市一商局疗养院。1994年市政府中英文保护牌记1930年竣工，2013年文章正文写1948年，2026年市英文文旅页写1949年。原始竣工档案仍待查。市英文文旅页记2023年经过整体修缮。[市级登记表](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [2013年现场牌照和两层平面](https://blog.sina.cn/dpool/blog/s/blog_55c85ddb0101gng8.html) · [市英文文旅页](https://english.shanghai.gov.cn/en-CityTour/20260303/b8a10d5e27664c69bb294479704a91b9.html)

南面按照2024年10月发布的实照塑形。东段底层以一个宽的弧券承托二层露台，中央有玻璃门和浅挑檐。2026年文旅页所配照片中，同一端为白墙和两扇方窗，中段下方亦有不同的外挑构件。两文没有给出各自的拍摄日期，尚不能将这两种外观依次对应到修缮前后。2009年12月6日的具日期街照可辨北侧两道山墙和独立门房。北庭院窗墙另以2013年和2024年发布的照片交叉核对。屋面的三处花园侧棚式老虎窗、明瓦脊、穿屋烟囱及街面伸翼与影像相符。[2009年新华路街照](https://commons.wikimedia.org/wiki/File:A_picture_from_China_every_day_199.jpg) · [实照与外观说明](https://www.thepaper.cn/newsDetail_forward_28954961) · [带来源及散列的图像清单](reference-review.json)

门房、花园围墙、院内其他建筑、室内和隐蔽构造留作后续。东西端的窗洞位置、檐口高度和梁架尺度按可见照片及平面图估计。材料和网格为原创，照片没有放入分发的文件。[冻结底图和独立原体范围](footprint-review.json)

## 重建

从上海项目目录运行。需要 Python、NumPy、Shapely 2.1、Blender、gltfpack、Open Image Denoise 和项目的 Node 环境。三档模型及可编辑 Blender 文件均由同一份几何源码生成。

```sh
python -B source/precise/changning-xinhua-road-315-garden-house/source/build_model.py \
  --out assets/models/candidates/changning-xinhua-road-315-garden-house \
  --audit data/audit/xinhua-road-315-garden-house-v1 \
  --decoded /tmp/xinhua-315-decoded
```

[几何与材质源码](source/garden_house.py) · [下载清单](../../../assets/models/candidates/changning-xinhua-road-315-garden-house/manifest.json) · [模型审计](../../../data/audit/xinhua-road-315-garden-house-v1/README.md)
