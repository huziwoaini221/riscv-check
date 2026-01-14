# 专业 Issue 报告模板

> 符合开源维护者期望的标准
> 参考：BenBE (htop maintainer) 的反馈

---

## 📋 报告标准（基于维护者反馈）

### ❌ 避免的格式

1. **太长** - 前 3 屏都是废话
2. **混用语言** - 中英混合
3. **过多 emoji** - 像 AI 生成的
4. **冗余文本** - 重复啰嗦
5. **营销话术** - "额外内容"像 FAQ
6. **AI 风格** - ChatGPT 生成的感觉

### ✅ 期望的格式

1. **简洁** - 直奔主题
2. **单语言** - 纯英文（或纯中文）
3. **无 emoji** - 专业、干练
4. **技术性** - 专注于问题
5. **推理清晰** - Coverity 风格
6. **有根据** - 每个声明都有证据

---

## 🎯 新的 Issue 报告模板

### 模板 1：发现真实 bug 时使用

```markdown
## Title
[Misaligned pointer access at FILE:LINE]

## Issue Description

Function NAME returns TYPE* but code at FILE:LINE casts it to TYPE2*,
which may cause SIGBUS on RISC-V due to alignment requirements.

## Affected Code

```c
// File: FILE, Line: LINE
void* ptr = function_returning_void_ptr();
TYPE2* typed_ptr = (TYPE2*)ptr;  // ← Misalignment
```

## Alignment Analysis

- Source type: TYPE (alignment: X bytes)
- Target type: TYPE2 (alignment: Y bytes)
- Requirement: Y > X, violates alignment

## Impact

On RISC-V architecture:
- x86: Tolerates misalignment (works by accident)
- RISC-V: Strict alignment, triggers SIGBUS

## Proposed Fix

```c
// Option 1: Use memcpy
TYPE2* typed_ptr = memcpy(&tmp, ptr, sizeof(TYPE2));

// Option 2: Ensure alignment
__attribute__((aligned(Y))) TYPE2* typed_ptr = (TYPE2*)ptr;
```

## Verification

Compile with:
```bash
gcc -fsanitize=alignment -o test test.c
./test  # Should fail on RISC-V
```

Or test with:
```bash
qemu-riscv64 ./test  # Should trigger SIGBUS
```

## Environment

- Compiler: GCC X.X / Clang X.X
- Architecture: x86_64 (development), RISC-V (target)
- Project: PROJECT_NAME
- Version: VERSION

## References

- RISC-V alignment requirements: [link]
- Similar issues: [link if any]

---
```

---

### 模板 2：工具改进建议时使用

```markdown
## Title
[Tool suggestion] Detect misaligned pointer casts for RISC-V migration

## Summary

Static analysis tool to detect C/C++ code patterns that work on x86
but crash on RISC-V due to misaligned memory access.

## Problem Statement

RISC-V architecture requires strict memory alignment:
- char* → int* cast: SIGBUS if char* is not 4-byte aligned
- x86 tolerates this, RISC-V doesn't
- Manual code review is time-consuming

## Proposed Tool

Detects:
1. Misaligned pointer casts
2. Packed struct member access
3. Inline assembly
4. Architecture-specific macros

## Example Detection

Input:
```c
char buffer[100];
buffer++;
int* p = (int*)buffer;  // Misaligned
```

Output:
```
ERROR: test.c:3: Casting char* (align=1) to int* (align=4)
```

## Technical Approach

1. Parse AST using libclang
2. Check alignment requirements of source and target types
3. Verify pointer sources (malloc/calloc vs arbitrary buffers)
4. Report violations

## Validation

Analyzed projects:
- htop: 44K LOC, found issues, tool improved based on feedback
- [Future]: More projects

## Questions

1. Would such a tool be helpful for RISC-V migration?
2. Should I analyze other projects?
3. Any feedback on the approach?

## Repository

github.com/huziwoaini221/riscv-check

---
```

---

### 模板 3：简短技术讨论时使用

