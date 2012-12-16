from OpenGL.GL import *
import random,numpy,cmath,math,pygame
import hashlib
import string
import sqlite3

import ui,globals,drawing,os,copy
from globals.types import Point

class Modes:
    ENTRY = 1
    VIEW  = 2

globals.final_password = ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in xrange(5))
globals.password_positions = range(5)
random.shuffle(globals.password_positions)

class Emulator(ui.UIElement):
    cursor_char     = chr(0x9f)
    cursor_interval = 500
    def __init__(self,parent,gameview,computer,background,foreground):
        bl = Point(50,50).to_float()/parent.absolute.size
        tr = (Point(1,1) - bl)
        super(Emulator,self).__init__(parent,bl,tr)
        self.background_colour = background
        self.foreground_colour = foreground
        self.scale = 2
        self.gameview = gameview
        self.computer = computer
        self.shift = None
        # find my door
        doors = [door for door in self.gameview.map.doors]
        doors.sort(lambda x,y:cmp((x.pos - self.computer.pos).SquareLength(),(y.pos - self.computer.pos).SquareLength()))
        self.door = doors[0]
        
        self.size = (self.absolute.size/(globals.text_manager.GetSize(' ',self.scale).to_float())).to_int()
        self.quads = []
        self.mode  = Modes.ENTRY
        for x in xrange(self.size.x):
            col = []
            for y in xrange(self.size.y):
                q = globals.text_manager.Letter(' ',drawing.texture.TextTypes.SCREEN_RELATIVE,self.foreground_colour)
                bl = (Point(x,self.size.y - 1 - y).to_float())/self.size
                tr = (Point(x+1,self.size.y - y).to_float())/self.size
                q.SetVertices(self.GetAbsolute(bl),self.GetAbsolute(tr),drawing.constants.DrawLevels.ui + self.level + 1)
                col.append(q)
            self.quads.append(col)
        self.cursor_flash = None
        self.cursor_flash_state = False
        self.current_buffer = []
        self.viewlines = self.GetCode().splitlines()
        self.viewpos = 0
            
        self.cursor_entry = Point(0,0)
        self.cursor_view  = Point(0,0)
        self.cursor = self.cursor_entry
        self.saved_buffer = []
        self.shift_transforms = dict(((a,a.upper()) for a in 'abcdefghijklmnopqrstuvwxyz'))
        self.shift_transforms.update( {'1' : '!',
                                       '2' : '"',
                                       '3' : '#',
                                       '4' : '$',
                                       '5' : '%',
                                       '6' : '^',
                                       '7' : '&',
                                       '8' : '*',
                                       '9' : '(',
                                       '0' : ')'} )

        self.text = ui.TextBox(self,
                               bl = Point(0.15,-0.14),
                               tr = None,
                               text = 'Press TAB to switch to code view, ESC to close',
                               scale = 2,
                               colour = drawing.constants.colours.green)
        #self.text_box = ui.Box(parent = self,
        #                       pos    = Point(0.2,0.9),
        #                       tr     = Point(1.1,1.2),
        #                       colour = (0,0,0,0.3))
        
        self.AddMessage(self.GetBanner())

    def GetBanner(self):
        return self.Banner

    def GameOver(self):
        return False

    def ShiftDown(self):
        self.shift = True

    def ShiftUp(self):
        self.shift = False

    def Update(self,t):
        self.t = t
        if self.cursor_flash == None:
            self.cursor_flash = t
            return
        if t - self.cursor_flash > self.cursor_interval:
            self.cursor_flash = t
            if not self.cursor_flash_state:
                #Turn the cursor on
                self.FlashOn()
            else:
                self.FlashOff()

    def FlashOn(self):
        old_letter = self.quads[self.cursor.x][self.cursor.y].letter
        globals.text_manager.SetLetterCoords(self.quads[self.cursor.x][self.cursor.y],self.cursor_char)
        self.quads[self.cursor.x][self.cursor.y].letter = old_letter
        self.cursor_flash_state = True

    def FlashOff(self):
        l = self.quads[self.cursor.x][self.cursor.y]
        globals.text_manager.SetLetterCoords(l,l.letter)
        self.cursor_flash_state = False

    def Disable(self):
        super(Emulator,self).Disable()
        self.text.Disable()
        for x in xrange(self.size.x):
            for y in xrange(self.size.y):
                self.quads[x][y].Disable()

    def Enable(self):
        super(Emulator,self).Enable()
        self.text.Enable()
        for x in xrange(self.size.x):
            for y in xrange(self.size.y):
                self.quads[x][y].Enable()

    def Dispatch(self,command):
        #print 'Got command : ',command
        pass

    def AddMessage(self,message,fail = None):
        if fail == True:
            globals.sounds.access_denied.play()
        elif fail == False:
            globals.sounds.access_granted.play()
        for char in '\n' + message + '\n':
            if char == '\n':
                key = pygame.K_RETURN
            else:
                key = ord(char)
            self.AddKey(key,False)

    def ToggleMode(self):
        if self.mode == Modes.ENTRY:
            self.text.SetText('Press TAB to switch to console mode,ESC to close',colour = drawing.constants.colours.green)
            self.mode = Modes.VIEW
            #Save off the current entry buffer for restoring
            self.SaveEntryBuffer()
            self.cursor = self.cursor_view
            self.SetViewBuffer()
        else:
            self.text.SetText('Press TAB to switch to code mode, ESC to close',colour = drawing.constants.colours.green)
            self.mode = Modes.ENTRY
            self.cursor = self.cursor_entry
            self.RestoreEntryBuffer()

    def SaveEntryBuffer(self):
        self.saved_buffer = []
        for x in xrange(self.size.x):
            for y in xrange(self.size.y):
                self.saved_buffer.append(self.quads[x][y].letter)
        
    def RestoreEntryBuffer(self):
        pos = 0
        for x in xrange(self.size.x):
            for y in xrange(self.size.y):
                globals.text_manager.SetLetterCoords(self.quads[x][y],self.saved_buffer[pos])
                pos += 1

    def SetViewBuffer(self):
        #Just set the text from the view buffer
        numlines = 0
        for y,line in enumerate(self.viewlines[self.viewpos:self.viewpos + self.size.y]):
            numchars = 0
            for x,char in enumerate(line[:self.size.x]):
                globals.text_manager.SetLetterCoords(self.quads[x][y],char)
                numchars += 1
            for x in xrange(numchars,self.size.x):
                globals.text_manager.SetLetterCoords(self.quads[x][y],' ')
            numlines += 1
        for y in xrange(numlines,self.size.y):
            for x in xrange(self.size.x):
                globals.text_manager.SetLetterCoords(self.quads[x][y],' ')
                

    def ViewAddKey(self,key):
        self.FlashOff()
        if key == pygame.K_LEFT:
            if self.cursor.x > 0:
                self.cursor.x -= 1
        if key == pygame.K_RIGHT:
            if self.cursor.x < self.size.x - 1:
                self.cursor.x += 1
        if key == pygame.K_DOWN:
            if self.cursor.y < self.size.y - 1:
                self.cursor.y += 1
            else:
                #ooh, need to move the screen up...
                self.viewpos += 1
                self.SetViewBuffer()
        if key == pygame.K_UP:
            if self.cursor.y > 0:
                self.cursor.y -= 1
            else:
                if self.viewpos > 1:
                    self.viewpos -= 1
                    self.SetViewBuffer()
        self.cursor_flash = self.t
        self.FlashOn()

    def AddKey(self,key,userInput = True,repeat = False):
        if userInput and not repeat:
            #for sound in globals.sounds.typing_sounds:
            #    sound.stop()
            #print dir(globals.sounds.typing_sounds[0])
            random.choice(globals.sounds.typing_sounds).play()
        if self.mode == Modes.VIEW:
            self.ViewAddKey(key)
            return
        #Handle special keys
        self.FlashOff()
        if key == pygame.K_RETURN:
            command = ''.join(self.current_buffer)
            if userInput:
                self.Dispatch(command)
            #Move to the start of the next line
            for i in xrange(self.size.x - self.cursor.x):
                self.AddKey(ord(' '),userInput)
            self.current_buffer = []
        elif key == pygame.K_BACKSPACE:
            if len(self.current_buffer) == 0:
                #ignore the backspace
                return
            if userInput:
                self.current_buffer.pop()
            if self.cursor.x == 0:
                if self.cursor.y == 0:
                    return
                self.cursor.x = self.size.x - 1
                self.cursor.y -= 1
            else:
                self.cursor.x -= 1
            c = Point(self.cursor.x,self.cursor.y)
            self.AddKey(ord(' '),userInput)
            self.current_buffer.pop() #remove the space we just added
            self.cursor = c
            return
        try:
            key = chr(key)
        except ValueError:
            return

        if self.shift:
            if key in self.shift_transforms:
                key = self.shift_transforms[key]

        if not globals.text_manager.HasKey(key):
            return
        globals.text_manager.SetLetterCoords(self.quads[self.cursor.x][self.cursor.y],key)

        self.cursor.x += 1
        if self.cursor.x >= self.size.x:
            self.cursor.x = 0
            self.cursor.y += 1
        if self.cursor.y >= self.size.y:
            #Move everything up
            for x in xrange(self.size.x):
                for y in xrange(self.size.y):
                    globals.text_manager.SetLetterCoords(self.quads[x][y],self.quads[x][y+1].letter if y+1 < self.size.y else ' ')
            self.cursor.y = self.size.y - 1
        if userInput:
            self.current_buffer.append(key)

