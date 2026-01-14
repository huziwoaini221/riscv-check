# riscv-check

[English](README.md) | 简体中文

**检测 C/C++ 项目 RISC-V 迁移问题的静态分析工具**

[![PyPI version](https://badge.fury.io/py/riscv-check.svg)](https://pypi.org/project/riscv-check/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## 概述

`riscv-check` 扫描 C/C++ 代码库，检测在 RISC-V 架构上会导致问题的模式：

- 内存对齐问题（RISC-V 上 SIGBUS 崩溃）
- 架构特定的内联汇编
- 缺失 RISC-V 代码路径
- 未对齐的指针转换

## 为什么需要这个工具

### 问题所在

这段代码在 x86_64 上能运行，但在 RISC-V 上会崩溃：

```c
char *p = malloc(10);
p++;
int *i = (int*)p;  // 未对齐地址
*i = 42;  // 在 RISC-V 上 SIGBUS
```

**原因**：x86_64 容忍未对齐访问。RISC-V 要求 int 严格 4 字节对齐。

### 解决方案

`riscv-check` 通过静态分析在迁移**之前**检测这些问题：

```bash
$ riscv-check /path/to/project

[ERROR] src/network.c:128 ALIGN_PTR_CAST
  在不验证对齐的情况下将 char* 转换为 int*
```

## 快速开始

### 安装

```bash
pip install riscv-check
```

### 基本使用

```bash
# 扫描项目
riscv-check /path/to/project

# 生成 maintainer 风格报告（一屏，无 emoji）
riscv-check /path/to/project --output report.md --report-style maintainer

# 跳过交叉编译验证
riscv-check /path/to/project --no-compile
```

### 报告模式

- `--report-style maintainer`（默认）：一屏专业格式
- `--report-style concise`：标准 < 2 屏幕报告
- `--report-style minimal`：仅 bug 报告，< 1 屏幕
- `--report-style verbose`：详细多页报告

### 语言控制

- `--language en`：仅英文（不混用）
- `--language zh`：仅中文

## 检测内容

### 1. 未对齐指针转换

**问题**：将指针转换为更严格的对齐要求

```c
// 错误：在 RISC-V 上会崩溃
char *p = get_buffer();
p++;  // 可能变得未对齐
int *i = (int*)p;  // 需要 4 字节对齐
*i = 42;  // 如果未对齐则 SIGBUS
```

**检测方法**：基于 AST 的静态分析，追踪指针来源和转换目标。

---

### 2. 紧凑结构体访问

**问题**：访问紧凑结构体的非 char 成员

```c
struct __attribute__((packed)) Packet {
    char type;
    int value;  // 未对齐字段
};

int x = packet->value;  // 在 RISC-V 上 SIGBUS
```

**检测方法**：紧凑结构体字段访问模式。

---

### 3. 内联汇编

**问题**：架构特定的汇编代码

```c
// 错误：x86 特定
__asm__ volatile("movq %rax, %rbx");
```

**检测方法**：内联汇编块、架构特定指令。

---

### 4. 架构宏

**问题**：仅在特定架构上编译的代码

```c
#ifdef __x86_64__
    // 缺少 RISC-V 实现
#endif
```

**检测方法**：不平衡的架构特定代码路径。

## 风险评分

**风险分数**：0-100（越高越好）

| 分数 | 状态 | 建议 |
|-------|--------|----------------|
| 80-100 | 推荐 | 可以迁移 |
| 50-79 | 需要修复 | 先修复 ERROR |
| 0-49 | 不推荐 | 崩溃风险高 |

**评分方法**：
- 基础分数：100
- 每个 ERROR：-20 分
- 每个 WARNING：-8 分
- 构建失败：-30 分

## 架构

```
输入：C/C++ 项目
  │
  ├─> 1. 项目扫描器
  │     - 解析 compile_commands.json
  │     - 收集源文件
  │
  ├─> 2. 静态分析 (libclang)
  │     - AST 遍历
  │     - 模式匹配
  │     - 类型检查
  │
  ├─> 3. 交叉编译验证（可选）
  │     - riscv64-linux-gnu-gcc
  │     - 构建错误提取
  │
  └─> 4. 报告生成
        - 控制台输出 (Rich)
        - Markdown 文件
        - Maintainer 格式（一屏）
```

## 环境要求

### 平台支持

| 平台 | 状态 | 备注 |
|----------|--------|-------|
| Linux | 支持 | 主要开发平台 |
| macOS | 支持 | 已测试验证 |
| Windows + WSL 2 | 支持 | Windows 用户推荐 |
| Windows 原生 | 实验性 | 配置复杂 |

### 系统要求

- Python 3.10+
- clang + libclang（用于 AST 解析）
- riscv64-linux-gnu-gcc（可选，用于交叉编译验证）

### 安装

**Ubuntu/Debian**：
```bash
sudo apt install clang llvm libclang-dev
sudo apt install gcc-riscv64-linux-gnu g++-riscv64-linux-gnu
```

**macOS**：
```bash
brew install llvm
brew install riscv-tools
```

## 文档

- [安装指南](docs/INSTALL.md)
- [Windows 安装](docs/INSTALL_WINDOWS.md)
- [使用指南](docs/USAGE.md)
- [架构设计](docs/ARCHITECTURE.md)
- [贡献指南](docs/CONTRIBUTING.md)

## 学习项目：htop (2025-01)

**注意**：本节描述学习经历，非生产部署。

### 背景

作为 MVP 阶段的工具，riscv-check 在 [htop](https://github.com/htop-dev/htop) - 一个维护良好的 C 项目 - 上进行测试，以了解真实代码库中的 RISC-V 迁移挑战。

### 分析详情

**项目**：htop - 交互式进程查看器
- **代码量**：127 个 C 文件，44,524 行
- **分析时间**：约 5 分钟
- **结果**：检测到 1 个对齐问题（后来证实为误报）

### 工具改进历程

**初始问题**：
- 工具生成长篇报告，包含 emoji
- 标记 `xRealloc()` 函数为潜在问题
- 提交 issue：[htop#1858](https://github.com/htop-dev/htop/issues/1858)

**维护者反馈**：
BenBE 和 Explorer09 提供了专业反馈：
- **报告质量**："too verbose"、"lots of emoji"、"reads like AI generated"
- **技术准确性**：建议使用 `__attribute__((malloc))` 而非硬编码函数
- **检测一致性**：指出缺少隐式转换检测

**改进措施**：
- Commit `b9c209d`：实现动态 `__attribute__((malloc))` 检测
- Commit `5a5cde9`：添加隐式转换检测以保持一致性
- Commit `e91e889`：完全重构报告格式
  - Maintainer 风格一屏报告
  - 移除所有 emoji
  - 添加证据等级（E0/E1/E2）
  - 单语言强制

### 经验教训

1. **误报**：`xRealloc()` 案例**不是**真正的问题，因为它内部调用 `realloc()`，而根据 C 标准，`realloc()` 返回对齐的内存。

2. **工具成熟度**：早期版本硬编码项目特定函数。现在使用编译器标准属性以实现可移植性。

3. **报告质量**：维护者友好的报告需要：
   - 简洁（一屏）
   - 无 emoji 或营销话术
   - 基于证据的推理
   - 专业技术写作

### 致谢

特别感谢 htop 维护者：
- **BenBE** - 关于报告质量和格式标准的专业批评
- **Explorer09** - 关于检测准确性的技术建议

他们的专业反馈显著改进了这个工具。详细回复见 [docs/htop_issue_reply.md](docs/htop_issue_reply.md)。

**注意**：该 issue 作为误报关闭。htop 项目没有实际的对齐问题。

## 贡献

欢迎贡献。详见 [CONTRIBUTING.md](docs/CONTRIBUTING.md)。

```bash
# 开发环境设置
git clone https://github.com/huziwoaini221/riscv-check
cd riscv-check
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
black riscv_check/
mypy riscv_check/
```

## 路线图

### v0.1.0（当前 - MVP）
- [x] 未对齐指针转换检测
- [x] 紧凑结构体访问检测
- [x] 内联汇编检测
- [x] 架构特定宏
- [x] 交叉编译验证
- [x] Maintainer 风格报告
- [x] 证据等级分类

### v0.2.0（计划中）
- [ ] QEMU 动态验证
- [ ] CI/CD 管道集成
- [ ] 更多检测规则（原子操作、缓存一致性）

### v0.3.0（未来）
- [ ] Web UI 报告查看
- [ ] 团队协作功能

## 常见问题

**Q：检测准确率如何？**

A：MVP 目标是在 ERROR 级别达到 >90% 精确率。仍会出现误报。工具使用：
- 指针来源追踪
- `__attribute__((malloc))` 检测
- 交叉编译验证

**Q：能处理大型项目吗？**

A：已在 10,000+ 文件的项目上测试。随项目规模线性扩展。

**Q：会修改代码吗？**

A：不会。只读分析和报告。

**Q：如果没有 compile_commands.json 怎么办？**

A：工具可以工作，但精确度会降低。生成方法：
```bash
cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

## 致谢

### 维护者反馈

本工具受益于开源维护者的反馈：

- **BenBE** (htop) - 报告质量标准和维护者期望
- **Explorer09** (htop) - 技术准确性和检测方法

他们的专业反馈推动了报告格式和检测准确性的重大改进。

### 依赖项目

- [clang](https://clang.llvm.org/) - C/C++ 解析和 AST 遍历
- [click](https://click.palletsprojects.com/) - CLI 框架
- [rich](https://rich.readthedocs.io/) - 终端输出格式化
- [RISC-V International](https://riscv.org/) - 架构规范

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 联系方式

- [报告问题](https://github.com/huziwoaini221/riscv-check/issues)
- [功能建议](https://github.com/huziwoaini221/riscv-check/discussions)
- 邮箱：thelazypig321@qq.com

---

**RISC-V 迁移静态分析**

如果这个工具有用，请考虑给项目加星！
