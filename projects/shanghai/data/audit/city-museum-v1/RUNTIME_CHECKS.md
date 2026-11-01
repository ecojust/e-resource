# 旧上海市博物馆江湾馆舍运行时增量检查

当前预检基线为 `93e3cb2d0ddeba1a7db7d435bf66c2f61492326e` 的80处目录（40处既有、40件候选）。本轮模型拟增加至81处、杨浦6处。

## 已执行

生产灯牌实现未改。[布局预检](beacon-capacity-preflight.json)使用队列中实际博物馆身份，在4视口将81个最长牌宽输入交给生产布局／命中函数；全部独立命中、无重叠或fallback。旧80条布局逐字段保持。最紧净区243×138像素沿用20×18编号格和12像素字，84格容量余3格。此为纯布局测试，未冒称真实地图投影、线上缓存、实际字形或原生触屏验收。

[当前目录35项灯牌／镜头测试](beacon-camera-preflight.tap)全部通过。[执行与输入绑定](runtime-preflight.json)保留该80处时点，最终81处结果将另写，不覆盖预检。

## 容量与历史行为

原全目录218行、容量224；容量阶段仅将生产容量常量扩大至288行，4×288 RGBA纹理18,432字节。[容量审查](runtime-capacity-review.json)保留变更时点，[预算实测](clipping-budget-preflight.json)将40件历史候选逐项元数据交给基线与当前真实clipper。旧218行13,952字节、顺序与owner完整一致，新尾行保持零。未读取历史GLB资产。

6种明确owner上下文（主场西源、东侧共享组、体育馆、泳馆、新馆8-owner组及逐顶点far）分别构造颜色／深度／距离材质，共18通道；有效负载完全相同，shader与cache key只差容量。[10项生产测试](clipping-budget-tests.tap)覆盖新225/288行、289行溢出拒绝及保持当前global/scoped纹理、owner过滤、延迟激活与释放重绑。

源候选主显示mask需保护连接的独立510/1262邻体，容量阶段候选主38行、独立1931门楼2行，当时预计新增40，总258；保护接口会留原主源少量边条，最终需实际构件包络和网页核验。不得将预测预算当作最终模型、源覆盖或像素验收。容量阶段未引入height clip字段；之后北侧修复另见下节。灯牌代码未改。

`global-integration-checks.mjs`在容量阶段只作语法检查；之后正式执行见下节。最终运行时另写runtime-checks，不覆盖初次runtime-preflight；浏览器画面由独立QA另验。

## 最终81目录检查

[最终运行时记录](runtime-checks.json)在正式四资产、定位合同、81处实际目录冻结后执行：7组集成检查及35项灯牌／镜头检查全部通过。博物馆主mask38行、独立门楼2行，另加北侧高位修复4行，全目录262／288；原218行13,952字节以及修复前258行16,512字节保持完全相同。真实8-owner near夹具只获得1860／1931的44行，排除这两owner的控制组为0行，颜色／深度／距离材质分别核验。该夹具不代替真实near几何与网页检查。

生产二维碰撞为1环105点；2个实体正点、54个空地负点、6片开放区与新模型碰撞无交集，均通过。向量源修正保留主1860约1.023006平方米接口，1931残量为0，并未错误声称两个源均零残留。

与独立小连廊的原生装饰投影接触仍按footprint记录：可能兼属的0—2米旧三角与新低位约0.244233／0.130974平方米相交，因共享接口缺少标签只是保守上界；高处原檐口也有XY投影接触。源足迹零交叠不等于全部原生构件零交叠，网页后侧与院部需实际观察。

用户本轮另要求README查看入口统一到主图，因此最初“全部旧audit/source不变”的旧范围断言不适用。最终只接受固定SHA报告列出的64份旧README及2个新说明文件，逐一从基线按唯一字面操作重放并核最终SHA；其他历史资产、源数据与审计文件保持，详见[runtime-scope-correction.json](runtime-scope-correction.json)。原预检与失败原因保留。


## 北侧高位旧源修复

原北侧两片1860屋顶悬在保留的1262上方。本轮追加独立`display_height_clips`，只交GPU，不进入二维向量源修正或地面碰撞。原主mask38行与门楼2行不变。高度28.705—30.11米按真实宏/near锚点换算，再写入Float32纹理；下界高于1262原屋顶约5毫米。[高度运行时检查](height-clipping-checks.json)保留实际262行、源变换矩阵和SHA绑定；[原始纹理](gpu-height-rows.f32)供独立全几何复核。

高段阶段28项聚焦JavaScript测试、14项Python构建测试通过，覆盖成对高度/参考点验证、非法输入原子拒绝、显示数组独立、隐藏撤销、构建透传与三类材质。实际北两片残留屋顶的Float32盒/高度/cross样本加±2毫米扰动共7,884例通过；3种owner上下文×3材质共9通道通过。样本不替代全三角几何或浏览器光栅验收，两项由独立审查记录。

入口、4个模块导入和候选目录请求统一版本化，避免新高段生产者配旧全高消费者。仅9份审核过的源码/构建/测试文件按固定SHA接受，见[runtime-height-source-change.json](runtime-height-source-change.json)。首轮未修高段结果保留在[旧运行时记录](runtime-checks-pre-height-fix.json)，初次高段预检保留在[height-clipping-preflight-checks.json](height-clipping-preflight-checks.json)。

## 片元坐标稳定修复

实际浏览器高段首轮仍有北4斜片；逐draw确认由near mesh_10颜色通道写出。真实GL纹理/计数/程序均正确，但RGBA8位编码读回的存活片元Z相对同像素几何射线偏约21—24毫米，越过约10毫米的裁剪余量。两个常量编码和重复X编码全部精确，记录保留于[故障与修复证据](fragment-coordinate-stability.json)。因此没有扩大裁剪边界。

生产改为插值不含modelMatrix平移的坐标，在fragment main处加回该object的平移后交原裁剪函数。程序缓存键更新为v3，入口/导入/候选目录查询更新为v2；Physical transmission声明顺序也有回归检查。同页正常颜色诊断中斜片消失、邻楼保留；还原原shader后原故障截图SHA完全复现。对照见[修复显示](fragment-diagnostic/normal-color.png)与[还原显示](fragment-diagnostic/restored-original.png)。最终独立浏览器验收另记录。

新29项Node聚焦检查、7组集成、35项灯牌／镜头检查全部通过；未改构建器沿用前阶段14项Python结果。Node shader检查只执行Three注入/流程与声明顺序，不冒称WebGL编译或逐object矩阵GPU验证；后两项由唯一QA的小fixture另验。旧218行、修复前258行及完整262行均保持原字节，GPU payload仍为ce4d45d3a9472b07790959cdb6052c715ea4411334d6399e2bccf9baac0feb09。

所有runtime CPU工作已结束，未启动Chrome或HTTP服务，可交唯一浏览器QA。