class GrotoEntryTerminal(Emulator):
    Banner = 'Welcome to Santa\'s Grotto! Enter the PIN to continue:'
    success_message = 'Correct, ACCESS GRANTED!'
    fail_message = 'That is not correct. Humbug!'
    code = """print("{banner}")
while True:
    pin = raw_input()
    if pin == '{pin}':
        print("{success}")
        door.open()
    else:
        print("{fail}")
""".format(banner  = Banner,
           success = success_message,
           fail    = fail_message,
           pin     = '{pin}')

    def __init__(self,*args,**kwargs):
        self.pin = ''.join(random.choice(string.digits) for i in xrange(4))
        super(GrotoEntryTerminal,self).__init__(*args,**kwargs)

    def Dispatch(self,command):
        if command == self.pin:
            self.AddMessage(self.success_message,fail = False)
            #open the door
            self.door.Toggle()
        else:
            self.AddMessage(self.fail_message,fail = True)

    def GetCode(self):
        return self.code.format(pin = self.pin)
            
class DisguisedPinTerminal(GrotoEntryTerminal):
    code = """print("{banner})"
while True:
    pin = raw_input()
    if ((pin*77)+1435)%385680 == '{pin}':
        print("{success}")
        door.open()
    else:
        print("{fail}")
""".format(banner  = GrotoEntryTerminal.Banner,
           success = GrotoEntryTerminal.success_message,
           fail    = GrotoEntryTerminal.fail_message,
           pin     = '{pin}')

    def GetCode(self):
        return self.code.format(pin = ('%d' % (((int(self.pin)*77)+1435)%385680)))

