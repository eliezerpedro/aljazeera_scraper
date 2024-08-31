from RPA.Browser.Selenium import Selenium
from RPA.Robocorp.WorkItems import WorkItems
from robocorp.tasks import task

from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import re
from time import sleep
from robot.api import logger
import locators as lc

browser = Selenium()
workitem = WorkItems()

try:
    workitem.get_input_work_item()
except Exception as e:
    logger.error(f"Failed to get input work item: {e}")
    raise


@task
def main():
    try:
        search_term = workitem.get_work_item_variable("search_term")
        months = int(workitem.get_work_item_variable("months"))

        # search_term = "dollar"
        # months = 0

        browser.open_available_browser("https://www.aljazeera.com/")
        browser.maximize_browser_window()

        perform_search(search_term)
        load_all_news(months)
        df = extract_news_data(search_term, months)
        sleep(1)
        download_images(df)
        save_news_data(df)

    except Exception as e:
        logger.error(f"An error occurred in the main task: {e}")
        raise
    finally:
        browser.close_all_browsers()


def perform_search(search_term):
    try:
        browser.wait_until_element_is_enabled(lc.SEARCH_TRIGGER, 10)
        browser.click_button(lc.SEARCH_TRIGGER)

        browser.wait_until_element_is_enabled(lc.SEARCH_BAR_INPUT, 10)
        browser.input_text(lc.SEARCH_BAR_INPUT, search_term)
        browser.press_keys(lc.SEARCH_BAR_INPUT, "ENTER")

        browser.wait_until_element_is_enabled(lc.SORT_BY_DATE, 10)
        browser.click_element(lc.SORT_BY_DATE)
        browser.wait_until_element_is_visible(lc.NEWS_ARTICLES, 30)

    except Exception as e:
        logger.error(f"Error during search: {e}")
        raise


def load_all_news(months):
    try:
        while True:
            sleep(2)
            last_news_date = datetime.strptime(
                get_last_news_date(), "%d/%m/%Y")
            desired_date = datetime.strptime(
                first_day_of_month(months), "%d/%m/%Y")

            if last_news_date > desired_date:
                load_more_news()
            else:
                break
    except Exception as e:
        logger.error(f"Error while loading news: {e}")
        raise


def load_more_news():
    sleep(1)
    try:
        if browser.is_element_visible(lc.COOKIE_ACCEPT_BUTTON):
            browser.click_button(lc.COOKIE_ACCEPT_BUTTON)

        if browser.is_element_visible(lc.CLOSE_AD_BUTTON):
            browser.click_button(lc.CLOSE_AD_BUTTON)

        browser.scroll_element_into_view(lc.SHOW_MORE_BUTTON)
        browser.wait_until_element_is_visible(lc.SHOW_MORE_BUTTON, 10)

        browser.click_button(lc.SHOW_MORE_BUTTON)
    except Exception as e:
        logger.error(f"Error while loading more news: {e}")
        raise


def get_last_news_date():
    try:
        browser.wait_until_element_is_visible(lc.NEWS_ARTICLES, 30)
        last_news = browser.find_elements(lc.NEWS_ARTICLES)[-1]
        logger.info(f"ultima data {last_news}")
        last_date = last_news.text.split("\n")[-1].replace("Last update ", "")
        last_date_obj = datetime.strptime(last_date, "%d %b %Y")
        return last_date_obj.strftime("%d/%m/%Y")
    except Exception as e:
        logger.error(f"Error getting last news date: {e}")
        raise


def first_day_of_month(months_ago):
    try:
        current_date = datetime.now()
        if months_ago <= 1:
            first_day = current_date.replace(day=1)
        else:
            target_date = current_date - relativedelta(months=months_ago-1)
            first_day = target_date.replace(day=1)
        return first_day.strftime("%d/%m/%Y")
    except Exception as e:
        logger.error(f"Error calculating first day of month: {e}")
        raise


def extract_news_data(search_term, months):
    try:
        news_data = []
        sleep(1)

        for index, news_element in enumerate(browser.find_elements(lc.NEWS_ARTICLES)):
            news_html = news_element.get_attribute("outerHTML")
            data = news_element.text.split(
                "\n")[-1].replace("Last update ", "")
            date_obj = datetime.strptime(data, "%d %b %Y")
            date_formated = date_obj.strftime("%d/%m/%Y")
            desired_date = datetime.strptime(
                first_day_of_month(months), "%d/%m/%Y")
            image_file = f"picture_{index}"

            if desired_date > date_obj:
                break

            title = re.search(
                r'class="u-clickable-card__link"><span>(.*?)<\/', news_html).group(1)
            description = re.search(r'<p>(.*?)<\/p>', news_html).group(1)

            try:
                picture_filename = re.search(
                    r'alt="(.*?)"', news_html).group(1)
            except Exception as e:
                picture_filename = None
                logger.error(f"Image name not found. Error: {e}")

            try:
                image_link = re.search(r'src="(.*?)"', news_html).group(1)
            except AttributeError:
                image_link = None
                logger.error("Image link not found.")

            count_phrase = count_search_phrase(title, description, search_term)
            money = check_money(title, description)

            news_data.append({
                "title": title,
                "description": description,
                "date": date_formated,
                "picture_filename": picture_filename,
                "image_link": image_link,
                "count_phrase": count_phrase,
                "money": money,
                "image_file": image_file
            })

        df = pd.DataFrame(news_data)
        logger.info(f"dados do dataframe {df}")

        return df
    except Exception as e:
        logger.error(f"Error extracting news data: {e}")
        raise


def count_search_phrase(title, description, search_term):
    try:
        phrase_to_count = (str(title) + str(description)).lower()
        return phrase_to_count.count(search_term.lower())
    except Exception as e:
        logger.error(f"Error counting search phrase: {e}")
        raise


def check_money(title, description):
    try:
        regex_coin = re.compile(
            r'\$(\d+\.\d+|\d+(,\d+)*(\.\d+)?)|(\d+)\s*dollars|\d+\s*USD')
        phrase_to_check = (title + description).lower()
        return bool(re.search(regex_coin, phrase_to_check))
    except Exception as e:
        logger.error(f"Error checking money references: {e}")
        raise


def download_images(df):
    try:
        df_images = df[['image_link', 'image_file']]

        for index, row in df_images.iterrows():
            try:
                browser.go_to(row['image_link'])
                image_path = f"output/pictures/{row['image_file']}.png"
                browser.capture_element_screenshot("tag:img", image_path)
            except Exception as e:
                logger.error(
                    f"Failed to save image: {row['image_file']}. Error: {e}")
    except Exception as e:
        logger.error(f"Error in download_images function: {e}")
        raise


def save_news_data(df):
    try:
        df.drop('image_link', axis=1, inplace=True)
        df.to_excel("output/aljazeera_news_info.xlsx", index=False)
    except Exception as e:
        logger.error(f"Error saving news data: {e}")
        raise


if __name__ == "__main__":
    main()
