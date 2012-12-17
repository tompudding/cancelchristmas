#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <limits.h>

#define ACCESS_GRANTED 1
#define ACCESS_DENIED  0
#define NUM_ELVES 200

/* There are 200 elves working at the grotto,
 * with UIDs ranging from 1 - 200
 * Santa has UID the special UID 0
 * Store a table with their permissions for this door. */

#define toggle_door(x)

uint32_t permissions[200 + 1] = {0}; //Extra is for Santa

int main(void) {

    char buffer[16] = {0};
    uint32_t uid;

    //Set all the people have permission. 
    //Oh look, only Santa has permission
    permissions[0] = ACCESS_GRANTED;

    while(1) {

        printf("Greetings elf, enter your user id:\n");
        
        fgets(buffer,sizeof(buffer),stdin);
        //Make sure it's NULL terminated
        buffer[sizeof(buffer)-1] = '\0';

        //Convert that number to an int
        uid = strtoul(buffer,NULL,10);
        if(ULONG_MAX == uid) {
            printf("Invalid UID\n");
            continue;
        }

        if(0 == uid) {
            //This elf is impersonating Santa!
            printf("Nice try elf, Santa does not use computers!\n");
            continue;
        }

        //Check if they have permission
        
        if(ACCESS_GRANTED == permissions[uid]) {
            printf("Access Granted\n");
            toggle_door();
        }
        else {
            printf("Access denied\n");
        }
    }
}

