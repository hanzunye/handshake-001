# HANDSHAKE-001 总清单（作者自用）

> 权威文件是英文的 `PREREGISTRATION.md`，本清单只是执行步骤。时间换算：10 月 12 日德国是夏令时（CEST），**德国时间 = UTC + 2**（夏令时 10 月 25 日才结束，即使推迟 7 次也不受影响）。
> 每次打开终端，先执行：`cd ~/Documents/fullstack/CISACOP/handshake-001 && source .venv/bin/activate`
> 实验过程中，把所有链接、时间和编号随手记进 `RECORD.md`。

---

## 0. 当前状态（2026-10-09）

**已定时间**：T0 = 2026-10-12 08:00 UTC（德国 10:00），T1 = 11:00 UTC（德国 13:00），等待 3 小时。已写入 `config.json` 和预注册。

### 当天时间表（德国时间）

| 德国时间 | UTC | 做什么 | 硬性要求 |
|---|---|---|---|
| 09:25 | 07:25 | 开 `caffeinate`，OBS 开始直播和录制，展示开场画面（F1、F2） | — |
| 09:30–09:58 | 07:30–07:58 | 自检窗口。计划 09:45 运行 `preflight` | 09:58 前必须有一次**完整**通过（开始和结束都在窗口内） |
| 09:59–10:10 | 07:59–08:10 | 开始窗口。计划 10:00 运行 `start` | 只能运行一次 |
| 紧接着 | | 发 ANU 承诺帖、备份，然后运行 `commit-ibm` | — |
| 12:25 前 | 10:25 | IBM 最后一次重新提交的创建时间（以 IBM 服务器时间为准） | 由脚本把关 |
| 12:30 前 | 10:30 | IBM 作业必须完成 | 由脚本把关 |
| 12:50 前 | 10:50 | 两条承诺帖都必须已经发在 X 上 | 晚了就 `void` |
| **13:00:00** | 11:00:00 | **T1**：目标就是 NIST 时间戳为 13:00:00 的那一个值 | — |
| 13:01 起 | 11:01 | 运行 `fetch-target`（脚本在 13:01 之前会拒绝运行，留 1 分钟让 NIST 发布） | — |
| 之后 | | `reveal`、`verify`，结束直播 | — |
| 14:01 起 | 12:01 | N2：`fetch-secondary` | 不用直播 |
| 10-13 13:01 起 | | N3 | 不用直播 |
| 10-19 13:01 起 | | N4 和次要分析报告 | 不用直播 |

如果推迟一次，上表所有时间顺延 24 小时（日期加一天，钟点不变）。


**✅ 已完成**
- ANU 免费 key：已保存到 `~/.anu_qrng_key`，测试可用。每月 100 次，已用约 3 次
- IBM 账号和 key：已保存到 `~/.qiskit/`，连接正常，可用的机器有 ibm_kingston、ibm_marrakesh、ibm_fez。每 28 天额度 600 秒，已用约 2 秒
- IBM 排队时间试测 1 次：9 秒（当时是空闲时段）
- 项目环境 `.venv`：版本已锁定（`requirements.txt`），OpenTimestamps 测试通过，本地模拟器已安装
- 脚本 v3.2：重试、自检、推迟、NIST 唯一来源、Codex 指出的问题已修复，离线测试全部通过
- 预注册 v3.2（时间已填）、核对说明、README
- YouTube 直播权限

**⬜ 还缺的（按顺序补）**

| # | 缺什么 | 在哪一步 |
|---|---|---|
| 1 | 10-10、10-11 的德国 10:00 各测一次 IBM 排队（等待时长已定为 3 小时，只是确认） | B |
| 2 | ~~定下 T0 的日期和时间~~ 已定：2026-10-12 德国 10:00 | B |
| 3 | 网络恢复后：真机彩排一次（用真的 ANU 和 IBM） | B |
| 4 | Codex 第二轮审核，审完后定稿 | C |
| 5 | 填好 AUTHOR、X_HANDLE、发布日期，最后算代码的指纹 | C |
| 6 | GitHub 账号和仓库 | A |
| 7 | Zenodo 账号（可以用 GitHub 登录），并开通和 GitHub 的联动 | A |
| 8 | 第二个公开平台的账号（Bluesky、Mastodon 或微博，至少一个） | A |
| 9 | 决定用主账号还是专门新开一个 X 账号 | A |
| 10 | 安装 OBS，授予屏幕录制权限，做一次不公开的测试直播 | E |
| 11 | 在 YouTube 上预约这场直播，拿到直播链接 | E |
| 12 | 一个 U 盘（备份秘密文件用） | A |
| 13 | 手机热点，作为网络的备用 | A |
| 14 | 许可协议：在 Zenodo 上传时选 CC0 1.0，README 里写明 | D |
| 15 | （可选）B 站和 YouTube 的预告视频 | D 之后 |

