# 多伦路59号鸿德堂北门石狮

市房管局第二批名录2F003号登记鸿德堂，具名OSM建筑为w1085786138。模型对应宏块14-13720-6692内的2557号建筑。临多伦路的北门向外方位约5.57°。上海虹口2024年11月24日的报道记载，教堂于1928年10月7日举行献堂典礼，门口设有一对石狮。报道所述建筑沿革与现存石雕的雕刻年代分开记录。[登记表159行](../municipal-heritage-register-2026-11-20/register.json) · [史料及方位核对](../../../source/precise/hongkou-hongde-church/revisions/entrance-guardians/reference-review.json) · [上海虹口原文](https://www.163.com/dy/article/JHPI11570514A3B5.html)

Livelikerw在2014年12月9日拍摄的日间原片、Windmemories在2024年1月7日拍摄的夜景，均显示两只石狮分立中央门阶两侧。照片可以辨认前爪、短吻、鬃卷、胸前束带和西侧石狮爪下的球状物。原版已做台阶、石拱门和两座石台。新增石雕分别在各自0.66×0.65米的原石台上，实读近景顶点的尺寸为宽0.524米、深0.576米、高0.846米。爪下支承向石台嵌入约3毫米，最高点在本地标高1.703米处。中央通道、原占地和原导航点继续沿用。[日间照片](https://commons.wikimedia.org/wiki/File:Fitch_Memorial_Church_Shanghai.JPG) · [夜间照片](https://commons.wikimedia.org/wiki/File:20240107_Hongde_Tang_Christian_Church_on_Duolun_Road.jpg) · [原石台与方位](../../../source/precise/hongkou-hongde-church/revisions/entrance-guardians/baseline.json)

同一门口镜头下，原版两座石台为空，修订版可分别看到东、西两只坐狮。Chromium分别读取原版和修订版近、远文件，核对实际获取的字节数、SHA-256和绘制面数。在816×624画面内比较同档前后图，RGB任一通道差值超过6的像素均位于两个石台上方。近景东侧6,840像素、西侧6,809像素发生变化，远景两侧分别6,724和6,729像素。两档中央门阶对照带内的差异数均为零。全楼视角中石狮很小，近距离图可查看卷鬃、脚趾与胸带。[门口原版](webgl-before-full-door.png) · [门口修订版](webgl-after-full-door.png) · [东侧石狮](webgl-after-full-east-lion.png) · [修订版远景资产的门口](webgl-after-lod-door.png) · [修订版全楼](webgl-after-full-whole.png) · [逐张比较](visual-review.json) · [浏览器加载记录](isolated-browser.json)

原始文件与网页近景由378,504面增至441,648面，网页远景由178,968面增至192,592面。读取三档各25个既有绘制单元，核对原顶点和索引数据、材质、访问器与缓冲区字节。原始、近景、远景分别保留27,090,648、10,602,816与5,196,344字节的原二进制数据。每档28组前后成对射线分别复验雕像、原石座、门阶及主体，三档共168次投射。Blender重新打开原件和修订件，逐一核对原5个对象的名称、类型及世界坐标矩阵，原2个网格的几何签名相同。两只雕像共新增8个独立可编辑网格。[分档网格与射线](geometry-revision.json) · [原生逐对象复验](native-object-signatures.json) · [原生重开](native-meshes.json) · [四件成品清单](../../../source/precise/hongkou-hongde-church/revisions/entrance-guardians/manifest.json)

登记脚本在独立的171处城市快照上运行两遍，每遍都重新执行核验。5份普通建筑名录的第二次结果逐字节相同，另39项普通地标保持原记录。鸿德堂沿用原ID、坐标、导航、源地块与邻楼范围。正式前后城市版本另行绑定。[登记程序](register-revision.py) · [重复登记复验](registration-rehearsal.json)

在紧接清心堂的正式父版本上复跑后，城市仍收录176处。独立读取新版本893个已签文件，核对鸿德堂原名、原坐标、选中导航与近远距离等15项；其余普通地标逐项相同。城市候选目录签名两版均为 `f55d1876…`，普通建筑索引指向新四件文件。[正式输入](production-snapshot.json) · [893项逐份复读](production-replay.json)

### 正式城市地图的修订前后对照

两版全城目录均有176处地点。桌面从原有“鸿德堂 · 多伦路59号”条目点击“进入漫游”，390×844手机从同一条目触摸进入。原版北门两座石台为空，修订版中两只坐狮位于门阶两侧。北面受光偏暗，东、西近照仍能辨出卷鬃、前足、胸带与原石座边缘。正面同机位的中央踏步检查区共10,208像素，所有颜色通道逐像素相同。两版真实远景分别载入178,968和192,592面。[原北门](city-24139/before/both-guardians-street.png) · [两只坐狮](city-24139/after/both-guardians-street.png) · [东侧近照](city-24139/after/east-guardian-street.png) · [西侧近照](city-24139/after/west-guardian-street.png) · [同机位像素复核](city-24139/city-pair-pixels.json)

从手机会话直接将视口改为桌面宽度，场景一度贴在画面左侧。独立打开1100×744桌面窗口，再次从正常目录点击进入，北门与两翼居中，背景可见邻楼简化体块。原版与修订版的原始GLB、网页近景、网页远景和Blender文件均从相应正式站点下载并校验，四件合计分别为82,899,192和60,111,427字节。首次基准场景出现14项基础资源请求失败，恢复后两站逐件校验48个公开地址，再跑完整城市前后对照，两次均无同源HTTP或页面错误。[独立桌面](city-24139/desktop-fresh/north-entrance-desktop-fresh.png) · [手机](city-24139/after/north-entrance-phone.png) · [同页改宽对照](city-24139/after/north-entrance-walk.png) · [逐图审查](city-24139/city-visual-review.json) · [八件下载](city-24139/updated-entry-and-downloads.json) · [初次记录](city-24139/first-load/ordinary-map.json) · [资源恢复](city-24139/restored-http.json) · [两版城市签名](city-24139/signed-maps.json)
