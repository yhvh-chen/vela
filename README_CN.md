# Vela Astrology Skill

<p align="center">
  <img src="assets/logo.png" alt="Vela Astrology Logo" width="200" style="border-radius: 50%;"/>
</p>

<p align="center">
  <a href="README.md">English README</a> | <b>简体中文</b>
</p>

这是一个自包含的占星图盘计算与解读 Agent Skill 包，封装了基于 `kerykeion` 的底层的瑞士星历表（Swiss Ephemeris）计算框架，专为各类大语言模型 Agent（如 LangGraph, MCP, AutoGen, CrewAI 等）提供精准的占星数据支撑。

## 功能范围

此 Skill 包支持以下 6 种图盘类型的底层计算与格式化输出：

- **本命盘 (Natal)**：支持基础行星、虚点（南北交点、 Chiron）及主要小行星（Ceres, Pallas, Juno, Vesta）位置与相位计算。
- **比较盘 (Synastry)**：计算双人星盘跨图相位 contacts，并打出匹配得分。
- **组合盘 (Composite)**：使用中点法计算双人关系组合图盘。
- **流年盘 (Transit)**：计算指定流年时间的行运星体与本命星体的相位关系。
- **太阳回归盘 (Solar Return)**：计算太阳回到出生精确度数那一刻的回归图盘。
- **月亮回归盘 (Lunar Return)**：计算月亮回到出生精确度数那一刻的回归图盘。

## 目录结构

```text
vela-skill/
├── pyproject.toml        # 依赖与打包配置文件（基于 uv）
├── SKILL.md              # Agent Skill 入口（含 frontmatter 触发描述）
├── script/               # 计算脚本目录
│   ├── ephe/             # 瑞士星历表数据包（包含 seas_18.se1）
│   ├── _common.py        # 地理、输入及格式化公共辅助函数
│   ├── calculator.py     # 核心计算引擎层（封装 kerykeion / swisseph）
│   ├── geo_service.py    # 地理解析服务（Nominatim + TimezoneFinder）
│   ├── models.py         # Pydantic 校验与数据结构模型定义
│   ├── rectify.py        # 生时校正扫描（仅当用户主动质疑出生时间时使用）
│   └── *_raw_chart.py    # 各种星盘类型的可执行计算命令行入口
├── reference/            # 占星解读参考规范（RAG/上下文注入）
│   ├── delivery.md       # 解读声音（占星师笔法）与交付格式规范
│   ├── examples.md       # 平庸 vs 深刻的对照范文（校准解读深度）
│   ├── ephemeris.md      # 星历计算协议规范
│   ├── retrieval_protocol.md # 可选检索策略
│   └── charts/           # 星盘、星体、宫位、相位深度解读库
└── tests/                # 独立单元测试目录
```

## 宿主集成说明

- **触发机制**：宿主 Agent 通过 `SKILL.md` frontmatter 中的 `name` + `description` 发现并触发本 Skill，请勿删除 frontmatter。
- **拒答策略属于宿主层**：如果产品需要"只聊占星、拒绝编码/新闻/闲聊"之类的路由与拒答策略，请写在宿主 Agent 的 system prompt 中，而不是本 Skill 内——Skill 应保持可复用，不应污染加载它的通用 Agent。
- **地理解析依赖外网**：`geo_service.py` 实时调用 Nominatim（有速率限制）。生产环境建议由宿主预解析经纬度与时区后直接传入，绕过在线 geocoding。

## 输入与输出契约

计算脚本设计为**纯函数**：
- **输入**：从 `stdin` 读取或通过 `--input` 参数传入的结构化 JSON。
- **输出**：计算结果作为 JSON 格式打印输出到 `stdout`。
- **错误处理**：发生 any 异常时，程序将捕获并向 `stdout` 输出 `{"error": "<错误原因>"}` 并以非 0 状态码退出。

### 示例用法

```bash
# 进入 skill 目录
cd vela-skill

# 运行本命盘计算
echo '{"name": "Demo", "birth_date": "1990-01-15T08:30:00", "location": "Beijing, China", "latitude": 39.9042, "longitude": 116.4074, "timezone": "Asia/Shanghai"}' | uv run python script/natal_raw_chart.py
```

## 开发者与测试指南

### 安装依赖

Skill 包要求 Python `>=3.10` 并建议使用 `uv` 运行：

```bash
uv sync --dev
```

### 运行测试

Skill 包包含一个完全独立的自动化测试套件。可运行以下命令验证全部脚本计算逻辑与数据结构契约是否正常：

```bash
uv run pytest tests/
```

## 许可（License）

版权所有 © 2026 DATATECHIE PTY LTD。

本包（包括全部代码与文档）采用 **知识共享 署名-非商业性使用 4.0 国际许可协议 (CC BY-NC 4.0)** 进行许可。详情请参阅 [LICENSE](LICENSE)。

请注意，第三方依赖项（如瑞士星历表数据、kerykeion、pyswisseph）仍受其各自的开源许可协议（AGPL-3.0）约束。
