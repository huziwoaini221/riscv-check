/* Test file with safe pointer casts */

#include <stdlib.h>

void test_safe_cast_1() {
    int *p = malloc(sizeof(int));
    int *i = (int*)p;  /* OK: same alignment */
    *i = 42;
    free(p);
}

void test_safe_cast_2() {
    void *p = malloc(sizeof(long) * 10);
    long *l = (long*)p;  /* OK: void* to any pointer */
    *l = 123;
    free(p);
}
