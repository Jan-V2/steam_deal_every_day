# -*- coding: utf-8 -*-
import collections
import string
from pprint import pprint

import bs4
import urllib3
import re
from my_logging import log_message as log, log_return
from utils import listmerger, list_demerger, get_methods_from_class
from consts import ints_str_list as ints_str
from platform_vars import dir_sep as dirsep, ROOTDIR

steam_special_url_firstpage = "http://store.steampowered.com/search/?specials=1"
and_page = "&page="
http = urllib3.PoolManager()

html_file = "test.html"


def get_number_pages():
    first_page = http.request("GET", steam_special_url_firstpage)
    html_soup = bs4.BeautifulSoup(first_page.data, 'html.parser')

    result = html_soup.find_all("div", {"class": "search_pagination_right"})
    result = str(result)

    searchstring = 'page='
    pagelist = [m.start() for m in re.finditer(searchstring, result)]

    # it assumes that the 2nd to last result is the total number of pages
    index = pagelist[len(pagelist) - 2] + len(searchstring)
    # this code
    i = 0
    page_number = ""
    while result[index + i] != "\"":
        page_number += result[index + i]
        i += 1

    return int(page_number)


def run_scrape(is_test):
    results_as_strs = []
    if is_test:
        num_pages = 3
    else:
        num_pages = get_number_pages()

    data_scraper = Data_Scraper()
    for i in range(1, num_pages+1):
        page_results_as_bs4 = get_results_from_page_n(i)
        log("got page " + str(i) + "/" + str(num_pages))

        apply_data_scraping(page_results_as_bs4, data_scraper)

    merged_results, keys = apply_filters(data_scraper.scraped_dict)

    log('scrape done')
    return merged_results, keys


def apply_data_scraping(page_as_bs4, data_scraper):
    methods = get_methods_from_class(data_scraper)  # returns list of 2 tuoles 0 = name 1 = method
    for method in methods:
        method[1](page_as_bs4)


def apply_filters(scraped_dict):
    keys = collections.defaultdict(int)# a dict contianing the indexes for bits of data
    merged_results = []

    i = 0
    for key in scraped_dict.keys():
        merged_results.append(scraped_dict[key])
        keys.update({key: i})
        i += 1

    merged_results = listmerger(merged_results)
    filter = Filter()
    for method in get_methods_from_class(filter):
        merged_results = method[1](merged_results, keys)

    return merged_results, keys


def get_results_from_page_n(page_n):
    page_results = []
    if page_n == 1:  # page 1 is special because it has no &page=n
        page = bs4.BeautifulSoup(http.request("GET", steam_special_url_firstpage).data, 'html.parser')
    else:
        page = bs4.BeautifulSoup(http.request("GET", steam_special_url_firstpage + and_page + str(page_n)).data, 'html.parser')

    i = page.find_all("a", {"class": "search_result_row"})
    for result in i:
        page_results.append(result)
    return page_results


def get_result_list(pages):
    results = []
    for page in pages:
        i = page.find_all("a", {"class": "search_result_row"})
        for result in i:
            results.append(result)
        i.clear()
    return results

