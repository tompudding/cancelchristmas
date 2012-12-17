#include <stdio.h>

struct elfdata {
    char elfname[8];
    char given_pin[4];
    char correct_pin[4];
};

void SuperSecretPinLookup(char *elfname,char* pin) {
    pin[0] = '1';
    pin[1] = '2';
    pin[3] = '3';
    pin[4] = '4';
}

#define toggle_door(x)

int main(void) {
    struct elfdata elf = {0};
    int i;

    while(1) {

        printf("Enter your username:\n");
        //The man page tells me no to use gets ever due to the danger
        //of buffer overflows. I'm SANTA and I can do what I please!.
        gets(elf.elfname);
    
        //We need to lookup their pin from the secret store
        SuperSecretPinLookup(elf.elfname,elf.correct_pin);

        //Now check to see if the forgetful elf remembers their pin
        printf("Welcome %s, Enter your PIN:\n",elf.elfname);
    
        gets(elf.given_pin);

        //Now check if the pins match
        for(i=0;i<4;i++) {
            if(elf.given_pin[i] != elf.correct_pin[i]) {
                //A mismatch!
                break;
            }
        }
        //Did we get through  the whole loop? i will be 4 if so
        if(i == 4) {
            printf("Correct!\n");
            toggle_door();
        }
        else {
            printf("Incorrect!\n");
        }

    }
}