```markdown
@maintainer Quick question about CODE_PATTERN in FILE:

Line XX does PATTERN. I'm concerned about RISC-V compatibility because:
- Reason 1
- Reason 2

Should this be changed to ALTERNATIVE?

Thanks

---
```

---

## 📏 报告长度控制

### 理想长度

```
Title: 1 行（10-20 字）
Description: 2-3 段（每段 2-3 行）
Code: 最小化示例
Analysis: 1 段
Impact: 1 段
Fix: 1-2 个选项
Total: ~1-2 屏幕高度
```

### ❌ 避免的冗余

```markdown
❌ 不要：
- 3 屏幕的"背景介绍"
- 重复相同观点 3 次
- 列出 10 个"为什么重要"
- FAQ 部分
- "额外阅读材料"
- 感叹号和 emoji
- 营销话术（"革命性工具"、"突破性方法"）
```

---

## 🔍 推理链条（Coverity 风格）

### 正确的推理顺序

```
1. Show code
   ↓
2. Explain alignment requirements
   ↓
3. Show violation
   ↓
4. Explain impact on RISC-V
   ↓
5. Provide fix
```

### ❌ 不要的推理顺序

```
1. Talk about RISC-V importance
2. Discuss tool capabilities
3. Show examples
4. Finally show the actual bug
```

---

## 📝 报告检查清单

### 提交前检查

- [ ] 报告 < 2 屏幕高度
- [ ] 单语言（不混用）
- [ ] 无 emoji
- [ ] 第一段就说明问题
- [ ] 代码最小化（只显示相关部分）
- [ ] 每个声明都有证据
- [ ] 推理链条清晰
- [ ] 提供了可验证的测试方法
- [ ] 检查所有链接可用
- [ ] 人工审查过（不是 AI 直接生成）

---

## 🎯 对比示例

### ❌ 之前（被 BenBE 批评的）

```markdown
# 🚀 使用 riscv-check 工具发现 RISC-V 兼容性问题

## 📖 背景介绍

RISC-V 是一个开放的指令集架构...（3 屏废话）

## 🔧 工具介绍

riscv-check 是一个革命性的工具...（营销话术）

## 🎯 案例分析

我们分析了 htop 项目...（冗长）

## ❌ 发现的问题

在 XUtils.c 的第 163 行...（终于到重点了）

## 💡 修复建议

...（错误的修复）

## 🙏 FAQ

...（更多废话）

## 📚 额外阅读

...（更多链接）

Total: 5+ screens, lots of emojis, mixed languages
```

### ✅ 改进后（符合标准的）

```markdown
# Misaligned pointer cast in XUtils.c:163

## Issue

Function xRealloc returns void* but code at line 163 casts it to char**
without verifying alignment, which may cause SIGBUS on RISC-V.

## Affected Code

```c
// XUtils.c:163
out = (char**)xRealloc(out, sizeof(char*) * blocks);
```

## Analysis

- xRealloc returns void* (unknown alignment)
- Cast to char** (8-byte alignment required on 64-bit)
- RISC-V requires strict alignment, triggers SIGBUS if violated

## Note

Upon further review, xRealloc internally calls realloc() which returns
aligned memory, so this is a false positive. The tool has been updated
to detect __attribute__((malloc)) to avoid such issues.

## Status

False positive - not a real issue. Tool improved based on feedback.

Total: 20 lines, no emojis, clear reasoning
```

---

## 🚫 AI 生成检测特征

### BenBE 说"看起来像 AI 生成的"

**避免这些模式**：

1. **过度结构化**
```markdown
❌
## 🎯 Executive Summary
## 💡 Key Insights
## 🔍 Deep Dive
## 🚀 Call to Action

✅
## Problem
## Analysis
## Solution
```

2. **过度热情**
```markdown
❌
"This revolutionary tool will transform..."
"Exciting breakthrough in..."
"Game-changing approach..."

✅
"Tool detects X by doing Y"
"Proposed fix: Z"
```

