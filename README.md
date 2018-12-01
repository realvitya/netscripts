Network script framework
=============
This project is to make common tasks on several devices more easy by eliminating handwork. The project does not want to replace big fancy projects like [Ansible](https://www.ansible.com/community) but to create quick and dirty jobs instead of manual working.

Example tasks where these worked well:
- cleaning up dot1x from switches
- cleaning up management configuration
- setup basic config
- backup switches/firewall configurations

INSTALL
-------
- You will need python 2 and netmiko
- telnet and/or ssh should be installed
- I recommend installing `virtualenv` and install `netscripts` into that virtual environment:
   - `pip install virtualenv`
   - `virtualenv ~/mypython`
   - `source ~/mypython/bin/activate`
   - `pip install netmiko`
   - `git clone https://github.com/realvitya/netscripts`

CONFIGURATION
-------------
copy [scripts.cfg.sample](https://github.com/realvitya/netscripts/blob/master/scripts.cfg.sample) to your $HOME or project folder where you are running the scripts.
Then rename to scripts.cfg and edit, add or remove sections based on builtin docs in example file.
You will use this scripts.cfg and devices.txt in your project folder (creating separate folder is recommended)
The scripts will use devices.txt to read which devices you want to configure. You may organize your devices in sections by access type and device type.

devices.txt
-----------
```
[devicegroup]
device1
device2
...
devicen

[telnet-devicegroup]
tdevice1
tdevice2
...
tdevice3

[asa-devicegroup]
fw1
fw2
...
fwn
```

scripts.cfg
-----------
Please check [scripts.cfg.sample](https://github.com/realvitya/netscripts/blob/master/scripts.cfg.sample) for documentation. Maybe one of the most important variable is `logging` as this must be enabled in order to check what would happen.

playscript.py
-------------
This program is running a script file which contains pure commands but you can use special keywords to tell the interpreter to do something with the input.

ARGUMENTS
---------
- `-s {scriptfile}` : The scriptfile name is `something.script` This contains the intended script for the interpreter.
- `-g {devicegroup}`: The devicegroup name which is a section in `devices.txt`
- `-f`              : By default no changes will be made and only a testrun will happen. If you specify this switch, then the script will go into config mode and do the changes. I recommend testing extensively without this switch and use it when you trust in your scriptfile! 

SCRIPTFILE
----------
Every line is a configuration item which will be executed in config mode 

Lines starting with '#' are comment, script doesn't bother               

Empty lines are count as ENTER! Might be useful when router wants confirmation:
```
#delete admin user:
no username admin

#the above empty line will press ENTER when switch asks for confirmation.
```

Lines starting with '!' are commands for the script.                     

Commands:
```
!clear {something} : script will run config "no {^something.*}"
```
Example:
`!clear ntp server`
The result can be something like:
```
no ntp server 1.1.1.1
no ntp server 2.2.2.2 prefer
```
Please make sure you specify as strict as you can to avoid removing lines which were not intended so!
Other example for ASA:

`!clear ssh [1-9]`

That will remove all ssh access except the one with starting by 0, therefore it's the `any`:
```
no ssh 1.1.1.1 255.255.255.0 management
no ssh 2.2.2.2 255.255.255.0 management
```
That could lock out us so the best to put this before clearing:

`ssh 0.0.0.0 0.0.0.0 management`
```
!getvar {varname} {regex (var value)}:
                     get var value and put into varname
                     This allows for dynamic variable management
```

Example:
`!getvar mgmtiface ssh [0-9].* (.*)`
That will take the first line of the output, match the regex and put the value between parentheses into dynamic variable `mgmtiface`
Why is it good for us? Because then we can use it as template variable:

`ssh 1.2.3.4 255.255.255.255 #mgmtiface#`
```
!quit              : quit the script immediately
                     (good for testing/tshooting)
!replace "{search}" "{replace}"      :
                     replace input with defined string
```
Replace is good for manipulating output by previously matched data. You may use one or more matches to subtitue config. The subtituted values are using `$[1-9]` format.
Example:
`!replace "privilege ([a-z]+) level [0-9]+ (.*)" "privilege $1 reset $2"`

Input:
`privilege exec level 7 show`

Output:
`privilege exec reset show`

`#variable#` are variables which will be substitued with something
Variables are read from `scripts.cfg` `[variables-{scriptname}]` section `{scriptname}` is the name of the script without file extension.
Example:
```
[variables-clean-ssh]
admin1 = "10.1.0.0 255.255.255.0"
admin2 = "10.2.0.0 255.255.255.0"
```
Then in the `clean-ssh.script` file:
```
ssh #admin1# management
ssh #admin2# management
```
The above will be derived to:
```
ssh 10.1.0.0 255.255.255.0 management
ssh 10.2.0.0 255.255.255.0 management
```

If you want to run exec mode commands instead of config mode commands, you may use the `do` keyword.
Example:
```
#Save config
do write memory
```
