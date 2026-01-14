/* Test file with inline assembly */

void test_inline_asm() {
    int x = 1;

    /* ERROR: ARCH_ASM - x86 inline assembly */
    __asm__ volatile(
        "movl %1, %%eax;"
        "movl %%eax, %0;"
        : "=r" (x)
        : "r" (x)
        : "%eax"
    );
}
