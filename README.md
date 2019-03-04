# twitter_crowd_control
twitter_crowd_control
'''
How to use:
1. Insert TW consumer key, consumer secret, token key, token secret into the blanks down below
into the variables.
2. Ctrl+F and find my_id declaration, change the value to your twitter screen id
* screen id is the id that starts with '@' below your account name
3. Set time condition in condition(). Default is whilst condition() returns True, this script will copy
followers, False, unfollow.
4. Insert your desired copy follow targets' screen names into TW_crowd_control.sqlite's copy_follow table
5. Install python3 and run 'pip3 install -r requirements.txt' command in the same directory as this. (You will have to have cloned the git)
6. Tested on
Python3.7
Mac OSX
*In case TW changes their API interface, it won't work, obviously...
'''