positionals = ['st','nd','rd','th','th']

class KeywordTerminal(Emulator):
    Banner_format = 'The {position} letter of the final password is {letter}'
    code = ''
    def __init__(self,*args,**kwargs):
        self.position = globals.password_positions.pop()
        self.letter = globals.final_password[self.position]
        self.Banner = self.Banner_format.format(position = '%d%s' % (self.position+1,positionals[self.position]),
                                                letter   = self.letter)
        super(KeywordTerminal,self).__init__(*args,**kwargs)

    def GetCode(self):
        return 'print("%s")' % self.Banner

class OverflowPinTerminal(Emulator):
    class States:
        ENTER_NAME = 0
        ENTER_PIN  = 1
        
    Banner = 'Welcome to Present Preparation. Please enter your username'
    code = """#include <stdio.h>

struct elfdata {
    char elfname[8];
    char given_pin[5];   //4 characters and room for the null
    char correct_pin[5]; //4 characters and room for the null
};

void SuperSecretPinLookup(char *elfname,char* pin) {
    [REDACTED]
}

int main(void) {
    struct elfdata elf = {0};
    int i;

    while(1) {

        printf("Welcome to Present Preparation. Please enter your \
username:\\n");
        //The man page tells me not to use gets ever due to a danger
        //of buffer overflows. I'm SANTA and I can do what I please!.
        gets(elf.elfname);
    
        //We need to lookup their pin from the secret store
        SuperSecretPinLookup(elf.elfname,elf.correct_pin);

        //Now check to see if the forgetful elf remembers their pin
        printf("Welcome %s, Enter your PIN:\\n",elf.elfname);
    
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
            printf("Correct!\\n");
            toggle_door();
        }
        else {
            printf("Incorrect!\\n");
        }
    }
}
"""
    def __init__(self,*args,**kwargs):
        self.state = self.States.ENTER_NAME
        self.rand = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in xrange(32))
        super(OverflowPinTerminal,self).__init__(*args,**kwargs)

    def Dispatch(self,command):
        if self.state == self.States.ENTER_NAME:
            self.name = command
            #simulate an overflow here, it's subtle, but if the user overflows into given_pin,
            #and then when later asked for their pin their write 4 or fewer characters (with the null)
            #then the pin checked will have some characters set from this initial overflow.
            #Actually ignore this because I can't be bothered!
            
            self.AddMessage('Welcome %s, Enter your PIN:' % self.name)
            self.state = self.States.ENTER_PIN
        elif self.state == self.States.ENTER_PIN:
            command += '\x00'
            pin = command[:4]
            for i in xrange(len(pin),4):
                try:
                    pin += self.name[i+8]
                except IndexError:
                    pin += '\x00'
            h = hashlib.sha1(self.rand + self.name).digest()
            correct_pin = []
            for b in h[4:8]:
                correct_pin.append('%d' % (ord(b)%10)) #Fun fact, this isn't flat random, 0-5 are more likely! Do you know why?

            #Simulate the overflow into the computed pin
            for i,c in enumerate(command[5:9]):
                correct_pin[i] = c
            correct_pin = ''.join(correct_pin)
            print pin,correct_pin
            if pin == correct_pin:
                self.AddMessage('Access granted',fail = False)
                self.door.Toggle()
            else:
                self.AddMessage('Access denied',fail = True)
            self.AddMessage(self.Banner)
            self.state = self.States.ENTER_NAME                

    def GetCode(self):
        return self.code

