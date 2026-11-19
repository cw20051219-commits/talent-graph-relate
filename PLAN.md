# 你要做的事（大白话版）

代码我全写好了，测也测过了。剩下的都得用**你自己的账号**，我替不了。按顺序做，全程不用出门。

---

## 第 1 步：报名（最先做，别拖）

打开 `https://relate.devpost.com/`，点注册（Devpost 账号），找到这个比赛点 Sign up。
- 免费，线上，个人就能报（也可组队 1-4 人）。
- 必须年满 18 岁。
- 报名后你会拿到提交入口，细则以这里为准。

**没报名 = 后面全白做，所以先做这一步。**

## 第 2 步：装 Relate（一条命令）

项目目录是 `D:\迅雷下载\2026-11-19-09-49-26\talent-graph-relate`。

- Windows：打开 PowerShell，运行
  `powershell -ExecutionPolicy ByPass -c "irm https://relatedb.ai/install.ps1 | iex"`
- 然后运行 `relate --version`，看到 `1.1.0` 或更高就对了。

## 第 3 步：装 Python 依赖（一条命令）

在这个目录里打开命令行，运行：

```
pip install -r requirements.txt
```

（只有 relate-db 一个包，10MB左右。）

## 第 4 步：建图 + 自测（两条命令，验证能用）

```
python scripts/build_graph.py
python scripts/selftest.py
```

第一条会生成 `outputs/talent-graph.rl`——这就是你的作品核心，一个能查的人才图谱数据库。
第二条应该显示 `23 passed, 0 failed`（如果显示 SKIP，说明第 3 步没装好或还没建图）。

再跑 `python scripts/demo_queries.py` 看看七个查询的真实结果。

## 第 5 步：录视频（2 分钟以内）

照着 `DEMO.md` 里的口播稿，用任意录屏软件录屏。比赛要求视频不超过 2 分钟——照着稿子念，卡着时间。

## 第 6 步：推到 GitHub（公开仓库）

1. 去 GitHub 新建一个**公开**仓库，名字随便，比如 `deepseek-talent-graph-relate`。
2. 在项目目录运行（把地址换成你的）：
   ```
   git remote add origin https://github.com/你的用户名/你的仓库名.git
   git push -u origin main
   ```
3. **关键**：到仓库页面 Settings 里，给仓库打上 `relate` 这个 topic 标签——规则明确说必须打，否则算提交不完整。顺手也加 `relate-neo4j-hackathon`。

## 第 7 步：提交

在 Devpost 提交入口填：项目简介、GitHub 链接、运行说明、视频链接、用了哪些工具（README 里都写好了，照抄即可）。

**截止时间：12 月 11 日 18:00  PST = 北京时间 12 月 12 日 10:00。** 这场有 3 周多，比 ODSC 那场（11/20）宽裕得多。

---

## 两场比赛对比（帮你排优先级）

| | ODSC × Nebius | Neo4j Relate |
|---|---|---|
| 截止 | 11/20（**明天**） | 12/12（三周后） |
| 大奖 | $2,000 额度 | Mac Studio（约 $3,799） |
| 我的完成度 | 代码+测试完成 | 代码+测试完成 |
| 你卡在哪 | 需要报名+两个 API key | 需要报名+装 Relate |

**建议**：ODSC 那场明天就截止，如果还没报名，基本赶不上了——除非你今晚就能拿到 key 并提交。Relate 这场时间充裕、奖品更实在、作品契合度更高，把精力压在这场。
