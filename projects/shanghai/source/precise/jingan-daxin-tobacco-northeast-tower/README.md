# 观渡庐东北砖塔与短翼成对拱窗

北京西路1094弄2号登记为第四批上海市优秀历史建筑4B005。市表原名称为「大新烟草公司」，现名称为「上海电筒厂职工宿舍」。院内的上海市人民政府铭牌将其记作「约1910年建」。观渡庐南立面的西端是陡坡人字山墙，东端收于一座六边形红砖塔；主入口位于东侧。模型取东北塔和转到东端后紧邻的两扇大拱窗。东侧主门、其余南立面、西山墙与院内另列。[上海市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [静安区档案局实物与历史资料](https://www.jingan.gov.cn/rmtzx/003001/20200612/cc3f0c82-e6bc-4032-9ec1-41e506f16826.html)

沿南立面向东走，塔上的封闭双拱砖饰和有窗的墙面依次转出。再转到东侧，可见灰色围边下的圆拱窗、下一层的高窗，以及短翼中间并排的两扇分格拱窗。2017年8月的修缮照片有脚手架遮挡，上海パンダ2018年7月的两张照片可分别核对长立面和东端墙，静安区档案局的照片另补了转角方向。2022年刊出的街角照还显示，同一层的实窗和盲拱在相邻面上交替。各照片的作者、来源、拍摄或发表时间和用途存入索引。砖材、玻璃、窗帘和灰色围边独立制作。[2017年署名原照](https://commons.wikimedia.org/wiki/File:北京西路1094弄2号.jpg) · [2018年两向图](https://shanghaiimayou.blog.fc2.com/blog-entry-363.html) · [2022年街角照](https://www.sohu.com/a/614897585_99917329) · [来源与署名](reference-review.json)

临园长边按登记足印约38.77米。正面照片给出的塔宽估计约5.94至7.79米。以首道腰线高4.30米为假设，把三张照片上48个角点共同拟合到六边塔身，得到约3.28米的外接半径和约17.16米的围边顶高。把东端两道窗拱反投到估计的端墙平面，窗中心分别在塔轴西北约4.94和8.37米。窗外的截断线位于9.98米处。照片分辨率、斜视和楼基遮挡会影响这些估值。[三张照片逐点对照](measurements/three-camera-fit.json) · [塔轴位置和短翼范围](measurements/footprint-and-scale.json) · [重算尺寸](measurements/measure_hexagon.py)

近景单独做了放射状拱砖、后退的玻璃与窗格、封闭双盲拱后方的砖面、外挑托齿和灰围边内的低平屋面。首层格栅、短翼窗下空调机和雨管按照片里可辨的位置制作。近景有21,500个三角形，远景有13,116个，Blender源模型按183个具名部件组组织。模型几何及原创贴图采用仓库的MIT许可。[窗头、玻璃与格栅](source/brickwork.py) · [六边砖塔](source/tower.py) · [成对拱窗与短翼](source/east_wing.py) · [几何实测](../../../data/audit/daxin-tobacco-northeast-tower-v1/preflight/geometry-rays.json)

在上海项目目录运行 `python source/precise/jingan-daxin-tobacco-northeast-tower/source/build_model.py --out 输出目录 --audit 检查目录 --decoded 解码目录` 可生成网格、两档网页模型、可编辑Blender文件和预览。可用 `--blender`、`--gltfpack`、`--oidn` 指定工具路径。[制作入口](source/build_model.py) · [地图地块、邻楼和保留的旧主屋](../../../data/audit/daxin-tobacco-northeast-tower-v1/placement-notes.md)
