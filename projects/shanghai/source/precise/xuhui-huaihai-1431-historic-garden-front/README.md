# 淮海中路1431号巴塞住宅历史花园立面

上海市第二批优秀历史建筑名录2D006登记淮海中路1431号花园住宅。首任业主之女 Georgette Basset McCann 向江似虹回忆，父亲 Lucien Basset 请义品洋行建筑师在霞飞路955号建造此屋，1921年迁入，1931年迁出。东方网另有奥古斯丁会建屋的叙述。里昂街景档案记载1936年此处为西班牙领事馆、1939年曾作法国商务参赞住宅。邻近1469号另列2D007。[市房管局原表](https://fgj.sh.gov.cn/yxlsjzcs/20200331/30c648cb811f401192bb61dd1dd487c9.html) [家族口述出处与两种记载](reference-review.json) [里昂街景档案77](https://www.virtualshanghai.net/Photos/Images?ID=77)

独立展件采用里昂 Virtual Shanghai 私人收藏的花园全景和近仰视照片。目录估年为1920至1939年，结合建筑建成年，展件年代取约1921至1939年。两张照片可互相核对中央弧形柱廊、阶石和石栏。另一幅雪景补足枝叶遮挡处的两翼三联窗、瓦楞屋面、屋顶尖饰和两端的低附房。三张照片的确切拍摄年月均待考。[花园全景409](https://www.virtualshanghai.net/Photos/Images?ID=409) [柱廊近景410](https://www.virtualshanghai.net/Photos/Images?ID=410) [雪景原始图像指纹](reference-review.json)

模型包括中央四根独立圆柱与弧形露台、对称前翼、左端栏顶凸窗和右端折面玻璃房。左附房基座的小窗和柱头的细部纹样留待后续细化。形体深浅及米制比例依据照片估计。黑白影像能辨认墙面、玻璃和瓦的相对明暗，无法确定原色。主图的公开门牌街区点可打开独立展件；现代院落、侧后墙与室内陈设保留待考。[查看历史立面](../../../huaihai-1431-history.html) [下载四种文件](../../../assets/models/candidates/xuhui-huaihai-1431-historic-garden-front/manifest.json) [建模与几何核验](../../../data/audit/huaihai-1431-historic-front-v1/README.md)

在项目的上海子目录下运行以下命令。重建使用 Python、NumPy、Shapely、Node、gltfpack、Blender、ImageMagick 7 及 Open Image Denoise。可执行文件支持通过命令行参数指定。原创网格依项目 MIT 许可发布，历史照片权利归原作者或收藏机构。

    python -B source/precise/xuhui-huaihai-1431-historic-garden-front/source/build_model.py --out /tmp/basset-model --audit /tmp/basset-review
