# 原英国驻沪领事馆办公主楼

中山东一路33号沿江花园内，1870年火灾后原址重建的办公主楼于1873年建成。1882年另建北侧住宅，两栋在档案照片中有独立题名。市房管局第二批保护名录2A010列该址1号楼、2号楼，工作名录另作1号楼、8号楼。这里依据历史用途、外墙与屋顶匹配确定所建的办公主楼及相连法院外墙。北侧住宅留在原址，连接廊和附近花园建筑另列。[保护名录、地方志及来源逐件记录](reference-review.json) · [两栋源轮廓和瓦片签名](footprint-review.json)

英国国家档案馆1911年南面全景可见中央五个拱券，1911年、1913年西面照片可辨旧法院的方柱外廊和凸门。1913年北面照片显示两端拱窗及中间不同窗形。东花园面参照2011年5月修缮后照片，保留凹入廊、两层开口、石栏杆和百叶窗。现存屋顶按航片分为主楼及相连西翼。1911至1913年照片以灰度为主，色彩、檐高、屋顶坡度、烟囱和门窗深度均为估算。模型仅含外观。[1911年南面](https://www.hpcbristol.net/visual/NA30-009) · [1913年北面](https://www.hpcbristol.net/visual/NA30-011) · [历史法院一侧](https://www.hpcbristol.net/visual/NA30-013)

[打开独立模型](../../../former-british-consulate.html) · [四件模型与下载签名](../../../assets/models/candidates/huangpu-former-british-consulate/manifest.json) · [几何和配准检验](../../../data/audit/former-british-consulate-v1/README.md)

## 重建

从上海项目目录执行。需要Python、NumPy、Shapely、Blender、gltfpack、ImageMagick与Open Image Denoise。

```sh
python source/precise/huangpu-former-british-consulate/source/build_model.py --out /tmp/consulate-assets --audit /tmp/consulate-audit --decoded /tmp/consulate-decoded --blender blender --gltfpack gltfpack --oidn oidnDenoise
python data/audit/former-british-consulate-v1/check-exterior.py --project . --manifest /tmp/consulate-assets/manifest.json --decoded /tmp/consulate-decoded --out /tmp/consulate-audit/exterior-checks.json
```
