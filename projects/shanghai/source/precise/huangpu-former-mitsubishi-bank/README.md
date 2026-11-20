# 九江路36号，原三菱银行南立面

市房管局第二批2A044登记为“中华邮政储金汇业局”。2024年市住建委、市历保中心介绍，这座银行由德和洋行设计，1934年始建，地上五层含夹层、地下一层。2015年1月的正面实拍与该文发出的历史照片、现楼照和门廊近照都可以辨认四巨柱、三段后退高窗与五级中央石阶。建筑文献另有1936年完工的记载。OSM六层标签与官方“含夹层”的叙述分别记录。[市政资料和实照](reference-review.json)

九江路36号最新OSM为w493784117@2，录有主门牌、原名和银行现名。原生宏区14-13720-6694的1993号源与其重合约99.10%。36号南侧贴九江路的轮廓边长约28.39米。街西50号建设银行的门牌点在88和2301号重叠轮廓；东端的228号源为外滩16号。Virtual Shanghai编号541的英文题头为Mitsubishi Bank，正文却写“三井銀行”及50 Kiukiang Road，该条目作为异名冲突保留。[源地块和六个同组地块](footprint-review.json) · [目录原页](https://www.virtualshanghai.net/Data/Buildings?ID=541)

临街面按2024报道近照的金色行名制作。2025年黄浦文博转载现场图上的行名已呈绿色。四根柱子包含层叠圆座、分段无凹槽柱身、颈部珠饰、卷涡与叶饰。三段深窗、中央门、两端长窗、五级石阶与卧狮均独立建模。门牌小字未逐字辨认，只表现铭牌位置。柱头形制参考照片，立面绝对高度、柱身进深和卧狮造型为视觉估计。[主街墙](source/bank_front.py) · [巨柱与卧狮](source/bank_portico.py) · [照片估高与不确定性](elevation-estimate.json)

以项目正常工具从上海项目根目录构建。目录参数用于放置本次四件资产和独立核验文件。

    python -B source/precise/huangpu-former-mitsubishi-bank/source/build_model.py \
      --blender blender --gltfpack gltfpack --oidn oidnDenoise \
      --out /tmp/mitsubishi-assets --audit /tmp/mitsubishi-audit --decoded /tmp/mitsubishi-decoded

照片仅作造型参考。模型使用原创几何及材质，行名采用SIL OFL字体子集。[字体与授权](source/fonts/provenance.json)