---

## A. 账号与物品

- [x] A1. ANU key
- [x] A2. IBM 账号
- [x] A3. YouTube 直播权限
- [ ] A4. **X 账号**：决定用主账号还是新开一个专门的实验账号。之后所有帖子都必须从**同一个账号**发出。
- [ ] A5. **第二个公开平台**：Bluesky 或 Mastodon，都开放、容易被网页存档，任选一个；如果想让中文读者看到，再加上微博。X 上发的每一条，这里都同步发一条。
- [x] A6. **GitHub**：注册账号，或者用现有的。
- [ ] A7. **Zenodo**：在 zenodo.org 用 GitHub 账号登录 → 个人设置里的 GitHub 页面 → 打开 `handshake-001` 仓库的开关。之后每在 GitHub 发布一个 Release，Zenodo 都会自动存档并分配 DOI。
- [x] A8. **U 盘**：`my usb`（NTFS，靠 iBoysoft NTFS 驱动才能写入；10-09 写入测试通过，已建好 `HANDSHAKE-001` 文件夹）。10-11 再测一次能否写入。另外准备一份加密网盘备份。
- [ ] A9. **手机热点**：提前测试，确认电脑能连上。

## B. 测试与定参数

- [ ] B1. 在你计划实验的**那个时段**（德国 10:00 左右），运行 `python3 handshake.py ibm-trial`，最好在不同的日子测 2–3 次，记进 `RECORD.md`。
- [ ] B2. 定等待时长：**取试测中最长的总耗时乘以 3，再和 3 小时比较，取较大的那个**。
- [ ] B3. 定 T0。注意以下几点：
  - 避开 IBM 公布的维护时间（看 IBM Quantum 的状态页）；
  - 避开美国政府可能停摆的时期（看新闻），停摆时 NIST 信标会停止发布；
  - 选一个你自己精力好、能连续坐 4–5 个小时的时段。
- [x] B0. 10-09 已完成：真实 NIST 链校验、模拟彩排、真 ANU + 真 IBM 彩排、真实自检（临时目录，不计入正式记录），全部通过。
- [ ] B4. 本地彩排（模拟器，免费）：`python3 handshake.py rehearse --ibm fake`，要看到 `REHEARSAL PASSED`。
- [ ] B5. 真机彩排：`python3 handshake.py rehearse --anu anu --ibm real`，会用掉 1 次 ANU 额度和几秒 IBM 额度。

## C. 代码定稿

- [x] C1. 代码审核（Codex 额度恢复后，让我来发起）。审核发现问题就修改，并重新彩排。
- [x] C2. **代码定稿后不再改动。**（2026-10-09 定稿，`handshake.py` 已设为只读）
- [x] C3. 填 `config.json`：`t0_utc` = `2026-10-12T08:00:00Z`，`t1_utc` = `2026-10-12T11:00:00Z`。
- [x] C4. 填 `PREREGISTRATION.md` 剩下的占位符：`Han Yunze`、`@DavonGluck`、`{{PUBLICATION_DATE}}`（T0、T1、等待时长已填）。README 里的占位符也一并填好。
- [x] C5. **最后**填 `{{HANDSHAKE_PY_SHA256}}`：运行 `shasum -a 256 handshake.py` 得到。自检会核对这个值，所以之后代码一个字都不能动。

## D. 预注册发布：多平台（最晚 10-11，建议 10-10；必须在 T0 之前）

- [x] D1. 计算并记下：`shasum -a 256 PREREGISTRATION.md handshake.py config.json`
- [x] D2. 盖时间戳：`ots stamp PREREGISTRATION.md handshake.py config.json`
- [x] D3. **GitHub**（10-09 已推送到 https://github.com/hanzunye/handshake-001 ，Release 还没发）：在 `handshake-001` 目录下运行 `git init`，提交后推送到新建的公开仓库。`secret/`、`.venv/`、`rehearsal/` 都不会被推上去。然后发布一个 Release，名字叫 `v1.0-prereg`。
- [x] D4. **Zenodo**（DOI 10.5281/zenodo.23269344；还需把作者和许可协议改成 Han, Yunze 和 CC0）：发布 Release 后会自动生成一个 DOI，记下来。如果 Zenodo 让你选许可协议，选 CC0 1.0。
- [x] D5. **YouTube**：先预约好直播（见 E2），拿到直播链接。
- [x] D6. **X 预注册帖**（2026-10-09 19:46 UTC 已发）（用文字发，然后**置顶**）：
  ```
  HANDSHAKE-001 pre-registration
  Protocol SHA-256: <PREREGISTRATION.md 的 64 位指纹>
  T0 2026-10-12 08:00 UTC | T1 2026-10-12 11:00 UTC
  Live: <YouTube 直播链接>
  Repo: <GitHub 链接>
  DOI: <Zenodo DOI>
  ```
