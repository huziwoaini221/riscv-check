# RISC-V 迁移实战项目完整计划

## 📋 项目概述

### 项目目标
使用自研的 `riscv-check` 工具，对一个真实的开源 C/C++ 项目进行 RISC-V 迁移兼容性分析，完整记录整个过程，并将分析结果和改进建议提交给开源社区。

### 核心价值
- **工具验证**：在真实项目中验证 `riscv-check` 的有效性
- **社区贡献**：帮助开源项目提升 RISC-V 兼容性
- **经验积累**：产出完整的 RISC-V 迁移实战案例
- **知识分享**：为 RISC-V 生态提供可复用的迁移流程

### 预期成果
1. **开源项目贡献**：详细的技术分析报告 + 修复建议
2. **技术文档**：完整的迁移实战教程（适合发布到技术社区）
3. **工具改进**：基于实战反馈优化 `riscv-check`
4. **个人能力提升**：静态分析、代码审计、社区协作经验

---

## 🎯 阶段 1：项目选择（预计 1-2 天）

### 1.1 候选项目评估

#### 推荐项目（按优先级排序）

| 项目名 | 代码规模 | 编程语言 | 优先级 | 优势 | 挑战 |
|--------|----------|----------|--------|------|------|
| **htop** | ~10K 行 | C | ⭐⭐⭐⭐⭐ | 知名度高、编译简单、系统工具 | 需要处理 ncurses 依赖 |
| **tldr-c-client** | ~5K 行 | C | ⭐⭐⭐⭐⭐ | 流行工具、依赖少、实用性强 | 代码较简单，检测内容可能较少 |
| **neofetch** | ~3K 行 | Bash/Shell | ⭐⭐⭐⭐ | 极简、流行、社区活跃 | 主要是 Shell 脚本，C 代码少 |
| **json-c** | ~30K 行 | C | ⭐⭐⭐⭐ | 基础库、影响面广 | 代码量较大 |
| **libevent** | ~50K 行 | C | ⭐⭐⭐⭐ | 网络库、重要性高 | 依赖复杂、测试用例多 |
| **redis** | ~100K 行 | C | ⭐⭐⭐ | 知名项目、数据库 | 代码量巨大、架构复杂 |
| **ffmpeg** | ~1M+ 行 | C | ⭐⭐ | 影响力巨大 | 过于复杂、时间投入大 |

#### 最终推荐：**htop**

**选择理由：**
1. ✅ **知名度高**：Linux 用户几乎都知道 htop
2. ✅ **代码规模适中**：~10,000 行 C 代码，2-3 天可以完成分析
3. ✅ **编译简单**：依赖少，构建系统标准（autotools）
4. ✅ **实际价值**：系统监控工具对 RISC-V 很重要
5. ✅ **社区活跃**：GitHub 上有 3.8k+ stars，维护活跃
6. ✅ **有迁移案例**：已有 Debian/RISC-V 移植经验可参考

### 1.2 项目选择验证清单

在确定项目前，确认以下条件：

- [ ] 项目是纯 C/C++ 代码（或主要部分）
- [ ] 项目在 GitHub 上有活跃维护
- [ ] 可以在本地成功编译
- [ ] 可以生成 `compile_commands.json`
- [ ] 代码量在 5K-50K 行之间
- [ ] 项目对 RISC-V 有实际迁移价值
- [ ] 项目有 Issue/PR 机制可以提交分析报告

### 1.3 首选备选方案

如果 htop 分析过程遇到问题，备选项目：
1. **tldr-c-client**（更简单）
2. **json-c**（更复杂，但更基础）

---

## 🛠️ 阶段 2：环境准备（已完成 ✅）

### 2.1 系统环境

```bash
操作系统：Linux Mint 21.x
Python：3.12.3
libclang：18.1.8
工作目录：~/riscv-migration-case-study/
```

### 2.2 工具安装

```bash
# riscv-check 工具
cd ~/r-v/riscv-check
source .venv/bin/activate
pip install -e .

# 验证安装
riscv-check --version
# 输出：riscv-check, version 0.1.0
```

### 2.3 辅助工具

```bash
# 安装 bear（生成 compile_commands.json）
sudo apt-get install bear

# 或使用 intercept-build
sudo apt-get install clang-tools

# 其他有用工具
sudo apt-get install git build-essential autotools-dev autoconf automake
```

---

## 🔍 阶段 3：项目分析与检测（预计 2-3 天）

### 3.1 项目准备

#### 步骤 1：克隆项目

```bash
# 创建工作目录
mkdir -p ~/riscv-migration-case-study
cd ~/riscv-migration-case-study

# 克隆目标项目
git clone https://github.com/htop-dev/htop.git
cd htop

# 记录项目信息
echo "Project: htop" > project-info.txt
echo "Repository: https://github.com/htop-dev/htop" >> project-info.txt
echo "Clone Date: $(date)" >> project-info.txt
echo "Commit: $(git rev-parse HEAD)" >> project-info.txt
git log -1 --format="%H %ai %s" >> project-info.txt
```

#### 步骤 2：编译并生成 compile_commands.json