class IntegerOverflowTerminal(Emulator):
    Banner = 'Welcome to Santa\'s Suites. Please enter your UID'
    code = """#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <limits.h>

#define ACCESS_GRANTED 0x584d4153
#define ACCESS_DENIED  0
#define NUM_ELVES 8

// There are 200 elves working at the grotto,
// with UIDs ranging from 1 - 8
// Santa has UID the special UID 0
// Store a table with their permissions for this door. 

// For reference sizeof(*void) == sizeof(uint32_t) == 4

int main(void) {

    uint32_t permissions[8 + 1] = {0}; //Extra is for Santa
    char buffer[16] = {0};
    uint32_t uid;

    //Set all the people who have permission. 
    //Oh look, it's only Santa
    permissions[0] = ACCESS_GRANTED;

    while(1) {

        printf("Greetings elf, enter your user id:\\n");
        
        fgets(buffer,sizeof(buffer),stdin);
        //Make sure it's NULL terminated
        buffer[sizeof(buffer)-1] = '\\0';

        //Convert that number to an int
        uid = strtoul(buffer,NULL,10);
        if(ULONG_MAX == uid) {
            printf("Invalid UID\\n");
            continue;
        }

        if(0 == uid) {
            //This elf is impersonating Santa!
            printf("Nice try elf, Santa does not use computers!\\n");
            continue;
        }

        //Check if they have permission
        
        if(ACCESS_GRANTED == permissions[uid]) {
            printf("Access Granted\\n");
            toggle_door();
        }
        else {
            printf("Access denied\\n");
        }
    }
}
"""

    def Dispatch(self,command):
        try:
            try:
                uid = int(command)
            except ValueError:
                self.AddMessage('Invalid UID')
                return

            #mimic the behaviour of strtoul
            uid = uid&0xffffffff
            if uid == 0:
                self.AddMessage('Nice try elf, Santa does not use computers!')
                return
            index = (uid*4)&0xffffffff
            if index > (8*4):
                self.AddMessage('Segfault detected, restarted')
                return

            if index == 0:
                self.AddMessage('Access Granted',fail = False)
                self.door.Toggle()
            else:
                self.AddMessage('Access denied',fail = True)

        finally:
            self.AddMessage(self.Banner)
                
    def GetCode(self):
        return self.code

def RandomPassword():
    return ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in xrange(5))

