import time
import sqlite3
from datetime import datetime
from pytz import timezone
import oauth2 as oauth
import urllib
import json

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

sql = './TW_crowd_control.sqlite'
consumer_key = ''
consumer_secret = ''
token_key = ''
token_secret = ''
my_id = ''


def oauth_request(argv, cons_k=consumer_key,
                  cons_s=consumer_secret,
                  tok_k=token_key,
                  tok_s=token_secret,
                  http_method='POST', post_body = None, http_headers = None, category = 1):

    consumer = oauth.Consumer(key = consumer_key, secret = consumer_secret)
    access_token = oauth.Token(key = token_key, secret = token_secret)
    client = oauth.Client(consumer, access_token)

    '''
    category 1 - friend request
    category 0 - unfriend request
    '''

    if category == 1:
        api_url = 'https://api.twitter.com/1.1/friendships/create.json?user_id=' + str(argv)
    else:
        api_url = 'https://api.twitter.com/1.1/friendships/destroy.json?user_id=' + str(argv)

    results = client.request(
    friend_request_api,
    method = http_method,
    body = urllib.parse.urlencode({'status' : post_body}),
    headers = http_headers,)

    return results

def condition():
    start_time = 9
    end_time = 21

    est_timezone = timezone('EST')
    now = datetime.now(est_timezone)

    return start_time < now.hour < end_time



'''
From when till when do you want to copy followers?
Rest of the time, this script will unfollow your non-mutual followings.
'''

#api endpoints
friends_api = 'https://api.twitter.com/1.1/friends/ids.json?'
followers_api = 'https://api.twitter.com/1.1/followers/ids.json?screen_name='

while True:
    print('Starting the script...')

    conn = sqlite3.connect(sql)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS twitter (user_id INTEGER PRIMARY KEY NOT NULL UNIQUE, \
                request_time INTEGER NOT NULL, is_friend INTEGER NOT NULL)')
    #I was going to do something with this list below, but forgot. What was it, seriously??
    #cur.execute('SELECT user_id FROM twitter where is_friend = 0')
    #previous_nonfriends = cur.fetchall()
    #if not previous_nonfriends: previous_nonfriends = [x[0] for x in previous_nonfriends]
    cur.execute('SELECT user_id FROM twitter')
    previous_allfriends = cur.fetchall()
    if not previous_allfriends: previous_allfriends = [x[0] for x in previous_allfriends]
    cur.close()
    conn.close()

    consumer = oauth.Consumer(key = consumer_key, secret = consumer_secret)
    access_token = oauth.Token(key = token_key, secret = token_secret)
    client = oauth.Client(consumer, access_token)

    print('Sorting out my followers...')

    my_friends_list = list()
    api_now = followers_api + my_id

    while True:
        friend_headers, friend_data = client.request(api_now)
        friend_data = json.loads(friend_data.decode())
        next_cursor = friend_data['next_cursor']

        my_friends_list += friend_data['ids']

        if not next_cursor:
            break

        api_now = friends_api + '&cursor=' + str(next_cursor)

    print('Checking if there have been some friend requests...')
    for my_friend in my_friends_list:
        if my_friend not in previous_allfriends:
            oauth_request(my_friend)
            print('Mutual Friend request has been sent, cheers! {}!'.format(my_friend))
            time.sleep(240)

    conn = sqlite3.connect(sql)
    cur = conn.cursor()
    for user in my_friends_list:
        cur.execute('INSERT OR IGNORE INTO twitter (user_id, request_time, is_friend) VALUES({}, 0, 1)'.format(user))
        cur.execute('UPDATE twitter SET is_friend = 1 WHERE user_id = {}'.format(user))
    conn.commit()
    cur.close()
    conn.close()
    print('Saving my followers data...')

    if condition():
        #EST 09~21 copy followers
        print('Starting copying followers...')
        conn = sqlite3.connect(sql)
        cur = conn.cursor()

        cur.execute('CREATE TABLE IF NOT EXISTS copy_follow (username TEXT[50] PRIMARY KEY NOT NULL UNIQUE)')
        cur.execute('SELECT username FROM copy_follow')
        target_inputs = [copy[0] for copy in cur.fetchall()]
        cur.close()
        conn.close()

        print('Target found, target ID {}'.format(target_input))

        if not target_inputs:
            target_inputs.append('unboxtherapy')

        print('Examining the target...')


        for target_input in target_inputs:
            url = followers_api + target_input
            copy_list = list()
            while True:
                if not condition: break
                copy_headers, copy_body = client.request(url)
                copy_body_json = json.loads(copy_body.decode())
                print('Extracting followers...')

                for copy_target in copy_body_json['ids']:
                    if not condition: break
                    oauth_request(copy_target, category = 1)
                    print('Friend request has been sent to {}...'.format(copy_target))
                    conn = sqlite3.connect(sql)
                    cur = conn.cursor()
                    cur.execute('INSERT OR IGNORE INTO twitter(user_id, request_time, is_friend) VALUES({}, {}, 0)'.format(copy_target, int(time.time)))
                    conn.commit()
                    cur.close()
                    conn.close()
                    time.sleep(240)

                copy_next_cursor = copy_body_json['next_cursor']
                if not copy_next_cursor:
                    conn = sqlite3.connect(sql)
                    cur = conn.cursor()
                    cur.execute('DELETE FROM copy_follow WHERE username = \'{}\''.format(target_input))
                    conn.commit()
                    cur.close()
                    conn.close()
                    break
                url = followers_api + target_input + '&cursor=' + str(copy_next_cursor)

    else:
        #EST 21~09 unfollow the unfriendly
        print('Start unfollowing...')
        print('Loading my following list...')
        conn = sqlite3.connect(sql)
        cur = conn.cursor()
        cur.execute('SELECT user_id FROM twitter WHERE is_friend = 0 AND request_time < {}'.format(int(time.time())-1209600))
        non_mutual = [x[0] for x in cur.fetchall()]
        cur.close()
        conn.close()

        for unfriend_target in non_mutual:
            if condition(): break
            oauth_request(unfriend_target, category=0)
            print('Friendship destroyed with {}...'.format(unfriend_target))
            conn = sqlite3.connect(sql)
            cur = conn.cursor()
            cur.execute('DELETE FROM twitter WHERE user_id = {}'.format(unfriend_target))
            conn.commit()
            cur.close()
            conn.close()
            time.sleep(240)