```bash
# 方法 1：使用 bear（推荐）
bear -- ./autogen.sh
bear -- ./configure
bear -- make

# 方法 2：如果 bear 失败，使用 intercept-build
intercept-build ./autogen.sh
intercept-build ./configure
intercept-build make

# 验证 compile_commands.json 生成
ls -lh compile_commands.json
wc -l compile_commands.json
head -5 compile_commands.json
```

**如果生成失败：**
1. 检查构建系统（CMake 需要导出：`-DCMAKE_EXPORT_COMPILE_COMMANDS=ON`）
2. 手动创建 compile_commands.json（参考 tests/fixtures/）
3. 使用较简单的编译命令记录

#### 步骤 3：项目基本信息收集

```bash
# 统计代码规模
find . -name "*.c" -o -name "*.h" | wc -l
cloc . --include-lang=C --exclude-dir=autom4te.cache

# 查看项目结构
tree -L 2 -I 'autom4te.cache|*.o|*.lo' > project-structure.txt

# 记录依赖
ldd ./htop 2>/dev/null || echo "需要先完全编译"
```

### 3.2 运行 riscv-check 分析

#### 基础分析

```bash
# 运行基本分析
cd ~/riscv-migration-case-study/htop
riscv-check . > htop-analysis.log 2>&1

# 生成详细报告
riscv-check . -v > htop-analysis-verbose.log 2>&1

# 生成 Markdown 报告
riscv-check . -o htop-riscv-report.md

# 查看报告摘要
cat htop-riscv-report.md | head -100
```

#### 分规则分析

```bash
# 只检测对齐问题
riscv-check . --ignore ARCH_ASM --ignore ARCH_MACRO \
  -o htop-alignment-only.md

# 只检测架构依赖
riscv-check . --ignore ALIGN_PTR_CAST --ignore ALIGN_PACKED_FIELD \
  -o htop-arch-only.md
```

### 3.3 问题分类与分析

#### 预期问题类型

| 问题类型 | 规则ID | 严重程度 | 示例 |
|----------|--------|----------|------|
| 内联汇编 | ARCH_ASM | 🔴 ERROR | `__asm__ volatile(...)` |
| 架构特定宏 | ARCH_MACRO | 🟡 WARNING | `#ifdef __x86_64__` |
| 架构特定内置函数 | ARCH_BUILTIN | 🟡 WARNING | `__builtin_ia32_*` |
| 指针对齐问题 | ALIGN_PTR_CAST | 🔴 ERROR | `int* p = (int*)char_ptr` |
| 紧凑结构访问 | ALIGN_PACKED_FIELD | 🔴 ERROR | `packed_struct.int_field` |

#### 问题分析表格

为每个检测到的问题创建记录：

```markdown
## 问题 #N：[问题类型]

### 基本信息
- **文件**：`path/to/file.c`
- **行号**：123
- **列号**：5
- **规则ID**：ARCH_ASM
- **严重程度**：ERROR

### 问题描述
[工具输出的描述]

### 代码上下文
\`\`\`c
// 代码片段（前后10行）
\`\`\`

### 根本原因分析
[为什么会有这个问题？历史背景？技术原因？]

### 修复建议
\`\`\`c
// 修复前
[原始代码]

// 修复后
[修复代码]
\`\`\`

### 验证方法
- [ ] 代码审查
- [ ] 本地编译测试
- [ ] RISC-V 交叉编译测试
- [ ] QEMU 模拟测试
- [ ] 真实硬件测试（可选）

### 优先级评估
- **影响范围**：[核心功能/边缘功能/特定平台]
- **修复难度**：[简单/中等/困难]
- **迁移阻塞**：[是/否]
- **建议优先级**：[P0 必须/P1 重要/P2 可选]
```

### 3.4 手动代码审查

除了工具检测，还需要人工检查：

```bash
# 检查架构特定文件
find . -name "*x86*" -o -name "*i386*" -o -name "*arm*"

# 检查内联汇编
grep -r "__asm__" --include="*.c" --include="*.h"

# 检查架构宏
grep -r "__x86_64__\|__i386__\|__arm__" --include="*.c" --include="*.h"

# 检查 SIMD/向量指令
grep -r "SSE\|AVX\|NEON" --include="*.c" --include="*.h"

# 检查字节序假设
grep -r "LITTLE_ENDIAN\|BIG_ENDIAN" --include="*.c" --include="*.h"
```

---

## 📊 阶段 4：报告生成与整理（预计 1-2 天）

### 4.1 报告结构

创建以下文档结构：

```
~/riscv-migration-case-study/
├── README.md                           # 项目总览
├── 01-项目背景.md                      # 为什么选择 htop
├── 02-环境准备.md                      # 工具安装和配置
├── 03-检测过程.md                      # 完整的分析步骤
├── 04-问题发现.md                      # 检测到的问题列表
├── 05-详细分析.md                      # 每个问题的深入分析
├── 06-修复方案.md                      # 具体的修复建议和代码
├── 07-总结与建议.md                    # 最终结论和后续步骤
├── reports/
│   ├── htop-riscv-full-report.md      # riscv-check 生成的完整报告
│   ├── htop-riscv-summary.md          # 简要总结（给社区）
│   └── htop-risk-matrix.md            # 风险矩阵图
├── data/
│   ├── compile_commands.json          # 编译数据库
│   ├── analysis-verbose.log           # 详细日志
│   └── issues-breakdown.csv           # 问题统计（可选）
└── patches/
    ├── 001-fix-alignment-issue.patch  # 修复补丁示例
    └── 002-replace-asm.patch          # 修复补丁示例
```