- [ ] D7. **第二平台**：发同一段文字。
- [x] D8. **存档**（X 帖：archive.ph/XKAfI；web.archive.org 存的是 oEmbed 版本）：把 X 帖子、第二平台帖子、GitHub 页面、Zenodo 页面，分别提交到 archive.ph 和 web.archive.org。web.archive.org 常常存不下 X 的页面，所以以 archive.ph 为主。
- [ ] D9. 过几个小时运行 `ots upgrade *.ots`，然后把 `.ots` 文件推送到 GitHub。
- [ ] D10. 所有链接、指纹和 DOI 都记进 `RECORD.md`。
- [ ] D11. （可选）发 B 站和 YouTube 预告视频。视频里展示预注册链接和指纹，并说明预期结果几乎一定是"无法判断"。

## E. 直播准备

- [ ] E1. **OBS Studio**：
  - 从 obsproject.com 下载安装；
  - 在系统设置 → 隐私与安全性 → 屏幕录制里，允许 OBS；
  - 推流设置：选 YouTube，可以直接连接账号，也可以填直播码；
  - 录制设置：格式选 **mkv**（软件崩溃也不会丢失录像），记下保存路径；
  - 画面设置：1920×1080，每秒 30 帧；
  - 场景：终端（字号 18 以上）+ 浏览器（X、NIST 页面）+ time.is（同时显示 UTC 和德国时间）。如果不说话，可以加一段文字说明；
  - 直播时同时按下"开始直播"和"开始录制"。
- [ ] E2. **YouTube 预约直播**：YouTube Studio → 创建 → 进入直播 → 安排直播。
  - 标题，例如：`HANDSHAKE-001 — a pre-registered one-shot test (live, full session)`
  - 说明：贴上预注册链接、指纹、DOI、T0 和 T1、`VERIFY.md` 链接
  - 公开范围：公开；不面向儿童；允许嵌入
  - 注意：直播超过 12 小时不会保存回放，这次大约 4–5 小时，没问题
- [ ] E3. **Mac 设置**：
  - 接上电源；
  - 时间设为自动同步（系统设置 → 通用 → 日期与时间）；
  - 暂停系统自动更新；
  - 打开勿扰模式；
  - 关掉无关的应用；
  - 专门开一个干净的浏览器配置文件用于直播。
- [ ] E4. **网络**：测一下上传速度，1080p 大约需要 4–6 Mbps；手机热点随时可以接上。
- [ ] E5. **测试直播**：至少提前 1 天，用"不公开"模式完整演练一遍：
  - 运行 `python3 handshake.py rehearse`；
  - 练习在 X 发帖、刷新页面、存档；
  - 检查画面、字号、声音，以及本地录像文件是否正常。

## F. 实验当天：T0 段（全程直播）

- [ ] F1. **T0 前 35 分钟（德国 09:25）**：在单独一个终端标签里运行 `caffeinate -dimsu`，整场都不要关，它会让 Mac 不进入睡眠。在 OBS 里同时开始直播和录制。
- [ ] F2. 开场画面（不露脸，屏幕上展示）：
  - X 上置顶的预注册帖及其发布时间；
  - GitHub 或 Zenodo 页面；
  - 现场运行 `shasum -a 256 PREREGISTRATION.md handshake.py`，和公开的指纹对照；
  - NIST 网页，展示信标每分钟都在更新。
