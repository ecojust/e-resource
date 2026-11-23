# 福州路89号中兴银行前楼

上海市第四批优秀历史建筑名录第4A022项登记为中兴银行，现名栏为申达大楼、上海市机电设计研究院。Virtual Shanghai 的建筑记录把 China Banking Corporation 列在 89 Foochow Road。东北转角连接今天的福州路与四川中路。福州路89号的门与窗位于直街墙上，照片中另见四川中路149号出入口。两门均在三条圆弧窗轴之外。[上海市房屋管理局名录](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [Virtual Shanghai 建筑档案556](https://www.virtualshanghai.net/Data/Buildings?ID=556)

门侧的上海市人民政府挂牌写明前楼1927年建、后楼1934年建、顶层曾加建。2011年孙玫的修缮论文摘要记前楼六层，平面呈L形，后楼原为仓库。高参88在2015年刊出的第2张照片可放大核对挂牌；文章正文另写1929年，本文对楼体年代采用挂牌的分期。[挂牌照片与两条街的立面](https://blog.sina.com.cn/s/blog_5d1bdf480102vf2v.html) · [修缮论文摘要](https://www.zhangqiaokeyan.com/academic-journal-cn_urban-construction-theory-research-electronic-edition_thesis/0201237354529.html)

## 1948年街廓

1948年上海航片1C原张为14,783×10,446像素。先用北京东路、滇池路、南京东路、九江路及汉口路上的九个交叉点配准，再留出福州路与四川中路的路心独立对照。路心预测离原图上读到的路心39像素。原生裁片可辨路口西南角的L形屋盖，两条临街檐线在东北角转圆。这里可以核实1948年的建筑位置和屋盖轮廓，街面窗扇及门牌仍须由街照核认。配准、道路节点、误差和五个屋边点见 historical-parcel.json。已查的1937年四川路133号图、早于前楼的福州路图和福州路451号图分列在 references.json，本次未取得足以认定为同楼的战前平视立面照。[1948年航片1C](https://archive.org/details/1948-shanghai-aerial-map-1-c-bund-and-hongkew) · [OpenStreetMap 路口资料](https://www.openstreetmap.org/node/103788196)

## 三组窗与门牌

Livelikerw 于2015年2月6日拍摄的路口原片保留两路的街名牌和六层街墙。从基座往上，可读三处带铁栏的大窗、二至五层每轴两扇的高窗、上部托臂挑檐和顶层的较矮成对窗。以原片宽4,912像素等比例缩到840像素，分别取三条窗轴上14个高度边界，共42点。五个独立街廓节点确定13.05米的原模型弧长和约9.73米半径。按真实24毫米等效焦距反算，保留三轴等距且各层共享高程时，点位的中位误差为1.62个工作像素。地坪、部分底窗下缘受行人和车辆遮挡，米制窗高是受尺度和相机位置约束的估计。圆弧外另取福州路直段正对门的十个位置，包含89号门牌、门洞和两层窗间墙，详见 entrance-controls.json。[Livelikerw 原片，CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:Former_Zhong-Xing_Bank_Building.JPG) · [福州路直段及89号门](https://www.sohu.com/a/601433736_121123673)

高参88图1提供另一视角，又读出42点。保持原模型层高，分别独立拟合两个相机，两个机位的边界误差中位数为4.27与3.41像素，最大21.47与19.76像素。第一张照片推定的高程固定后，第二机位的中位误差降至1.68像素。第二相机缺少EXIF，可拟合出不止一种合理焦距与站距，绝对层高尚缺独立测距。底层窗头、台基上口及第五层深檐下的边界尤其值得保留原读数。[高参88图1](https://blog.sina.com.cn/s/blog_5d1bdf480102vf2v.html)

## 与发行模型的比对

原档与网页近档各20,556三角面，远档12,600面。逐档读取解码三角面，在相同高度、相同弧长位置命中真实面。两侧点间直弦到中央面差分别是1.848、1.848、1.855米。三档各有48/48束命中预期的基座玻璃、楼上两扇玻璃和实心窗间墙。在2015年原片另读33个窗内样点，按原模型的固定层高反算相机，各档均有32束落在玻璃、1束落在第六层真横梃。另用第一张照片单独推出高程的机位去投原模型，每档是16玻璃、6金属、11石面。两组结果均在 mesh-comparison.json 中，可复核绝对高程和相机位置的耦合。现有圆弧和三轴开窗有真实几何，此次保留发行模型字节。[拍摄原片与授权](https://commons.wikimedia.org/wiki/File:Former_Zhong-Xing_Bank_Building.JPG)

## 下载与复算

公开附件包括图片来源记录和散列、逐点像素、原始拟合及误差，不含受限照片像素。measure_corner.py 取 Commons 原片和本栋 source/frontage-registration.json。check_photograph_mesh.py 取项目根目录、第一次配准 JSON 和可写的解码目录，逐项检查发行清单并调用项目自带 meshopt 解码器。check_second_station.py 取高参88图1、第一次配准 JSON 及三档比对 JSON。register_aerial.py 取记录中的 OSM 地图 XML。四个脚本均有 --help。