### 4.2 各文档详细模板

#### README.md

```markdown
# htop 项目 RISC-V 迁移兼容性分析

## 项目概述

本案例研究使用 `riscv-check` 工具对 [htop](https://github.com/htop-dev/htop)
项目进行了全面的 RISC-V 迁移兼容性分析。

### 分析结果摘要

- **项目**：htop (系统监控工具)
- **代码规模**：~10,000 行 C 代码
- **分析时间**：2026-01-XX
- **风险评分**：XX/100
- **发现问题**：X 个 ERROR，Y 个 WARNING

### 核心发现

1. **内联汇编**：发现 X 处
2. **对齐问题**：发现 Y 处
3. **架构依赖**：发现 Z 处

### 迁移建议

[简短总结]

## 文档导航

- [项目背景](./01-项目背景.md) - 为什么选择 htop
- [环境准备](./02-环境准备.md) - 工具安装和配置
- [检测过程](./03-检测过程.md) - 完整的分析步骤
- [问题发现](./04-问题发现.md) - 检测到的问题列表
- [详细分析](./05-详细分析.md) - 每个问题的深入分析
- [修复方案](./06-修复方案.md) - 具体的修复建议
- [总结建议](./07-总结与建议.md) - 最终结论

## 工具信息

- **工具**：riscv-check v0.1.0
- **GitHub**：https://github.com/yourusername/riscv-check
- **分析者**：[Your Name]
- **联系方式**：[your.email@example.com]

## 许可证

本分析报告采用 CC BY-NC-SA 4.0 许可证
```

#### 01-项目背景.md

```markdown
# 项目背景

## 为什么选择 htop？

### htop 简介

htop 是一个交互式进程监控工具，是 Linux 系统管理员的必备工具之一。
它是传统 `top` 命令的现代化替代品，提供：
- 彩色、图形化的界面
- 直观的键盘操作
- 支持垂直和水平滚动
- 支持杀进程、改变优先级等操作

### 技术栈

- **语言**：C
- **UI 库**：ncurses
- **构建系统**：Autotools (autoconf/automake)
- **平台支持**：Linux, macOS, FreeBSD

### 为什么选择它进行 RISC-V 迁移分析？

#### 1. 实际需求
RISC-V 作为新兴架构，系统监控工具是必需的。htop 作为 Linux
系统的标准工具，支持 RISC-V 对生态发展很重要。

#### 2. 技术代表性
- 使用 ncurses 库（很多命令行工具的依赖）
- 涉及系统调用和进程管理
- 需要处理平台特定的信息读取

#### 3. 代码规模适中
~10,000 行代码，适合：
- 完整分析（2-3 天）
- 详细文档编写
- 生成有价值的报告

#### 4. 社区活跃度
- GitHub Stars: 3.8k+
- 最新版本：3.x
- 活跃维护者
- 有Issue/PR机制

### RISC-V 移植现状

根据调研：
- ✅ Debian 已经有 htop 的 RISC-V 租
- ✅ Gentoo 已经标记为支持
- ❓ 官方尚未正式宣布支持

这意味着我们的分析可以：
1. 验证当前移植的完整性
2. 发现潜在的兼容性问题
3. 提供改进建议

### 预期挑战

1. **平台特定代码**
   - CPU 信息读取（/proc/cpuinfo）
   - 内存信息读取（/proc/meminfo）
   - 硬件计数器访问

2. **对齐问题**
   - ncurses 数据结构访问
   - 系统结构体指针转换

3. **内联汇编**
   - 性能关键路径可能有汇编优化
   - 原子操作实现

## 参考资料

- htop GitHub: https://github.com/htop-dev/htop
- RISC-V 移植指南: https://wiki.gentoo.org/wiki/RISC-V
- Debian RISC-V: https://wiki.debian.org/RISC-V
```

#### 03-检测过程.md

```markdown
# 检测过程

## 环境信息

- **操作系统**：Linux Mint 21.x
- **Python 版本**：3.12.3
- **libclang 版本**：18.1.8
- **riscv-check 版本**：0.1.0
- **分析时间**：2026-01-XX

## 步骤 1：克隆项目

```bash
$ git clone https://github.com/htop-dev/htop.git
$ cd htop
$ git describe --tags
v3.2.2
```

## 步骤 2：生成 compile_commands.json

### 2.1 安装依赖

```bash
$ sudo apt-get update
$ sudo apt-get install -y \\
    build-essential \\
    autoconf \\
    automake \\
    libncursesw5-dev \\
    libncurses5-dev \\
    bear
```

### 2.2 配置和编译

```bash
$ ./autogen.sh
$ ./configure --prefix=/usr
$ bear -- make -j$(nproc)
```

**遇到的问题**：
[记录任何构建问题]

**解决方案**：
[如何解决的]

### 2.3 验证 compile_commands.json

```bash
$ ls -lh compile_commands.json
-rw-r--r-- 1 user user 15K Jan 14 10:00 compile_commands.json

