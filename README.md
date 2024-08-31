# Aljazeera Scraper

## Overview

This project uses RPA to fetch information from the website https://www.aljazeera.com/ and stores the obtained data in an excel file.


## Configured Variables

 

- Search phrase
- Number of months for which news is to be received

  

## Challenge

  

This challenge only uses Python with the RPA Framework's Selenium library and Pandas. I split this challenge into the following steps:

  

1. Open the Aljazeera website using Selenium.
2. Type the search phrase in the search field and press enter.
3. Filter by the most recent news.
4. Navigate to the latest news in the given date range.
5. Extract the news info, including title, date, description, and picture filename.
6. Count  occurrences of search  terms in titles  and  descriptions.
7. Checks whether the title or description contains an amount in the specified format.
8. Save all the the extracted data in an Excel file.
9. Download all the pictures from the news and store in a picture folder.

  

## Requirements

  



- Python 3.x
- RPA Framework
- Pandas

  

## How to Run

  

1. Clone the repository.
2. Install the dependencies using pip

  

```bash

pip  install  rpaframework
pip  install  pandas

```

  

3. Change the work-items.json file with the desired values for the search term and number of months.

4. Run the Python script 

  

```bash

python  tasks.py

```


5. After  the  script  has  finished  running, you  can  find  the  extracted  news  data in the `aljazeera_news_info.xlsx` file and the pictures in the pictures folder.


---