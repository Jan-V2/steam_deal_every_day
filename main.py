from utils import log, log_return, ROOTDIR, get_timestamp
import api_key

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

api = api_key.get_api()
max_chars = 280

def chars_in_str_array(str_array):
    total_chars = 0
    for line in str_array:
        total_chars += len(line)

def get_tweet_start():
    return "This tweet was created at " + get_timestamp()


def get_tweetable_result(index):
    # returns a 1 line string that can be added to the tweet.
    pass


tweet_lines = []
tweet_lines.append(get_tweet_start())


tweet = ''
for line in tweet_lines:
    tweet += line
    tweet += '\n'

print(tweet)
api.update_status(tweet)