$ jq '. | length' compile_commands.json
42

$ jq '.[0]' compile_commands.json
{
  "directory": "/home/user/riscv-migration-case-study/htop",
  "command": "cc -c -DHAVE_CONFIG_H -I./.. -I/usr/include/ncursesw -o ../htop.o htop.c",
  "file": "/home/user/riscv-migration-case-study/htop/htop/htop.c"
}
```

## 步骤 3：运行 riscv-check

### 3.1 基础分析

```bash
$ riscv-check .

✓ Found 42 files
  Analyzing... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:05

RISC-V Migration Risk Report
==================================================
Project: /home/user/riscv-migration-case-study/htop
Files scanned: 42
Risk Score: XX/100
...
```

### 3.2 详细分析（-v 标志）

```bash
$ riscv-check . -v 2>&1 | tee analysis-verbose.log

✓ Found 42 files
  Analyzing: htop/htop.c
  Analyzing: htop/AvailableMetersPanel.c
  ...
[如果有 AST 解析错误，会在这里显示]
```

### 3.3 生成 Markdown 报告

```bash
$ riscv-check . -o reports/htop-riscv-full-report.md

✓ Full report saved to: reports/htop-riscv-full-report.md
```

## 步骤 4：补充分析

### 4.1 手动检查架构相关代码

```bash
# 检查 x86 特定代码
$ grep -rn "__x86_64__\|__i386__" --include="*.c" --include="*.h"
[输出结果]

# 检查内联汇编
$ grep -rn "__asm__\|asm volatile" --include="*.c" --include="*.h"
[输出结果]
```

### 4.2 检查平台相关文件

```bash
# 查找平台特定目录/文件
$ find . -type d -name "*platform*" -o -name "*arch*"
[输出结果]

$ find . -type f -name "*x86*" -o -name "*arm*"
[输出结果]
```

## 步骤 5：结果收集

### 5.1 报告文件

- `reports/htop-riscv-full-report.md` - 完整报告
- `analysis-verbose.log` - 详细日志
- `compile_commands.json` - 编译数据库

### 5.2 数据统计

```bash
# 统计各类问题数量
$ grep "rule_id" reports/htop-riscv-full-report.md | sort | uniq -c

   X ARCH_ASM
   Y ARCH_MACRO
   Z ALIGN_PTR_CAST
```

## 遇到的问题和解决方案

### 问题 1：[描述]

**现象**：
[具体错误信息]

**原因**：
[根本原因分析]

**解决**：
[解决步骤和命令]

### 问题 2：[描述]

...

## 经验总结

1. **compile_commands.json 的关键性**
   - 必须正确生成，否则 AST 分析会失败
   - bear 在某些构建系统上可能不工作

2. **详细模式的重要性**
   - `-v` 标志可以看到 AST 解析错误
   - 有助于理解为什么某些代码没被检测到

3. **人工审查的必要性**
   - 工具可能遗漏一些平台相关代码
   - 需要结合 grep 和人工检查

## 下一步

- [ ] 详细分析每个问题
- [ ] 提出修复方案
- [ ] 准备社区报告
```

### 4.3 问题统计表格

创建一个 CSV 或 Markdown 表格：

```markdown
| 问题ID | 文件 | 行号 | 类型 | 严重程度 | 优先级 | 状态 |
|--------|------|------|------|----------|--------|------|
| 1 | htop/Platform.c | 123 | ARCH_ASM | ERROR | P0 | 待修复 |
| 2 | htop/CPUCount.c | 45 | ALIGN_PTR_CAST | ERROR | P1 | 待修复 |
| ... | ... | ... | ... | ... | ... | ... |
```

---

## 🔧 阶段 5：修复方案设计（预计 1-2 天）

### 5.1 修复优先级

**P0 - 必须修复（迁移阻塞）**
- 内联汇编（无替代方案）
- 关键路径上的对齐问题
- 架构特定宏（影响核心功能）

**P1 - 重要修复（影响功能）**
- 边缘功能的对齐问题
- 性能优化相关的架构依赖

**P2 - 可选修复（优化建议）**
- 代码清理
- 更好的可移植性

### 5.2 修复模板

为每个 P0/P1 问题创建修复方案：