3. **重复强调**
```markdown
❌
"Important! Very important! Really important!"
"As mentioned earlier, as stated above, as previously noted..."

✅
"Important: [statement]"
（只说一次）
```

4. **模糊技术术语**
```markdown
❌
"Leverage cutting-edge AI technology"
"Utilize advanced machine learning algorithms"

✅
"Parses AST using libclang"
"Checks alignment at compile time"
```

---

## 📊 未来的报告流程

### 步骤 1：发现问题

```
工具检测到潜在问题
↓
AI 生成初稿
```

### 步骤 2：人工审查

```
人工检查：
1. 这是否真实问题？
2. 推理是否清晰？
3. 报告是否简洁？
4. 是否有根据？
```

### 步骤 3：精简报告

```
应用模板：
1. 删除所有 emoji
2. 删除冗余段落
3. 确保单语言
4. 检查推理链条
5. 验证所有链接
6. 测试长度（< 2 屏幕）
```

### 步骤 4：最终检查

```
检查清单：
- [ ] < 2 screens
- [ ] No emojis
- [ ] Single language
- [ ] First paragraph has the point
- [ ] Evidence for every claim
- [ ] Tested fix
- [ ] All links work
```

### 步骤 5：提交

```
只有通过所有检查后才提交
```

---

## 💡 关键原则

### 1️⃣ 简洁 > 详细

```
❌ "This is a very important issue that needs to be addressed
immediately because it can cause serious problems..."

✅ "Issue causes SIGBUS on RISC-V at FILE:LINE"
```

### 2️⃣ 证据 > 声明

```
❌ "This won't work on RISC-V"

✅ "RISC-V requires 8-byte alignment for int64*, current code
provides 4-byte alignment (tested with qemu-riscv64)"
```

### 3️⃣ 代码 > 文字

```
❌ Describe the code in 3 paragraphs

✅ Show minimal code example (5 lines)
```

### 4️⃣ 一步到位 > 渐进式

```
❌
## Background
## Introduction
## Overview
## The Issue
## Details

✅
## Issue
[Brief description]
[Code]
[Analysis]
[Fix]
```

---

## 🎓 学习资源

### 好的 Issue 报告示例

1. **Coverity Reports** - 行业标准
2. **Linux Kernel Mailing List** - 技术邮件列表
3. **GCC Bugzilla** - 编译器 bug 报告

### 特点

- 第一句话就说清楚问题
- 最小化代码示例
- 清晰的推理链条
- 可验证的测试方法
- 简洁、专业、无废话

---

## 📝 实践练习

### 练习 1：重写 htop 报告

**原报告**：5+ 屏幕，emoji，混用语言

**改进后**（20 行）：
```
# Tool improvement suggestion based on htop analysis

## Summary

Static analysis tool for RISC-V migration detected false positive
in htop XUtils.c:163. Tool has been improved to use
__attribute__((malloc)) detection instead of hardcoding functions.

## What happened

Initial analysis flagged:
```c
out = (char**)xRealloc(out, sizeof(char*) * blocks);
```

Issue: xRealloc returns aligned pointer (via realloc), so this
is safe. Tool's hardcoded whitelist was not scalable.

## Improvements made

1. Added __attribute__((malloc)) detection
2. Removed project-specific functions from whitelist
3. Now works with any project using malloc attribute

Commits: 600bcad, 5a5cde9, b9c209d

## Questions

Any feedback on the approach? Other cases to consider?

---
```

---

## ✅ 最终标准

### 完美的 Issue 报告 =

1. **标题** - 一句话说明问题
2. **问题描述** - 2-3 句话
3. **代码** - 最小化示例
4. **分析** - 清晰推理
5. **影响** - 为什么重要
6. **修复** - 可行方案
7. **验证** - 如何测试
8. **长度** - < 2 屏幕
9. **风格** - 无 emoji，单语言
10. **质量** - 人工审查过

---

**使用这个模板，未来的报告将会被认真对待！** 🎯
