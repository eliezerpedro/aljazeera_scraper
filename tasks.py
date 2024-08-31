import logging
from datetime import datetime
from time import sleep
import re
import pandas as pd
from dateutil.relativedelta import relativedelta

from RPA.Browser.Selenium import Selenium
from RPA.Robocorp.WorkItems import WorkItems
from robocorp.tasks import task

import locators as lc

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


class NewsScraper:
    def __init__(self):
        self.browser = Selenium()
        self.workitem = WorkItems()
        self.search_term = None
        self.months = None

    def initialize(self):
        try:
            self.workitem.get_input_work_item()
            self.search_term = self.workitem.get_work_item_variable(
                "search_term")
            self.months = int(self.workitem.get_work_item_variable("months"))
        except Exception as e:
            logger.error(f"Failed to initialize work item: {e}")
            raise

    def start_browser(self):
        logger.info("open the website")
        self.browser.open_available_browser("https://www.aljazeera.com/")
        self.browser.maximize_browser_window()

    def perform_search(self):
        try:
            logger.info("searching the term")
            self.browser.wait_until_element_is_enabled(lc.SEARCH_TRIGGER, 10)
            self.browser.click_button(lc.SEARCH_TRIGGER)

            self.browser.wait_until_element_is_enabled(lc.SEARCH_BAR_INPUT, 10)
            self.browser.input_text(lc.SEARCH_BAR_INPUT, self.search_term)
            self.browser.press_keys(lc.SEARCH_BAR_INPUT, "ENTER")

            logger.info("Sorting by date")
            self.browser.wait_until_element_is_enabled(lc.SORT_BY_DATE, 10)
            self.browser.click_element(lc.SORT_BY_DATE)
            self.browser.wait_until_element_is_visible(lc.NEWS_ARTICLES, 30)
        except Exception as e:
            logger.error(f"Error during search: {e}")
            raise

    def load_all_news(self):
        try:
            logger.info("Loading all news")
            while True:
                sleep(2)
                last_news_date = datetime.strptime(
                    self.get_last_news_date(), "%d/%m/%Y")
                desired_date = datetime.strptime(
                    self.first_day_of_month(), "%d/%m/%Y")

                if last_news_date > desired_date:
                    self.load_more_news()
                else:
                    break
        except Exception as e:
            logger.error(f"Error while loading news: {e}")
            raise

    def load_more_news(self):
        sleep(1)
        try:
            if self.browser.is_element_visible(lc.COOKIE_ACCEPT_BUTTON):
                self.browser.click_button(lc.COOKIE_ACCEPT_BUTTON)

            if self.browser.is_element_visible(lc.CLOSE_AD_BUTTON):
                self.browser.click_button(lc.CLOSE_AD_BUTTON)

            self.browser.scroll_element_into_view(lc.SHOW_MORE_BUTTON)
            self.browser.wait_until_element_is_visible(lc.SHOW_MORE_BUTTON, 10)
            self.browser.click_button(lc.SHOW_MORE_BUTTON)
        except Exception as e:
            logger.error(f"Error while loading more news: {e}")
            raise

    def get_last_news_date(self):
        try:
            self.browser.wait_until_element_is_visible(lc.NEWS_ARTICLES, 30)
            last_news = self.browser.find_elements(lc.NEWS_ARTICLES)[-1]
            logger.info(f"ultima data {last_news}")
            last_date = last_news.text.split(
                "\n")[-1].replace("Last update ", "")
            last_date_obj = datetime.strptime(last_date, "%d %b %Y")
            return last_date_obj.strftime("%d/%m/%Y")
        except Exception as e:
            logger.error(f"Error getting last news date: {e}")
            raise

    def first_day_of_month(self):
        try:
            current_date = datetime.now()
            if self.months <= 1:
                first_day = current_date.replace(day=1)
            else:
                target_date = current_date - \
                    relativedelta(months=self.months - 1)
                first_day = target_date.replace(day=1)
            return first_day.strftime("%d/%m/%Y")
        except Exception as e:
            logger.error(f"Error calculating first day of month: {e}")
            raise

    def extract_news_data(self):
        try:
            logger.info("Extracting news data")
            news_data = []
            sleep(1)

            for index, news_element in enumerate(self.browser.find_elements(lc.NEWS_ARTICLES)):
                news_html = news_element.get_attribute("outerHTML")
                data = news_element.text.split(
                    "\n")[-1].replace("Last update ", "")
                date_obj = datetime.strptime(data, "%d %b %Y")
                date_formated = date_obj.strftime("%d/%m/%Y")
                desired_date = datetime.strptime(
                    self.first_day_of_month(), "%d/%m/%Y")
                image_file = f"picture_{index}"

                if desired_date > date_obj:
                    break

                title = re.search(
                    r'class="u-clickable-card__link"><span>(.*?)<\/', news_html).group(1)
                description = re.search(r'<p>(.*?)<\/p>', news_html).group(1)

                picture_filename = self.extract_image_filename(news_html)
                image_link = self.extract_image_link(news_html)

                count_phrase = self.count_search_phrase(title, description)
                money = self.check_money(title, description)

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

    def extract_image_filename(self, news_html):
        try:
            return re.search(r'alt="(.*?)"', news_html).group(1)
        except Exception as e:
            logger.error(f"Image name not found. Error: {e}")
            return None

    def extract_image_link(self, news_html):
        try:
            return re.search(r'src="(.*?)"', news_html).group(1)
        except AttributeError:
            logger.error("Image link not found.")
            return None

    def count_search_phrase(self, title, description):
        try:
            phrase_to_count = (str(title) + str(description)).lower()
            return phrase_to_count.count(self.search_term.lower())
        except Exception as e:
            logger.error(f"Error counting search phrase: {e}")
            raise

    def check_money(self, title, description):
        try:
            regex_coin = re.compile(
                r'\$(\d+\.\d+|\d+(,\d+)*(\.\d+)?)|(\d+)\s*dollars|\d+\s*USD')
            phrase_to_check = (title + description).lower()
            return bool(re.search(regex_coin, phrase_to_check))
        except Exception as e:
            logger.error(f"Error checking money references: {e}")
            raise

    def download_images(self, df):
        try:
            logger.info("Downloading all images")
            df_images = df[['image_link', 'image_file']]

            for index, row in df_images.iterrows():
                try:
                    self.browser.go_to(row['image_link'])
                    image_path = f"output/{row['image_file']}.png"
                    self.browser.capture_element_screenshot(
                        "tag:img", image_path)
                except Exception as e:
                    logger.error(
                        f"Failed to save image: {row['image_file']}. Error: {e}")
        except Exception as e:
            logger.error(f"Error in download_images function: {e}")
            raise

    def save_news_data(self, df):
        try:
            logger.info("Saving all data in a excel file")
            df.drop('image_link', axis=1, inplace=True)
            df.to_excel("output/aljazeera_news_info.xlsx", index=False)
        except Exception as e:
            logger.error(f"Error saving news data: {e}")
            raise

    def run(self):
        try:
            self.initialize()
            self.start_browser()
            self.perform_search()
            self.load_all_news()
            df = self.extract_news_data()
            self.download_images(df)
            self.save_news_data(df)
        except Exception as e:
            logger.error(f"An error occurred in the main task: {e}")
            raise
        finally:
            logger.info("All clear. Closing the browser.")
            self.browser.close_all_browsers()


@task
def main():
    scraper = NewsScraper()
    scraper.run()


if __name__ == "__main__":
    main()
