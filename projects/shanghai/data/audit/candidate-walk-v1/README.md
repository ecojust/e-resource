# 候选模型独立室外漫游与宋庆龄故居入口修正

本轮五个独立候选可在局部场景外围行走：宋庆龄故居主楼、鲁迅故居正立面与院门、崇明学宫尊经阁、大成殿、泮池与登云桥。**不属于城市原址接入**，不新增或替换任何城市源对象；原址入口仍为40处，未配准候选仍为5个。

漫游地面为虚拟平地。碰撞采用已校验模型的完整水平包围矩形，并保留人体间距；这是保守的外围禁入范围，不代表实测墙线或室内布局。泮池周围单独增加带中空区域的展示地面，保留池体可见；不支持上桥、登楼、外廊或室内。鲁迅故居仍只是正立面与院门，没有因此补成整栋建筑。

支持 WASD / 方向键、Shift 加速、触屏方向按钮、拖动转向与仰视、回到起点、Esc / 按钮返回旋转查看。失焦或触摸取消释放按键；细节切换保留保守碰撞范围；进入漫游加载完整模型。模型文件未通过大小与SHA检查时不能进入新场景，失败后可重试。

- `browser-final.json` 与对应图片：五个真实 Chromium 场景，直接链接进入、键盘实际移动与松键、墙体阻挡、沿墙移动、失焦停止、远景返回完整、重复进出无几何资源增长、手机布局、原生触屏移动、拖动转向和仰视。
- `failure.json`：损坏初始模型不能开始漫游；重试成功后进入请求的模式；远景加载失败保留完整模型与碰撞。
- `browser-public.json`：固定功能提交 `4b6efce` 的五场景完整公开复核。
- `source-files.json`：最终源码、清单、模型资产及关键数据的哈希绑定；完整行为验证的原始输入另保留在 `source-files-full-verification.json`。之后仅修正进入完整漫游时的下拉框状态，移动、碰撞和模型未改动。
- `quality-state-local.json` / `quality-state-public.json`：最终发布版本的五场景细节状态增量复核；手动远景进入漫游后显示完整细节，自动模式仍保持自动，实际行走仍可用。
- `soong-door/`：入口门的新几何、材质、原生文件和独立预览核验。

宋庆龄故居入口此前为全高玻璃门，现按已授权的2016入口照片改为浅色实门和上部小窗，加入凹进门框、下部门板及把手。小窗与门板细分、把手和全部尺寸仍为照片引导的估计。完整模型198,536面，远景17,332面；其余结构和三张原创PBR不变。完整/远景各13项射线检查；旧全高玻璃模型不能通过新增实门检查。压缩解码后几何、位置/UV及嵌入PNG一致；Blender保存重开和实际源几何匹配。

此前几何交付记录保留在 [宋庆龄故居V1](../soong-residence-v1/README.md) 及各候选原审计目录；历史文件哈希仅绑定当时版本。新的原址身份筛查见 [map-context-v2.json](../../../source/precise/xuhui-soong-ching-ling-residence/map-context-v2.json)：现有证据仍不足以把主楼可靠映射到院内小源轮廓，因此保留原城市模型。

复现（仓库根目录，需Playwright与Chromium）：

```sh
python -m http.server 8001 --directory projects/shanghai
node projects/shanghai/data/audit/candidate-walk-v1/qa-browser.cjs http://127.0.0.1:8001/ final
node projects/shanghai/data/audit/candidate-walk-v1/qa-failure.cjs
node projects/shanghai/data/audit/candidate-walk-v1/qa-soong-viewer.cjs
node --test projects/shanghai/tests/candidate-walk-motion.test.mjs projects/shanghai/tests/landmark-directory.test.mjs
```

原创代码、模型及人物沿用项目MIT许可；原参考照片许可与署名不变。未分发新查看的卫星影像或采样其像素作为材质。
