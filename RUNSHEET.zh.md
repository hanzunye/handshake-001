# HANDSHAKE-001 当天直播运行单（2026-10-12，德国时间 CEST = UTC+2）

> 打印出来放在手边。详细说明见 `CHECKLIST.zh.md` 的 E–I 和 M 部分。

## 1. 画面（OBS 准备三个场景）

| 场景 | 内容 | 什么时候用 |
|---|---|---|
| **开场** | 浏览器全屏，标签页依次是：X 置顶的预注册帖 → GitHub 仓库 → Zenodo 记录 → NIST 信标页 https://beacon.nist.gov/home → time.is（同时显示 UTC 和柏林时间） | 09:25–09:40 |
| **终端**（主场景） | 左边大终端（字号 18 以上），右上 time.is 时钟，右下浏览器（X 或 NIST） | 运行命令、发帖的时候 |
| **等待** | 和"终端"场景一样，再加一行字：`Commitments posted, numbers hidden. Waiting for T1 = 13:00:00 CEST.` | 10:30–12:50 |

浏览器用一个专门的干净配置文件，只开上面这些标签页。Mac 打开勿扰模式。

## 2. 开播前（09:00–09:25）

- 接上电源，插好 U 盘（名字是 `my usb`，里面已建好 `HANDSHAKE-001` 文件夹）。
- **终端 1（不出镜）**：`caffeinate -dimsu`，整场都不要关。
- **终端 2（出镜）**：
  ```
  cd ~/Documents/fullstack/CISACOP/handshake-001
  source .venv/bin/activate
  unset PYTHONPATH
  clear
  ```
- 09:15 在 OBS 点"开始推流"，在 YouTube 直播控制室的预览里检查画面和声音。

## 3. 时间表

| 德国时间 | 场景 | 运行 / 操作 |
|---|---|---|
| **09:25** | 开场 | YouTube 点"开始直播"，OBS 点"开始录制" |
| 09:25–09:44 | 开场 → 终端 | 逐个展示 X 置顶帖、GitHub、Zenodo；然后在终端运行：<br>`shasum -a 256 PREREGISTRATION.md handshake.py config.json`<br>`cat config.json`<br>对照 X 帖子和预注册里的指纹，确认一致 |
| **09:45** | 终端 | `python3 handshake.py preflight`，要看到 `PREFLIGHT PASSED`。<br>没通过：看是哪一项 FAIL，修好再跑；最后一次最晚 09:55 开始 |
| **10:00** | 终端 | `python3 handshake.py start`。它会自动重试，**中途不要打断** |
| 紧接着 | 浏览器 | 复制屏幕上的 **ANU 承诺帖**文字，发到 X 和第二平台，刷新页面让发帖时间出现在画面里，然后存档 |
| 紧接着 | 终端 | `cp secret/anu.json "/Volumes/my usb/HANDSHAKE-001/" && cmp secret/anu.json "/Volumes/my usb/HANDSHAKE-001/anu.json" && echo "ANU backup OK"`<br>（只复制、不打开；`cmp` 只比对内容是否一致，不会显示内容） |
| 紧接着 | 终端 | `python3 handshake.py commit-ibm`，等它打印出 IBM 承诺帖（通常 1 分钟以内） |
| 紧接着 | 浏览器 | 发 **IBM 承诺帖**（里面带 JOB 编号），存档；然后在终端运行 `cp secret/ibm.json "/Volumes/my usb/HANDSHAKE-001/" && cmp secret/ibm.json "/Volumes/my usb/HANDSHAKE-001/ibm.json" && echo "IBM backup OK"` |
| 两条承诺帖都发出后 | 终端 | `git add public && git commit -m "T0 commitments" && git push` |
| 10:30–12:50 | 等待 | 保持画面，偶尔运行 `ls -l public/`、刷新 NIST 页面。<br>**趁这段时间**把下面 13:05 要用的 verify 命令准备好：哈希从两条 X 帖子里复制 |
| **12:50** | 浏览器 | 打开 https://beacon.nist.gov/beacon/2.0/pulse/time/1791802800000 ，现在显示 404 是正常的 |
| **13:01** | 终端 | `python3 handshake.py fetch-target`，把打印出的**目标帖**发到 X，打开它给出的存档链接；然后刷新上面的 NIST 链接，画面上显示的是同一个值 |
| 紧接着 | 终端 | `python3 handshake.py reveal`，把打印出的**揭晓帖**发到 X 和第二平台，然后存档 |
| 紧接着 | 终端 | 运行 verify（见下方），最后一行应为 `VERDICT: consistent` |
| 紧接着 | 终端 | `git add public && git commit -m "T1 target and reveal" && git push` |
| 结束 | — | 用一两句话说明结果（预注册第 6 节），在 YouTube 点"结束直播"，再在 OBS 停止推流和录制 |

verify 命令（四个值都从 X 帖子里复制，不要从本地文件复制）：
```
python3 handshake.py verify \
  --anu-sha256 <ANU 帖里 SHA256: 后面的值> \
  --anu-sha3-512 <ANU 帖里 SHA3-512: 后面的值> \
  --ibm-sha256 <IBM 帖里 SHA256: 后面的值> \
  --ibm-sha3-512 <IBM 帖里 SHA3-512: 后面的值>
```

## 4. 截止时间（脚本会把关，但要心里有数）

| 德国时间 | 截止 |
|---|---|
| 09:58 | 必须有一次完整通过的自检 |
| 09:59–10:10 | 只能在这个窗口里运行 `start`，而且只能运行一次 |
| 12:30 | IBM 作业必须完成 |
| **12:50** | 两条承诺帖都必须已经发在 X 上 |
| 13:01 起 | 才能运行 `fetch-target` |

## 5. 画面里绝对不能出现

- `secret/` 里的任何内容：不要 `cat`、不要用访达打开、不要预览；
- `~/.anu_qrng_key` 和 `~/.qiskit/`；
- IBM 网页控制台里这个作业的结果页；
- 消息通知、邮箱、其他标签页。

## 6. 出问题时

| 情况 | 做法 |
|---|---|
| 自检没通过，到 09:58 还修不好 | `python3 handshake.py postpone --reason "..."`，把打印出的推迟帖在 10:10 之前发出；YouTube 直播改到明天同一时间 |
| `start` 在重试 | 不要打断，等它自己结束 |
| `commit-ibm` 被打断或断网 | 网络恢复后重新运行 `python3 handshake.py commit-ibm` |
| 承诺帖没能在 12:50 前发出 | 揭晓前运行 `python3 handshake.py void --draw ANU --reason "..."`（IBM 那条就写 `--draw IBM`） |
| `fetch-target` 提示 NIST 还没发布或连不上 | 等一两分钟再运行，目标值不会变 |
| 提示 OpenTimestamps 失败 | 不影响实验，记进 `RECORD.md`，之后补盖 |
| 直播断了 | OBS 会自动重连，本地录像一直在录；记下中断的起止时间 |
