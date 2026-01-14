/* Test file with architecture-specific macros */

/* ERROR: ARCH_MACRO - x86_64 specific */
#ifdef __x86_64__
int x86_only_function() {
    return 42;
}
#endif

/* ERROR: ARCH_MACRO - ARM specific */
#ifdef __arm__
int arm_only_function() {
    return 43;
}
#endif

/* Portable code */
int portable_function() {
    return 44;
}