- [ ] F3. **T0 前 30 分钟到 T0 前 2 分钟（德国 09:30–09:58）**：运行 `python3 handshake.py preflight`，必须看到 `PREFLIGHT PASSED`。一次自检要连 NIST、ANU、IBM，实测大约 10 秒（10-09 测试），**开始和结束都要在窗口内**，保险起见最后一次最晚 09:55 开始。没通过就修好后再跑一次；到 09:58 还没通过，就按 M2 推迟。
- [ ] F4. **T0（德国 10:00；窗口为 09:59–10:10）**：运行 `python3 handshake.py start`。如果请求失败，脚本会自动重试，每一路最多 10 次，**不要中途打断**。
- [ ] F5. 立刻把 **ANU 承诺帖**原样发到 X 和第二平台，刷新页面，让观众看到发帖时间，然后存档。
- [ ] F6. 备份秘密文件：`cp secret/anu.json "/Volumes/my usb/HANDSHAKE-001/" && cmp secret/anu.json "/Volumes/my usb/HANDSHAKE-001/anu.json" && echo "ANU backup OK"`，再加一份加密网盘。**只复制，不打开。**
- [ ] F7. 运行 `caffeinate -i python3 handshake.py commit-ibm`，让它一直等着。
- [ ] F8. IBM 完成后，把 **IBM 承诺帖**（里面带作业编号）发到 X 和第二平台并存档，然后备份 `secret/ibm.json`。
  - IBM 作业必须在 **T1 前 30 分钟（德国 12:30）**之前完成，承诺帖必须在 **T1 前 10 分钟（德国 12:50）**之前发出。
  - 如果脚本提示 OpenTimestamps 盖章失败：照常发帖，记进 `RECORD.md`，之后补盖。盖章只是补充证据，失败不作废。
- [ ] F9. 把 `public/` 推送到 GitHub。里面没有秘密，提前推送可以多留一份记录。
- [ ] F10. 记进 `RECORD.md`：两条帖子的链接、时间、存档链接、IBM 作业编号。

## G. 等待期（直播继续）

- [ ] G1. 画面保留：时钟、终端（显示 `public/` 里的文件列表）、NIST 最新信标页（定时刷新）、一段说明文字。
- [ ] G2. **不要**打开 `secret/`，**不要**打开 IBM 网页控制台里这个作业的结果页。
- [ ] G3. 如果某条承诺帖没能按时发出，就在开封前运行 `python3 handshake.py void --draw IBM --reason "..."`（ANU 那条就写 `--draw ANU`）。

## H. T1 段：取目标

- [ ] H1. T1 前 10 分钟（德国 12:50）：在浏览器准备好这个地址，13:01 后刷新，它就是目标：
  `https://beacon.nist.gov/beacon/2.0/pulse/time/1791802800000`
  （T1 之前打开会显示 404，这是正常的。）
- [ ] H2. **德国 13:01 或更晚**：运行 `python3 handshake.py fetch-target`。目标是时间戳为 13:00:00 的那个值，不是你运行命令那一刻的值，所以晚几分钟运行不影响结果。
- [ ] H3. 把脚本输出的**目标帖**发到 X 和第二平台；把脚本给出的 NIST 存档链接打开存档；`target.json` 的时间戳由脚本自动盖好。
- [ ] H4. 如果脚本提示 NIST 连不上或者还没发布：**等一会儿再试**。目标值不会因此改变。

## I. 开封与当场核对

- [ ] I1. 运行 `python3 handshake.py reveal`，把**揭晓帖**发到 X 和第二平台，然后存档。
- [ ] I2. 当场核对：**从 X 帖子上复制哈希值**，运行
  `python3 handshake.py verify --anu-sha256 … --anu-sha3-512 … --ibm-sha256 … --ibm-sha3-512 …`
- [ ] I3. 用一两句话说明结果的含义（按预注册第 6 节），然后结束直播，停止录制。

## J. 实验后：多平台归档

**当天（揭晓后 1 小时内）**
- [ ] J1. 把 `public/` 全部推送到 GitHub。其中包括 `public/opened/`，也就是揭晓后公开的完整秘密文件。
- [ ] J2. 在 README 里填上状态、结果和各个链接；在 GitHub 发布 Release `v1.1-result`，Zenodo 会自动生成新版本。
- [ ] J3. 确认 YouTube 回放已保存，OBS 本地录像文件完好。

**次要目标（不用直播，到时间运行即可；NIST 的档案是永久的，晚一点再取也没关系）**
- [ ] J3b. **T1 + 1 小时后（德国 14:01 起）**：运行 `python3 handshake.py fetch-secondary`，取 N2。把输出的帖子发到 X 和第二平台，再打开脚本给出的 NIST 存档链接完成存档。
- [ ] J3c. **T1 + 24 小时后（10-13 德国 13:01 起）**：再运行一次，取 N3，照样发帖、存档。
- [ ] J3d. **T1 + 7 天后（10-19 德国 13:01 起）**：再运行一次，取 N4。这一次脚本还会生成**次要分析报告**（`public/secondary.json`），把报告帖发到 X 和第二平台，推送到 GitHub，发布 Release `v1.2-secondary`，Zenodo 会自动生成新版本。
- [ ] J3e. 次要分析的结果**单独报告**，不改变主结果（预注册第 6.2 节）。

