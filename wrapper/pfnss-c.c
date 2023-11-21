#include <stdio.h>
#include <cstdlib>
#include <cstring>

#define BUFSIZE 128

int main(int argc, char **argv) {
    FILE *f = fopen("pfnss-c.txt", "r");
    char *buf = (char *)calloc(BUFSIZE, sizeof(char));
    fread(buf, sizeof(char), BUFSIZE - 1, f);
    fclose(f);
    char *s = buf;
    while (*s) {
        if (*s == '\n') {
            break;
        }
        ++s;
    }
    *s++ = ' ';
    *s = '\0';
    --argc;
    ++argv;
    while (argc--) {
        strcat(buf, *argv++);
        if (argc) {
            strcat(buf, " ");
        }
    }
    printf("Executing: '%s'\n", buf);
    int retcode = system(buf);
    free(buf);
    return retcode;
}