```markdown
## 修复方案：问题 #N

### 问题描述
[文件:行号] ARCH_ASM: 内联汇编不兼容

### 当前代码

```c
// htop/Platform.c:123
static inline uint64_t rdtsc(void) {
    uint32_t lo, hi;
    __asm__ __volatile__ ("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
}
```

### 问题分析

这段代码使用 x86 特定的 `rdtsc` 指令读取时间戳计数器，
在 RISC-V 上无法运行。

### 修复方案

#### 方案 1：使用 clock_gettime（推荐）

```c
#include <time.h>

static inline uint64_t rdtsc(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}
```

**优点**：
- 完全可移植
- 标准 POSIX 接口
- RISC-V 完全支持

**缺点**：
- 性能略低于 rdtsc（但如果不是热点路径可接受）

**测试方法**：
```bash
# 编译测试
gcc -Wall -Wextra -o test test.c

# x86_64 上测试
./test

# RISC-V 交叉编译
riscv64-linux-gnu-gcc -Wall -Wextra -o test test.c
```

#### 方案 2：条件编译（如果需要保留 x86 性能）

```c
#include <time.h>

static inline uint64_t rdtsc(void) {
#if defined(__x86_64__) || defined(__i386__)
    uint32_t lo, hi;
    __asm__ __volatile__ ("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
#else
    // RISC-V 和其他架构
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
#endif
}
```

**优点**：
- 保留 x86 性能
- RISC-V 可用

**缺点**：
- 代码复杂度增加
- 需要在多个平台上测试

### 推荐方案

**方案 1**（使用 clock_gettime）

理由：
1. htop 不是性能关键型应用（监控工具）
2. 时钟读取不是热点路径
3. 代码更简洁可维护

### 测试计划

1. **编译测试**
   ```bash
   # 本地测试
   make clean && make

   # RISC-V 交叉编译
   riscv64-linux-gnu-gcc -c Platform.c -I/usr/include
   ```

2. **功能测试**
   ```bash
   # 运行 htop
   ./htop

   # 检查 CPU 占用率显示是否正常
   # 检查进程列表更新是否正常
   ```

3. **回归测试**
   - 确保没有引入新 bug
   - 性能无明显退化

### 提交 PR 前的检查清单

- [ ] 代码编译通过（x86_64）
- [ ] 代码编译通过（RISC-V 交叉编译）
- [ ] 功能测试通过
- [ ] 代码符合项目风格
- [ ] 添加了必要的注释
- [ ] 更新了相关文档（如果需要）

### 预期效果

修复后，htop 可以在 RISC-V 平台上正常编译和运行，CPU
监控功能正常工作。
```

---

## 📤 阶段 6：社区提交（预计 1 天）

### 6.1 准备材料

#### 给社区的压缩报告（htop-riscv-summary.md）

```markdown
# htop RISC-V Migration Compatibility Analysis

## Executive Summary

I've analyzed htop v3.2.2 using the `riscv-check` tool to assess
RISC-V migration readiness.

### Key Findings

| Metric | Value |
|--------|-------|
| Risk Score | XX/100 |
| Critical Issues (ERROR) | X |
| Warnings (WARNING) | Y |
| Migration Readiness | [READY/NEEDS WORK/NOT READY] |

### Critical Blockers

1. **Inline Assembly (X instances)**
   - Files: `Platform.c:123`, `CRT.c:45`
   - Impact: CPU timestamp reading
   - Fix: Replace with `clock_gettime()`

2. **Pointer Alignment (Y instances)**
   - Files: `ProcessTable.c:789`
   - Impact: Potential SIGBUS on RISC-V
   - Fix: Use memcpy for type-punning

3. **Architecture Macros (Z instances)**
   - Files: `Arch.h`, `Config.c`
   - Impact: Platform detection
   - Fix: Add `__riscv` macro support

## Proposed Fixes

Detailed fix proposals are available in the full report.
Summary of changes:

- [ ] Replace `rdtsc` with `clock_gettime` (2 locations)
- [ ] Fix misaligned pointer casts (3 locations)
- [ ] Add RISC-V to platform detection (1 location)

## Testing

All fixes have been validated:
- ✅ Compiles on x86_64 (current)
- ✅ Cross-compiles for Riscv64 (tested)
- ✅ Functional testing passed
- ✅ No performance regression

## Next Steps

I'm ready to submit pull requests with the fixes.
Feedback on prioritization is welcome.

## Full Report

[Link to detailed analysis document]

## Tools Used

- **riscv-check** v0.1.0: https://github.com/yourusername/riscv-check
- Analysis performed: 2026-01-XX
- libclang version: 18.1.8

---

**Author**: [Your Name]
**Contact**: [your.email@example.com]
**License**: This analysis is submitted under the same license as htop (GPL-2.0)
```

### 6.2 提交策略

#### 选项 A：GitHub Issue（推荐，如果项目较大）

1. **创建 Issue**
   - 标题：`[RFC] RISC-V Migration Compatibility Analysis`
   - 标签：`enhancement`, `risc-v`, `portability`
   - 内容：粘贴上面的压缩报告

2. **等待反馈**
   - 维护者的意见
   - 社区讨论
   - 优先级排序

3. **提交 PR**
   - 基于 Issue 的讨论结果
   - 一次修复一个或一类问题
   - 引用 Issue

#### 选项 B：直接提交 PR（如果项目较小/维护者友好）

1. **Fork 仓库**
   ```bash
   # 在 GitHub 上 fork htop/htop
   git clone https://github.com/YOUR_USERNAME/htop.git
   cd htop
   git remote add upstream https://github.com/htop-dev/htop.git
   ```

2. **创建分支**
   ```bash
   git checkout -b riscv-fix-alignment
   # 或
   git checkout -b riscv-replace-rdtsc
   ```

3. **应用修复**
   ```bash
   # 编辑文件
   vim Platform.c

   # 测试
   make clean && make

   # 提交
   git add Platform.c
   git commit -m "Fix: Replace x86 rdtsc with portable clock_gettime

   This change enables htop to build and run on RISC-V architecture.

   - Replaces x86-specific rdtsc instruction with POSIX clock_gettime
   - Maintains compatibility with x86_64 and other platforms
   - No performance regression observed

   Fixes: #[issue-number]"
   ```

4. **推送并创建 PR**
   ```bash
   git push origin riscv-replace-rdtsc
   # 然后在 GitHub 上创建 Pull Request
   ```

#### PR 描述模板

```markdown
## Purpose
Enable htop to build and run on RISC-V architecture.

## Changes
- Replace x86-specific `rdtsc` with POSIX `clock_gettime`
- Tested on x86_64 (no regression)
- Cross-compiled for RISC-V (successful)

## Testing
```bash
# Build test on x86_64
$ ./autogen.sh && ./configure && make
$ ./htop  # Works as expected

# Cross-compile for RISC-V
$ riscv64-linux-gnu-gcc -c Platform.c -I/usr/include
$ # Success
```

## Context
Part of RISC-V migration effort. See full analysis: [link to Issue/Doc]

## Checklist
- [x] Code compiles on x86_64
- [x] Code compiles on RISC-V (cross-compile)
- [x] No functional regression
- [x] Follows project code style
- [x] Commit message is clear
```

### 6.3 社区沟通技巧

#### 积极的开场
> "Hi htop team, I'm working on improving RISC-V support for open-source tools.
> I've analyzed htop with a static analysis tool and found some opportunities to
> improve portability. I'd like to contribute fixes."

#### 展示价值
> "These changes will enable htop to work on the growing RISC-V ecosystem,
> including Debian/RISC-V and Fedora/RISC-V ports."

#### 尊重现有代码
> "I understand these optimizations were made for x86 performance. I've tested
> that the portable alternatives don't cause regression on x86_64."

#### 愿意迭代
> "I'm happy to adjust the approach based on your feedback. What do you think
> is the best way to handle this?"

#### 处理拒绝
如果维护者不接受：
1. 询问具体原因
2. 提供替代方案
3. 如果仍被拒绝，礼貌接受
4. 将分析作为独立文档发布（博客/Gist）

---

## 📝 阶段 7：文档产出与分享（预计 1-2 天）

### 7.1 技术博客/文章

#### 推荐发布平台

**中文社区：**
- 掘金（juejin.cn）
- 知乎专栏
- CSDN
- 个人博客

**英文社区：**
- Medium
- Dev.to
- Hacker Noon
- Personal blog

#### 文章大纲

**标题示例：**
- "使用静态分析工具助力 htop 迁移到 RISC-V"
- "RISC-V 移植实战：htop 兼容性分析与修复"
- "开源项目 RISC-V 移植指南：以 htop 为例"

**文章结构：**

```markdown
# [标题]

## 摘要
[200-300字概括全文]

## 1. 背景介绍
- RISC-V 生态现状
- 为什么需要迁移工具
- 选择 htop 的原因

## 2. 工具介绍
- riscv-check 工具原理
- 检测能力
- 使用方法

## 3. 检测过程
### 3.1 环境准备
### 3.2 编译配置
### 3.3 运行分析
### 3.4 问题发现

## 4. 问题分析
### 4.1 内联汇编问题
- 问题代码
- 根本原因
- 修复方案

### 4.2 对齐问题
- 问题描述
- 为什么 RISC-V 对齐严格
- 修复方案

### 4.3 架构依赖
- 平台检测代码
- 可移植改进

## 5. 修复实施
- 具体代码修改
- 编译测试
- 功能验证

## 6. 结果与展望
- 修复前后对比
- 风险评分变化
- 后续工作

## 7. 经验总结
- 工具使用的经验教训
- 社区协作的心得
- 对 RISC-V 生态的建议

## 8. 参考资料
- 项目链接
- 工具 GitHub
- RISC-V 官方资源
```

#### 写作建议

1. **图文并茂**
   - 截图：htop 运行界面
   - 代码对比：Before/After 高亮
   - 表格：问题统计、优先级

2. **代码示例**
   ```markdown
   ```c
   // 修复前
   __asm__ volatile("rdtsc" : ...);

   // 修复后
   clock_gettime(CLOCK_MONOTONIC, &ts);
   ```
   ```

3. **命令记录**
   ```markdown
   ```bash
   $ riscv-check . -o report.md
   ✓ Found 42 files
   ✓ Analysis complete
   ```
   ```

4. **数据可视化**
   - 风险评分对比图
   - 问题分布饼图
   - 修复进度甘特图

### 7.2 视频教程（可选）

如果愿意出镜，可以制作视频：

**平台：**
- Bilibili（中文）
- YouTube（英文）

**内容大纲：**
1. RISC-V 和工具介绍（5 分钟）
2. 环境配置演示（5 分钟）
3. 分析过程演示（10 分钟）
4. 代码修复演示（10 分钟）
5. 总结和展望（5 分钟）

**总时长：** ~35 分钟

### 7.3 开源发布

#### GitHub 仓库

创建公共仓库托管所有材料：

```bash
# 创建仓库
mkdir ~/htop-riscv-migration
cd ~/htop-riscv-migration
git init

# 添加文件
cp -r ~/riscv-migration-case-study/* .

# 创建 README
cat > README.md << 'EOF'
# htop RISC-V Migration Project

Complete documentation of RISC-V migration compatibility analysis
for the htop project.

## Quick Links

- [Full Report](./reports/htop-riscv-full-report.md)
- [Summary](./reports/htop-riscv-summary.md)
- [Blog Post](./blog-post.md)
- [Fix Proposals](./06-修复方案.md)

## About

This project demonstrates the use of static analysis tools for
RISC-V migration readiness assessment.

## Tools Used

- riscv-check v0.1.0
- libclang 18.1.8
- Linux Mint 21.x

## License

CC BY-NC-SA 4.0

## Contact

[Your Name] - [your.email@example.com]
EOF

# 推送到 GitHub
git remote add origin https://github.com/YOUR_USERNAME/htop-riscv-migration.git
git add .
git commit -m "Initial commit: htop RISC-V migration analysis"
git push -u origin main
```

---

## ⏱️ 时间规划

### 总体时间线

| 阶段 | 预计时间 | 实际时间 | 完成日期 | 备注 |
|------|----------|----------|----------|------|
| 项目选择 | 1-2 天 | ___ | ___ | 选择 htop |
| 环境准备 | 0.5 天 | ✅ 已完成 | 2026-01-14 | 工具已安装 |
| 项目克隆与编译 | 0.5 天 | ___ | ___ | 生成 compile_commands.json |
| 运行分析 | 0.5 天 | ___ | ___ | riscv-check 检测 |
| 问题分析 | 1-2 天 | ___ | ___ | 深入分析每个问题 |
| 修复方案设计 | 1-2 天 | ___ | ___ | 编写修复代码 |
| 报告编写 | 1-2 天 | ___ | ___ | 文档整理 |
| 社区提交 | 1 天 | ___ | ___ | Issue/PR |
| 文章发布 | 1-2 天 | ___ | ___ | 博客/视频 |
| **总计** | **8-14 天** | ___ | ___ | 约 2 周 |

### 每日计划

**Day 1-2：项目准备**
- [ ] 克隆 htop
- [ ] 编译并生成 compile_commands.json
- [ ] 运行 riscv-check
- [ ] 整理初步结果

**Day 3-4：问题分析**
- [ ] 详细分析每个问题
- [ ] 手动代码审查
- [ ] 确定修复优先级

**Day 5-6：修复方案**
- [ ] 编写 P0 问题修复代码
- [ ] 本地测试
- [ ] RISC-V 交叉编译测试

**Day 7-8：报告编写**
- [ ] 编写各阶段文档
- [ ] 生成最终报告
- [ ] 制作问题统计表

**Day 9：社区提交**
- [ ] 准备 Issue/PR 材料
- [ ] 提交到 htop 仓库
- [ ] 等待反馈

**Day 10-12：文档产出**
- [ ] 编写技术博客
- [ ] 制作视频（可选）
- [ ] 发布到社区

**Day 13-14：总结与后续**
- [ ] 整理经验教训
- [ ] 规划下一步工作
- [ ] 回复社区反馈

---

## 📈 成功标准

### 技术指标

- [x] **工具可用性**：riscv-check 能成功运行
- [ ] **检测准确性**：发现的 80% 以上问题经过验证
- [ ] **修复可行性**：所有 P0 问题有可执行的修复方案
- [ ] **编译通过**：修复后代码能在 x86_64 和 RISC-V 上编译

### 社区指标

- [ ] **Issue/PR 被接受**：htop 维护者认可分析价值
- [ ] **修复被合并**：至少一个修复被合并到上游
- [ ] **正向反馈**：社区给出积极评价
- [ ] **引发讨论**：带动 RISC-V 移植话题讨论

### 个人成长指标

- [ ] **完整文档**：产出 7 篇以上文档
- [ ] **技术博客**：发布 1 篇高质量博客
- [ ] **工具改进**：基于实战反馈优化 riscv-check
- [ ] **社区影响力**：GitHub stars/issues/mentions 增加

---

## 🎓 预期收获

### 技术能力提升

1. **静态分析技术**
   - 理解 AST（抽象语法树）
   - 掌握 clang API
   - 学习代码审计方法

2. **RISC-V 架构知识**
   - 理解 RISC-V 与 x86/ARM 的差异
   - 掌握对齐和内存模型
   - 学习 RISC-V 汇编和 intrinsic

3. **跨平台开发**
   - 理解可移植性编程
   - 学习条件编译和平台抽象
   - 掌握交叉编译工具链

4. **软件工程实践**
   - 完整的项目文档
   - 系统的问题分析
   - 代码重构和修复

### 社区协作经验

1. **开源贡献流程**
   - Issue/PR 最佳实践
   - 代码评审经验
   - 社区沟通技巧

2. **技术写作**
   - 技术博客写作
   - 文档组织能力
   - 知识分享经验

3. **个人品牌**
   - GitHub 活跃度
   - 技术影响力
   - RISC-V 生态参与

---

## ⚠️ 风险与应对

### 技术风险

#### 风险 1：无法生成 compile_commands.json

**概率**：中等

**影响**：无法进行 AST 分析，检测能力下降 50%

**应对**：
1. 尝试不同的编译数据库生成工具（bear, intercept-build）
2. 手动创建 compile_commands.json
3. 退回到纯文本分析（宏、内联汇编）

#### 风险 2：htop 已经完全支持 RISC-V

**概率**：低

**影响**：分析可能没有价值

**应对**：
1. 选择其他项目（json-c, tldr）
2. 重新定位为"验证已有移植的完整性"
3. 分析其他 RISC-V 移植问题

#### 风险 3：修复方案被维护者拒绝

**概率**：中等

**影响**：时间投入可能无法转化为 PR

**应对**：
1. 以学习为主，PR 为辅
2. 将分析报告独立发布
3. 改进工具后重新分析

### 时间风险

#### 风险 1：问题比预期多

**概率**：中等

**应对**：
1. 专注于 P0 问题
2. 限制分析范围（核心模块）
3. 延长项目周期

#### 风险 2：社区反馈慢

**概率**：高

**应对**：
1. 不等待反馈，先完成其他产出
2. 同时提交到多个平台
3. 设置合理的期望

---

## 📚 参考资料

### RISC-V 相关

- [RISC-V 官方网站](https://riscv.org/)
- [RISC-V 国际规范](https://github.com/riscv/riscv-isa-manual)
- [Debian RISC-V 移植](https://wiki.debian.org/RISC-V)
- [Gentoo RISC-V 项目](https://wiki.gentoo.org/wiki/RISC-V)

### 工具相关

- [riscv-check GitHub](https://github.com/yourusername/riscv-check)
- [libclang 文档](https://clang.llvm.org/doxygen/group__CINDEX.html)
- [clang Python 绑定](https://github.com/llvm-mirror/clang/tree/master/bindings/python)

### 开源实践

- [如何向开源项目提交 PR](https://opensource.guide/how-to-contribute/)
- [开源社区沟通礼仪](https://opensource.guide/community-ettiquette/)
- [技术博客写作指南](https://dev.to/middleton/tech-blogging-best-practices-5f5g)

### 静态分析

- [《静态分析的艺术》](https://www.amazon.com/Art-Static-Analysis-Building-Secure/dp/0321809452)
- [Clang AST 遍历教程](https://jonasdevlieghere.com/unorderedness/clang-ast/)

---

## 🎯 立即开始

### 今天就可以做的事

```bash
# 1. 创建工作目录
mkdir -p ~/riscv-migration-case-study
cd ~/riscv-migration-case-study

# 2. 克隆 htop
git clone https://github.com/htop-dev/htop.git
cd htop

# 3. 安装依赖
sudo apt-get update
sudo apt-get install -y build-essential autoconf automake \\
    libncursesw5-dev libncurses5-dev bear

# 4. 编译并生成 compile_commands.json
./autogen.sh
./configure
bear -- make

# 5. 验证
ls compile_commands.json

# 6. 运行分析
cd ~/r-v/riscv-check
source .venv/bin/activate
riscv-check ~/riscv-migration-case-study/htop \\
  -o ~/riscv-migration-case-study/reports/initial-report.md \\
  -v

# 7. 查看结果
cat ~/riscv-migration-case-study/reports/initial-report.md
```

### 第一次会议记录模板

创建 `01-meeting-notes.md`：

```markdown
# 项目启动会议

**日期**：2026-01-14
**参与者**：[Your Name]

## 会议目标

启动 htop RISC-V 迁移分析项目

## 讨论内容

### 1. 项目确认
- ✅ 目标项目：htop
- ✅ 工具：riscv-check v0.1.0
- ✅ 时间预期：2 周

### 2. 成功标准
- 检测所有 RISC-V 兼容性问题
- 提供可执行的修复方案
- 向上游提交 PR

### 3. 产出计划
- 7 篇技术文档
- 1 篇技术博客
- 完整的分析报告

### 4. 下一步行动
- [ ] 完成 htop 克隆和编译
- [ ] 运行 riscv-check 分析
- [ ] 创建文档结构

## 风险识别

- compile_commands.json 生成可能失败
- htop 可能已经支持 RISC-V
- 修复方案可能被拒绝

## 行动项

| 任务 | 负责人 | 截止日期 |
|------|--------|----------|
| 克隆并编译 htop | [Name] | 2026-01-15 |
| 生成 compile_commands.json | [Name] | 2026-01-15 |
| 运行初步分析 | [Name] | 2026-01-15 |
```

---

## 🎉 结语

这个项目是一个绝佳的机会，可以：
- ✅ 验证自研工具的实战能力
- ✅ 为开源社区做贡献
- ✅ 学习 RISC-V 架构知识
- ✅ 积累跨平台开发经验
- ✅ 产出高质量的技术内容

**最重要的是：这是一个完整的、可执行的计划，不是空谈。**

让我们开始吧！🚀

---

**文档版本**：v1.0
**最后更新**：2026-01-14
**作者**：[Your Name]
**联系方式**：[your.email@example.com]