class SqlInjectionTerminal(Emulator):
    """ Think something like [' and '0'='1'; SELECT Password,Name from Passwords Where Uid='0] for UID"""
    Banner = 'Welcome to Market Research. Please enter your UID'
    code = """while True:
  print 'Welcome to Market Research. Enter your UID:'
  uid = raw_input()
  with con:
    cur = con.cursor()
    try:
      #Mrs Claus keeps insisting that this is vulnerable to an 
      #SQL injection attack. Nag Nag Nag.
      command = "SELECT Name,Password from Passwords WHERE UID = '%s'" % uid
      results = database.execute(command)
    except error as e:
      print 'Error with UID',str(e)
    if results == None:
      print 'No such UID'

    name,password = results[0]
    print 'Greetings %s, what is your password?' % (name)
    given_password = raw_input()
    if given_password == password:
      print 'Access granted'
      door.toggle()
    else:
      print 'Access denied'
"""
    class States:
        ENTER_UID  = 0
        ENTER_PASS = 1
    def __init__(self,*args,**kwargs):
        self.state = self.States.ENTER_UID
        self.con = sqlite3.connect(':memory:')
        data = (
            (0, 'Santa'      , RandomPassword()),
            (1, 'Mrs Claus'  , RandomPassword()),
            (2, 'Gingerbread', RandomPassword()),
            (3, 'Eggnog'     , RandomPassword()),
            (4, 'Sugarplum'  , RandomPassword()),
            (5, 'Dudley'     , RandomPassword()),
            (6, 'Ferrel'     , RandomPassword()),
            (7, 'Jingle'     , RandomPassword()),
            (8, 'Holly'      , RandomPassword())
            )
        with self.con:
            cur = self.con.cursor()
            cur.execute('CREATE TABLE Passwords(Uid INT, Name TEXT, Password TEXT)')
            cur.executemany('INSERT INTO Passwords VALUES(?,?,?)',data)

        super(SqlInjectionTerminal,self).__init__(*args,**kwargs)

    def Dispatch(self,command):
        if self.state == self.States.ENTER_UID:
            results = []
            with self.con:
                #Sqlite quite sensibly limits execute to only one statement, so simulate 
                #a more dodgy database by allowing them. Sqlite would still be vulnerable
                #to a blind injection attack on the passwords, but that would be too hard
                #for this game. Left as an exercise for the reader!
                cur = self.con.cursor()
                self.uid = command
                command = "SELECT Name,Password from Passwords WHERE UID = '%s'" % self.uid
                commands = command.split(';')
                try:
                    for command in commands:
                        cur.execute(command)
                        result = cur.fetchone()
                        if result == None:
                            continue
                        name,password = result
                        results.append((name,password))
                except sqlite3.Error as e:
                    self.AddMessage('Error with UID %s' % str(e),fail = True)
                    self.AddMessage(self.Banner)
                    return
            if results == []:
                self.AddMessage('No such UID')
                return
            self.name,self.password = results[0]
            self.state = self.States.ENTER_PASS
            self.AddMessage('Greetings %s, what is your password?' % self.name)
            return
        elif self.state == self.States.ENTER_PASS:
            password = command
            if password.lower() == self.password.lower():
                self.AddMessage('Access Granted',fail = False)
                self.door.Toggle()
            else:
                self.AddMessage('Access Denied',fail = True)
            self.AddMessage(self.Banner)
            self.state = self.States.ENTER_UID                
                
    def GetCode(self):
        return self.code

class FinalChallengeTerminal(Emulator):
    Banner = 'Access to the naughty list room is restricted. Enter the password'
    code = """[REDACTED]"""

    def Dispatch(self,command):
        try:
            if command.lower() == globals.final_password.lower():
                self.AddMessage('Access Granted',fail = False)
                self.door.Toggle()
            else:
                self.AddMessage('Access denied',fail = True)
        finally:
            self.AddMessage(self.Banner)
                
    def GetCode(self):
        return self.code

class NaughtyListTerminal(Emulator):
    Banner = 'Welcome to the Hallowed Nice-or-Naughty List Computer\nCommands are read, print, delete or help'
    code = """[REDACTED]"""

    def __init__(self,*args,**kwargs):
        super(NaughtyListTerminal,self).__init__(*args,**kwargs)
        self.deleted = False

    def Dispatch(self,command):
        if command == 'read':
            if not self.deleted:
                self.AddMessage('There are 7 billion names on this list. It is too large to read')
            else:
                self.AddMessage('The list contains only one entry : "Mysterious Hacker : Naughty"')
        elif command == 'print':
            self.AddMessage('Now printing in the main office. I hope you have enough paper!')
        elif command == 'delete':
            if not self.deleted:
                self.AddMessage('Happy new year! Naughty list now deleted. Press ESC to close the terminal')
                self.deleted = True
            else:
                self.AddMessage("It's already deleted. Seriously, just press ESC")
            
        else:# command == 'help':
            if command != 'help':
                self.AddMessage('Unknown command %s' % command)
            self.AddMessage(self.Banner)
                
    def GetCode(self):
        return self.code

    def GameOver(self):
        return self.deleted
