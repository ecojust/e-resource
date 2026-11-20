# 上海市房屋管理局五批优秀历史建筑登记表

2026 年 11 月 20 日，从上海市房屋管理局「优秀历史建筑」栏目打开五张登记表。五个网页均返回 HTTP 200，共有 1,058 条带编号的登记行。每行保留网页表格的行号、区名栏头、印刷编号、原名或原使用单位、表列现名或使用单位及地址。一个登记范围可以包含多栋建筑。[房管局栏目](https://fgj.sh.gov.cn/yxlsjz/index.html) · [提取结果](register.json) · [下载地址、字节数及 SHA-256](sources.json)

| 批次 | 官方登记行 | 原名和一项地址相同 | 仅地址相同 | 余下需查 |
| --- | ---: | ---: | ---: | ---: |
| [第一批](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html) | 61 | 34 | 10 | 17 |
| [第二批](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) | 175 | 128 | 8 | 39 |
| [第三批](https://fgj.sh.gov.cn/yxlsjz/20210922/bc5957926d80432b8bea0157eb16bb94.html) | 162 | 104 | 6 | 52 |
| [第四批](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) | 234 | 138 | 37 | 59 |
| [第五批](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) | 426 | 124 | 134 | 168 |
| 合计 | 1,058 | 528 | 195 | 335 |

在同一批的项目工作名录内，对原名及地址去除空白、统一 Unicode 全半角，再逐字比较。528 条官方行在原名和一项地址上都有相同记录，其中 8 条各有多个候选；195 条仅找到相同地址，其中 1 条有多个候选。335 条需要查异名、门牌、合并与拆分。来源页的顺序和工作名录编号分别保留。确定楼栋、位置、建造年代及改造范围仍须逐栋使用现场照片、平面或原址证据。[原始工作名录](../../model-todo/discovered-buildings.json) · [已核地址异文及具体建模范围](../first-batch-register-2026-11-20/README.md)

第二批的 2M006 在圣约翰大学同一保护编号和地址下，另列校政厅、怀施堂等六组建筑原名与表列楼号。第二、第三批页面还附有三处标明灭失年代的表注，结果保留表注所在行。第五批两次使用 5A012，分别列思南路 36 号、皋兰路 12 号；两次使用 5F038，分别列四川北路和高阳路地址。结果使用批次及原始表格行号区别这些登记，并保留 D5035、50D80、D50102 等原页印刷形式。[逐行原值](register.json)

## 重现

使用项目发现工具的 Beautiful Soup 依赖。从来源清单下载五个 HTML 页面，分别在同一目录保存为 `batch1.html` 至 `batch5.html`。脚本先核对网页与原始工作名录的字节指纹，再提取和比对。以下命令从仓库根目录运行，将结果写入临时文件。[依赖版本](../../model-todo/tooling/requirements.txt) · [提取脚本](extract.py)

```sh
python projects/shanghai/data/audit/municipal-heritage-register-2026-11-20/extract.py \
  --cache /tmp/shanghai-historic-registers --output /tmp/shanghai-register-recheck.json
cmp /tmp/shanghai-register-recheck.json projects/shanghai/data/audit/municipal-heritage-register-2026-11-20/register.json
```
