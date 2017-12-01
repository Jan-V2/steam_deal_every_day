# -*- coding: utf-8 -*-

from utils import timestamp_to_datatime, get_timestamp
from my_logging import log_message as log, log_return, get_timestamp
from platform_vars import ROOTDIR, dir_sep
import api_key
from scraper import run_scrape
import datetime

# todo bedenk een format voor de tweet
# it needs the following pieces of data.
# the title
# the url
# the price
# the discount percentage
#
# the url looks like this.
# http://store.steampowered.com/app/364640/FreeCell_Quest/
# it also works like this
# store.steampowered.com/app/364640/
# this way the link is always 35 chars
# exept when it's a bundle
#
# i did some testing and the average length of a title is ~28 chars
# i also found that only about 1/12th of all titles is longer than 45 chars
# what i should do is that is a title is longer than 45 chars, is should add a elipsis.
# aka cut down the string to 42 chars and paste ... on at the end.
#
# i could format the tweet like this
# "title" was "origianal price" is now "reduced price"
# link "link"
# maybe i could add in the discount percentage in somewhere
#
# what i should do is, i should get a result.
# then i should check if the result makes the tweet longer than the max chars.
# if not then it should get the next result and check again


# todo add a bit of code that checks if this deal hasn't already been tweeted in the last n days
# could to this by having a file where it saves a date stamp and the app id /url

def chars_in_str_array(str_array):
    # adds newline char for each str in str_array
    total_chars = 0
    for line in str_array:
        total_chars += len(line)
    total_chars += len(str_array)
    return total_chars

def get_tweet_start():
    return "This tweet was created at " + get_timestamp()

def write_to_tweeted_games(url):
    global tweeted_games_log_path
    with open(tweeted_games_log_path, mode='a') as logfile:
        logfile.write(get_timestamp() + ',' + url + '\n')


def get_tweeted_games_log():
    global tweeted_games_log_path
    try:
        tmp = open(tweeted_games_log_path, 'r')
    except IOError:
        tmp = open(tweeted_games_log_path, 'w')
    tmp.close()
    with open(tweeted_games_log_path, mode='r+') as logfile:
        lines = logfile.read()
        lines = lines.split('\n')
        if len(lines) > 1500:
            logfile.seek(0)
            logfile.truncate()
            for i in range(1000):
                logfile.write(lines[i] + '\n')

        ret = []
        for line in lines:
            if line != '':
                line = line.split(',')
                line[0] = timestamp_to_datatime(line[0])
                ret.append(line)
    return ret


def get_tweetable_result(results, i):
    global keys
    # returns a 1 line string that can be added to the tweet.
    log = get_tweeted_games_log()
    url = get_url(results[i])

    looping = True
    while looping:
        is_in_log = False
        for line in log:
            if line[1] == url:
                if line[0] > datetime.datetime.now() - datetime.timedelta(days=30):
                    is_in_log = True
                    break
        if is_in_log:
            i += 1
            url = get_url(results[i])
        else:
            looping = False
    write_to_tweeted_games(url)
    result = results[i]

    ret = []
    title_maxlength = 45
    title = result[keys['titles']]
    if len(title) > title_maxlength:
        title = title[:title_maxlength-4]
        title += "..."
    line = title + " was €" + str(result[keys['old_price']]) + " is now €" + str(result[keys['new_price']])
    ret.append(line)

    ret.append(str(results[i][keys['discount_percents']]) + '% off!')


    ret.append("Link " + url)
    ret.append('')
    return ret, i

def get_url(result):
    global keys
    new_bundle_url = 'http://store.steampowered.com/bundle/'
    old_bundle_url = 'http://store.steampowered.com/sub/'
    app_url = 'http://store.steampowered.com/app/'
    url = ''
    if result[keys['is_bundle']]:
        if result[keys['is_old_bundle']]:
            url += old_bundle_url
        else:
            url += new_bundle_url
    else:
        url += app_url
    url += result[keys['appids']] + '/'
    return url

def build_tweet(results):
    tweet_lines = []
    tweet_lines.append(get_tweet_start())

    i = 0
    result_lines, i = get_tweetable_result(results, i)
    while chars_in_str_array(tweet_lines) + chars_in_str_array(result_lines) < max_chars:
        for line in result_lines:
            tweet_lines.append(line)
        result_lines, i = get_tweetable_result(results, i)
        i += 1

    tweet = ''
    for line in tweet_lines:
        tweet += line
        tweet += '\n'
    return tweet

def create_test_double_log(results, log_path):
    log('creating test double log')
    for i in range(10):
        write_to_tweeted_games(get_url(results[i]))


api = api_key.get_api()
max_chars = 280
days_before_double_tweet = 45
tweeted_games_log_path = ROOTDIR + dir_sep + 'tweeted_games.log'

results, keys = run_scrape(False)
results.sort(key= lambda p : p[keys['discount_percents']], reverse=True) # should already be sorted but just to be sure

tweet = build_tweet(results)
log(tweet)
api.update_status(tweet)

# for debug
# create_test_double_log(results, keys, tweeted_games_log_path)
# for line in get_tweeted_games_log(tweeted_games_log_path):
#     print(str(line))