class Data_Scraper:
    # every methode in this class will be applied to the the results
    # they all must take the list of results as an argument and add a list to the dict in this object and have no return
    # a list in which each result lines up with a result from the argument
    # like this ["review_scores": [list of review scores]]
    scraped_dict = collections.defaultdict(list)

    def get_user_reviews(self, results):
        # returns 2 lists
        # the first list is how many user reviews the result got
        # the second list is what percentage was positive
        n_user_reviews = []
        percent_reviews_positive = []
        found = 0
        log("scraping reviews")
        for result in results:
            var = result.find("span", {"class": "search_review_summary"})
            if not isinstance(var, type(None)):  # if true it contains a review
                var = str(var)
                of_the_str = "% of the "
                of_the_start = var.find(of_the_str)
                of_the_end = of_the_start + len(of_the_str)
                # this part checks how many of the reviews where positive
                percent_positive_as_str = ""
                for char in var[of_the_start - 3:of_the_start]:  # 3 is because a max of 3 digets
                    if char in ints_str:
                        percent_positive_as_str += char

                percent_reviews_positive.append(int(percent_positive_as_str))

                # this part get how many reviews it got
                temp_n_reviews = ""
                for char in var[of_the_end:]:
                    if char == " ":
                        break
                    else:
                        if not char == "," and not char == ".":
                            temp_n_reviews += char
                # print("reviews " + temp_n_reviews)
                n_user_reviews.append(int(temp_n_reviews))

                found += 1
            else:
                n_user_reviews.append(0)
                percent_reviews_positive.append(0)
        for i in range(len(n_user_reviews)):
            self.scraped_dict['n_user_reviews'].append(n_user_reviews[i])
            self.scraped_dict['percent_reviews_positive'].append(percent_reviews_positive[i])

    def get_discount_percents(self, results_list):
        log('scraping discount percents')
        discount_percents = []
        for r in results_list:
            string = str(r.find("div", {"class": "col search_discount responsive_secondrow"}))
            span = "<span>"
            # for some fucking reason not all results have a discount number
            if string.find(span) != -1:
                # the +1 and -1 are to cut off the - and the %
                start = string.find(span) + len(span) + 1
                end = string.find("</span>") - 1
                discount_percents.append(int(string[start:end]))
            else:
                discount_percents.append(0)
        for item in discount_percents:
            self.scraped_dict["discount_percents"].append(item)

    def get_titles_list(self, results_list):
        log("scraping title")
        for result in results_list:
            self.scraped_dict["titles"].append(
                str(result.find("span", {"class": "title"}).string)
                                               )

    def get_old_and_new_price(self, results_list):
        log('scraping the old+new price')
        for result in results_list:
            if result.find('div', {'class': 'col search_price discounted responsive_secondrow'}) is not None:
                price_str = str(result.find('div', {'class': 'col search_price discounted responsive_secondrow'}).text)
                price_str = price_str[:price_str.rfind('€')] # cuts of € and the spaces that come after it at the end of the string so you can split it cleanly
                price_str = price_str.replace('\n', '')# there is apperently a return at the start of the string
                price_str = price_str.replace(',', '.')
                price_str = price_str.replace('--', '0')# if a price has no decimal places it apperently adds --
                old_new_str = price_str.split('€')

                self.scraped_dict["old_price"].append(float(old_new_str[0]))
                self.scraped_dict["new_price"].append(float(old_new_str[1]))
            else:
                self.scraped_dict["old_price"].append(float(0))
                self.scraped_dict["new_price"].append(float(0))

    def get_app_id(self, results_list):
        # THE APP ID(S) ARE STRORED AS STRINGS FOR NOW since i don't need them as ints right now.
        # nor can i think of a reason why i should want that.
        log("scraping appids")
        for result in results_list:
            try:
                if(',' in result['data-ds-appid']):# if it has multible appids which is when it's an old style bundle
                    self.scraped_dict["appids"].append(
                        result['data-ds-packageid'])
                    self.scraped_dict["is_bundle"].append(True)
                    self.scraped_dict["is_old_bundle"].append(True)
                else:
                    self.scraped_dict["appids"].append(
                        result['data-ds-appid'])
                    self.scraped_dict["is_bundle"].append(False)
                    self.scraped_dict["is_old_bundle"].append(False)
            except KeyError:
                self.scraped_dict["appids"].append(
                    result['data-ds-bundleid'])
                self.scraped_dict["is_bundle"].append(True)
                self.scraped_dict["is_old_bundle"].append(False)


class Filter:
    # every methode in this class will be applied to the the results
    # they all must take the list of results as an argument and returns the filtered list

    minimum_discount = 40

    def get_highly_discounted(self, merged_results, keys):
        percents_index = keys["discount_percents"]
        # parameters for get_good_games
        # todo make configureable
        merged_results.sort(key=lambda p: p[percents_index], reverse=True)
        before = len(merged_results)
        for i in range(0, len(merged_results)):
            if merged_results[i][percents_index] < self.minimum_discount:
                break
        merged_results = merged_results[:i]
        log(str(len(merged_results)) + " out of " + str(before) + " had deep enough discount")
        return merged_results

    # parameters for get_good_games
    # todo make configureable
    min_reviews = 100
    min_positive = 75

    def get_good_games(self, merged_results, keys):
        n_rev_idx = keys['n_user_reviews']
        min_positive_idx = keys['percent_reviews_positive']
        ret = []
        before = len(merged_results)
        for result in merged_results:
            if result[n_rev_idx] >= self.min_reviews and result[min_positive_idx] >= self.min_positive:
                ret.append(result)
        log(str(len(ret)) + " out of " + str(before) + " had good enough reviews")
        return ret

    def delete_duplicates(self, merged_results, keys):
        doubles_found = 0
        ret = []
        appid_key = keys['appids']
        is_bundle_key = keys['is_bundle']
        for line in merged_results:
            if len(ret) > 0:
                double = False
                for i in ret:
                    if i[appid_key] == line[appid_key] and i[is_bundle_key] == line[is_bundle_key]:
                        double = True
                        doubles_found += 1
                        break
                if not double:
                    ret.append(line)
            else:
                ret.append(line)
        log('removed ' + str(doubles_found) + ' doubles')
        return ret




# todo count duplicates to see if there's somthing i can do about it
# todo i could make this more effecient by doing basic data scrape -> filter -> rest of datascraping
if __name__ == '__main__':
    # ui = Gui()
    # ui.open()
    run_scrape(True)
