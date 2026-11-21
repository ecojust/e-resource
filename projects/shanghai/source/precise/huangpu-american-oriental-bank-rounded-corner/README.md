# 上海美丰银行的弧形转角

河南中路521–529号、宁波路180号在上海市优秀历史建筑名录中列为4A013，原名美丰银行，现名美丰大楼，又称强农大楼。邬达克在克利洋行任职时参与设计。上海黄浦的报道将这座四层建筑列为其1920年作品，资料中的建设时间范围为1918–1924年。[上海市房屋管理局名录](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [上海黄浦报道与照片](https://www.thepaper.cn/newsDetail_forward_22089072)

## 制作范围

转角中央的宽窗、左右各两道窄窗以及接入两条街的直墙，共形成七条窗轴。模型包含首层三联入口、台阶、宁波路侧店额、两层砖墩、钢窗、外机、落水管及顶层的弧形女儿墙。照片中的中央木牌可辨「老□老香」，几何根据可见笔画概括。门面和外机以2023年区报照片为准。2015年另有可核对的上层外机和店面招牌。2025年银行文章刊出的首图与2023年为同一画面。[2015年独立照片](https://commons.wikimedia.org/wiki/File:Former_American_Oriental_Banking_Corporation_Building.JPG) · [上海银行博物馆文章](https://www.sohu.com/a/859038403_121124391)

模型按两条街线和四个弧线节点拟合，转角半径约7.91米，街角弧长约13.56米。两期照片共同约束七条轴线的位置，受拍摄角度影响，两侧直墙的第一扇窗误差较大。屋顶部位由155个照片线点、4条竖边和原足印约束，常规女儿墙约14.90米，中央抬高处约15.14米。两项合理区间分别为14.40–15.74米和14.63–15.99米。建筑切至街面向内1.50米，内侧返边、洞口深度和未见的构件背面均为估计。[平面注册](source/frontage-registration.json) · [双照片窗轴](source/window-registration.json) · [高程拟合](source/height-registration.json)

## 复建

从本目录运行以下命令。通用打包器将原始网格、两档网页模型、可编辑 Blender 工程和预览写入指定目录。

```sh
python source/build_model.py --out /tmp/meifeng-model --audit /tmp/meifeng-review
```

几何和砖纹为项目原创。店额「老鸿兴」使用随源文件提供的 Noto Sans CJK 子集，许可为 SIL OFL 1.1。[字形许可](source/shop-letters-OFL.txt) · [建筑及影像来源](reference-review.json)
