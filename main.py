from my_logging import log, log_return, ROOTDIR, get_timestamp
import api_key
from scraper import run_scrape

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

def chars_in_str_array(str_array):
    # adds newline char for each str in str_array
    total_chars = 0
    for line in str_array:
        total_chars += len(line)
    total_chars += len(str_array)
    return total_chars

def get_tweet_start():
    return "This tweet was created at " + get_timestamp()


def get_tweetable_result(result, keys):
    # returns a 1 line string that can be added to the tweet.
    ret = []

    title_maxlength = 45
    title = result[keys['titles']]
    if len(title) > title_maxlength:
        title = title[:title_maxlength-4]
        title += "..."
    line = title + " was €" + str(result[keys['old_price']]) + " is now €" + str(result[keys['new_price']])
    ret.append(line)

    ret.append(str(result[keys['discount_percents']]) + '% off!')

    bundle_url = 'http://store.steampowered.com/bundle/'
    app_url = 'http://store.steampowered.com/app/'
    url = "Link "
    if result[keys['is_bundle']]:
        url += bundle_url
    else:
        url += app_url
    url += result[keys['appids']] + '/'
    ret.append(url)
    return ret


api = api_key.get_api()
max_chars = 280


results, keys = run_scrape(False)
results.sort(key= lambda p : p[keys['discount_percents']], reverse=True)

tweet_lines = []
tweet_lines.append(get_tweet_start())

i= 0
result_lines = get_tweetable_result(results[i], keys)
while chars_in_str_array(tweet_lines) + chars_in_str_array(result_lines) < max_chars:
    for line in result_lines:
        tweet_lines.append(line)
    i += 1
    result_lines = get_tweetable_result(results[i], keys)


tweet = ''
for line in tweet_lines:
    tweet += line
    tweet += '\n'

print(tweet)
#api.update_status(tweet)
