# 游戏化国家公园护照打卡站 — design.md

> 方案 A 落地设计 ｜ 2026-09-16 ｜ 状态：MVP
> 配套文档：[成功假设与事实判断](./成功假设与事实判断.md)

---

## 1. 一句话定位

给"想集齐国家公园"的**收集型成年人和带娃家长**用的游戏化护照打卡工具站：
把集邮心理做成游戏机制（成就 / 等级 / 挑战 / 连续打卡），工具页吃搜索流量，联盟带货收钱。

不做：纯游戏站、巡逻员主题、teenager 人群定位（见事实判断 F8）。

## 2. 目标用户（按需求定位，不按人群）

| 用户 | 行为 | 付费信号 |
|---|---|---|
| 收集型成年人 | 买实体护照册、到访盖章、想在线同步进度 | passport book 6,600/月（电商词，竞争度 100/100） |
| 带娃家长 | 带孩子刷 junior ranger 项目、找亲子公园活动 | junior ranger CPC $0.85~$3.77（本轮最高） |

## 3. 成功标准（对齐假设 A1 / A6）

- 12 个月：2~5 万/月访问；收入锚点约 $630~$1,570/月
- 北极星指标：自然搜索流量占比 >60%（对标领跑者 71.2%）
- 证伪红线：上线 6 个月核心变体词无一进前 20 → 停下来复盘

## 4. 差异化：游戏化机制（v1）

6 家竞品清一色只做"记录"，v1 用游戏化切出缝隙：

- **等级**：按打卡公园数升级（Explorer → Adventurer → Ranger → Legend），进度条可视化
- **成就徽章**：首访 / 10 园 / 25 园 / 全 63 园 / 单州全制霸 / 连续打卡 7 天 / 30 天
- **挑战**：月度挑战（如"本月打卡 3 个新公园"）、印章收集进度环
- **连续打卡 streak**：每日打开并记录即算，轻量不强制
- **分享卡**：一键生成"我的国家公园成就"图片卡（canvas 生成），带站点域名水印 → 传播回流
- **数据存本地**：localStorage 持久化，对标 Inkpass（免费、无安装、无订阅）；v1 不做账号系统

> 假设 A2 的证伪点：上线 90 天回访率无差异 → 砍游戏化，只做工具+内容。

## 5. 信息架构与页面矩阵（URL 结构）

域名待定（词名直拼，用户拍板），以下路径基于根域名。

### P0 — MVP 必做

| 页面 | URL | 主攻词（美国月搜索量） |
|---|---|---|
| 首页 = 强交互打卡工具 | `/` | national park checklist（1,600）、national parks checklist（880） |
| 变体页 ×8 | `/check-off/` `/tracker/` `/counter/` `/visited-map/` `/interactive-map/` `/passport-stamps/` `/passport-book/` `/park-planner/` | check off / tracker / counter / visited map / interactive map / passport stamps（2,400）/ passport book（6,600）/ planner（140） |
| 公园单页 ×63 | `/parks/{slug}/` | 各公园名 + checklist 长尾 |
| Quiz 内页 | `/quiz/` | national park trivia（1,000）、national park quiz（320，顶部出价 $21.73） |
| 技术页 | `/sitemap.xml` `/robots.txt` | — |

- 变体页：一页一词，同一套模板 + 差异化文案（标题/H1/首段/FAQ 各不相同，防重复内容）。
- 公园页：程序化生成（简介 / 建园年份 / 面积 / 特色 / 打卡按钮 / 同州公园内链）。

### P1 — 上线后 30 天

- `/states/{state}/` 50 州打卡页
- 电商导购页 `/scratch-off-map/` `/journal/` `/bucket-list/`（联盟位，100/100 竞争度词）
- `/annual-pass/`（america the beautiful pass，9 万/月）
- poster 线：待调研补完（F11 边界项 3）后再定

### P2 — 长期

- NPS 433 个单元扩展（领跑者已验证池子够大）
- PWA / App 化（吃 `national park passport app` +56% 的溢出）

## 6. 核心工具交互（首页）

- 左：63 园清单（按州/字母筛选 + 搜索框），点击 toggle 打卡
- 右：统计面板（已去 X/63、等级进度条、成就墙、streak 天数）
- 首次访问 3 步引导；所有状态写 localStorage
- 分享卡生成按钮（canvas → PNG 下载）
- 首屏正文 ≥800 词 + FAQ（哥飞：工具页文字也要铺够）；FAQPage JSON-LD

## 7. SEO 规范

- 一页一词：title / H1 含目标词，URL 短横线拼词
- 内链网：公园页互链（同州/附近）→ 变体页互链 → 首页链全部
- 每页必备：meta description、OG 标签、canonical、JSON-LD（WebPage + FAQPage）
- 内容量：变体页正文 ≥1200 词 + 工具组件；公园页 ≥400 词
- 上线当天提交 Search Console + sitemap（muse-zh 的教训：别等收录）

## 8. 技术方案

- **Python 静态生成器**：`data/parks.json`（63 园数据）+ `templates/` → `dist/` 全静态 HTML
- 交互：原生 JS，无框架；localStorage 持久化
- 部署：Cloudflare Pages（Direct Upload API）；GitHub 公开仓库备份
- 零后端、零数据库（v1）；内容构建时 bake（对齐 WorkAtAI blog 模式）

## 9. 变现设计（按优先级）

1. **联盟带货（主）**：passport book / scratch-off map / journal 导购位（Amazon Associates 待申请，v1 先占位，后替换链接）
2. **AdSense（保底）**：v1 占位，流量 >1 万/月再接入（出价 $0.04~$0.79，期望放低）
3. 年票/装备信息页联盟位（P1）

## 10. MVP 验收标准（AC）

- [ ] 首页工具可用：打卡 / 统计 / 成就 / 分享卡全链路走通
- [ ] 8 变体页 + 63 公园页 + quiz 页全部生成，HTML 自检通过（无坏链）
- [ ] sitemap.xml / robots.txt / JSON-LD 就绪
- [ ] Cloudflare Pages 上线，https 可访问
- [ ] GitHub 仓库已推送

## 11. 待用户拍板

- [ ] 域名（词名直拼；候选：nationalparkchecklist 类已被占，需调研可用变体）
- [ ] Amazon Associates 联盟账号（用谁的信息申请）
- [ ] poster 线是否跟进（等 KD 精评 + Inkpass 复查之后）