**24 小时内**
- [ ] J4. 运行 `ots upgrade *.ots public/*.ots`，推送到 GitHub 并在 Zenodo 发布新版本。
- [ ] J5. 从 YouTube Studio 下载回放，连同 OBS 本地录像一起上传到 archive.org 或 Zenodo（Zenodo 每条记录最多 50 GB）。
- [ ] J6. 在 X 和第二平台发**结果总结帖**并置顶：
  ```
  HANDSHAKE-001 result: <INCONCLUSIVE / HIT (…) / DOUBLE HIT>
  Data, proofs, code: <DOI 链接>
  Full recording: <YouTube 链接>
  Verify it yourself: <VERIFY.md 链接>
  ```
- [ ] J7. 把 `RECORD.md` 填完整，一起推送到 GitHub。

**一周内（可选）**
- [ ] J8. 把录像上传到 B 站。
- [ ] J9. 如果是任何一种命中：按预注册第 6 节处理，先找程序和计时上的问题，公开全部材料，**不宣称证明了什么**。

---

## K. 发布矩阵：每个阶段往哪里发什么

| 阶段 | X（置顶或普通帖） | 第二平台 | GitHub | Zenodo | 网页存档 | OpenTimestamps | YouTube |
|---|---|---|---|---|---|---|---|
| 预注册 | 预注册帖（置顶） | 同上 | Release `v1.0-prereg` | 自动生成 DOI | X 帖、GitHub、Zenodo | 预注册、代码、配置 | 预约直播 |
| 推迟（如有） | 推迟帖 | 同上 | `postponements.json` | — | X 帖 | — | 修改预约时间 |
| T0 | ANU 承诺帖、IBM 承诺帖 | 同上 | `public/` | — | 两条帖子 | 两份承诺（脚本自动） | 直播中 |
| T1 | 目标帖 | 同上 | — | — | X 帖 + NIST 那一分钟的页面 | `target.json`（脚本自动） | 直播中 |
| 开封 | 揭晓帖 | 同上 | `public/` 全部（含 `opened/`） | — | X 帖 | — | 直播结束，自动保存回放 |
| 次要目标（+1 小时、+24 小时、+7 天） | N2、N3、N4 帖子，第 7 天发报告帖 | 同上 | `secondary_N2.json`、`secondary_N3.json`、`secondary_N4.json`、`secondary.json` | `v1.2-secondary` | 每个 NIST 值的页面 | 每个 `secondary_N*.json`（脚本自动） | — |
| 之后 | 结果总结帖（置顶） | 同上 | Release `v1.1-result`、升级后的 `.ots`、`RECORD.md` | 新版本 + 录像 | 总结帖 | `ots upgrade` | 回放 |

## L. 直播画面里绝对不能出现的

- `secret/` 目录里的任何文件；
- `~/.anu_qrng_key` 和 `~/.qiskit/`；
- 任何会显示 key 的命令（例如 `cat` 这两个文件，或者打印环境变量）；
- IBM 网页控制台里这个作业的结果页；
- 消息通知、邮箱、其他浏览器标签页。

## M. 出问题时怎么办

| 情况 | 做法 |
|---|---|
| M1. 自检某一项没通过 | 修好后在窗口内再跑一次。每一次都会被记录、之后公开 |
| M2. 到 T0 前 2 分钟仍未通过，或者遇到停电、生病、维护 | `python3 handshake.py postpone --reason "..."`，然后在 T0 后 10 分钟之前把推迟帖发出去。最多推迟 7 次 |
| M3. `start` 运行时 ANU 或 IBM 请求失败 | 脚本自动重试，每一路最多 10 次；全部失败的那一路作废，另一路照常进行 |
| M4. IBM 作业报错 | `commit-ibm` 会自动重新提交，最晚到 T1 前 35 分钟 |
| M5. 电脑睡着了或者断网 | 截止时间之前重新运行 `commit-ibm` 就能接上 |
| M6. 承诺帖发晚了 | 开封前用 `void` 命令标记作废，之后公开说明 |
| M7. NIST 连不上，或者还没发布 | 等一会儿再试，目标值不会变 |
| M8. 直播中断 | 马上重新开播，OBS 本地录像一直在录。在回放说明和 `RECORD.md` 里注明中断的时间段。直播只是补充证据，中断本身不会让实验作废 |
| M10. OpenTimestamps 盖章失败 | 不影响实验。记进 `RECORD.md`，网络好了以后运行 `ots stamp <文件>` 补盖（已有 `.ots` 的文件不会被覆盖） |
| M9. 两路都作废 | 这次实验作废，公开说明。按"只做一次"的约定，HANDSHAKE-001 到此结束 |
