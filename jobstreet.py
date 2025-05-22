from seleniumbase import SB
import pandas as pd
import datetime
from lxml import html
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

def get_url (root_url, job_title, location, date_range, work_arrangement):
    job_title = job_title.replace(' ', '-')
    location = location.replace(' ', '-')
    template = '{}/{}-jobs/in-{}?daterange={}?workarrangement={}'
    url = template.format(root_url,job_title, location, date_range, work_arrangement)
    return url

def parse_date_listed(date_listed_str, date_extracted_str):
    if not date_listed_str:
        return None
    date_listed_str = date_listed_str.lower()
    word_to_num = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
        'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18,
        'nineteen': 19, 'twenty': 20, 'twenty one': 21, 'twenty two': 22,
        'twenty three': 23, 'twenty four': 24, 'twenty five': 25,
        'twenty six': 26, 'twenty seven': 27, 'twenty eight': 28,
        'twenty nine': 29, 'thirty': 30, 'thirty one': 31
    }
    # Handle "more than thirty days ago"
    if "more than thirty days ago" in date_listed_str:
        return "30+ days ago"
    # Extract number and unit
    match = re.search(r'listed ([a-z\s\d]+) (hour|day)s? ago', date_listed_str)
    if not match:
        return None
    num_str, unit = match.groups()
    num_str = num_str.strip()
    try:
        num = int(num_str)
    except ValueError:
        num = word_to_num.get(num_str, None)
    if num is None:
        return None
    date_extracted = datetime.strptime(date_extracted_str, "%Y-%m-%d")
    if unit == 'day':
        date_listed = date_extracted - timedelta(days=num)
    elif unit == 'hour':
        date_listed = date_extracted - timedelta(hours=num)
    else:
        return None
    return date_listed.strftime("%Y-%m-%d")

def main():
    root_url = "https://ph.jobstreet.com"
    title = 'python'
    location = 'Metro Manila'
    date_range = '31' # Listed in the last X days
    work_arrangement = '2%2C3' # Hybrid + Remote

    today = datetime.now().strftime("%Y-%m-%d")

    df = pd.DataFrame({
        'Job Title': [''],
        'Company Name': [''],
        'Location': [''],
        'Salary Range': [''],
        'Summary': [''],
        'Link': [''],
        'Work Arrangement': [''],
        'Date Listed': [''],
        'Date Extracted': ['']
    })

   #  Initial url
    url = get_url(root_url, title, location, date_range, work_arrangement)

    with SB(uc_cdp=True, incognito=True) as sb:
        while True: 
            sb.open(url)
            raw_html = sb.get_page_source()
            soup = BeautifulSoup(raw_html, 'lxml')
            tree = html.fromstring(raw_html)
            articles = tree.xpath('//article[@data-card-type="JobCard"]')
            
            for article in articles:
                # Job Title
                try:
                    job_title = article.get('aria-label')
                except Exception:
                    job_title = None

                # Job URL
                try:
                    job_url = root_url + article.xpath('.//a[@data-automation="jobTitle"]/@href')[0]
                except Exception:
                    job_url = None

                # Company Name
                try:
                    company_name = article.xpath('.//div[4]/div[1]/div[1]/div/div[2]/div/div/span/div/a/text()')[0].strip()
                except Exception:
                    company_name = None

                # Company Location
                try:
                    loc1 = article.xpath('.//div[4]/div[3]/div[1]/span/span[1]/span/text()')
                    loc2 = article.xpath('.//div[4]/div[3]/div[1]/span/span[2]/span/text()')
                    locations = [l.strip() for l in loc1 + loc2 if l and l.strip()]
                    company_location = " ".join(locations) if locations else None
                except Exception:
                    company_location = None

                # Salary Range
                try:
                    salary_range = article.xpath('.//div[4]/div[3]/div[2]/span/span/text()')[0].strip()
                except Exception:
                    salary_range = None
                    
                try:
                    summary_items = article.xpath('.//div[4]/ul/li/div[2]/span/text()')
                    summary = " ".join([item.strip() for item in summary_items if item.strip()]) if summary_items else None
                except Exception:
                    summary = None

                # Work Arrangement
                try:
                    work_arrangement = article.xpath('.//div[4]/div[3]/div[1]/span/span[3]/text()')[1].strip()
                except Exception:
                    work_arrangement = None

                # Date Listed
                try:
                    date_listed = article.xpath('.//div[3]/text()')[0].strip()
                except Exception:
                    date_listed = None

                date_listed_parsed = parse_date_listed(date_listed, today)

                new_data = pd.DataFrame({
                    'Job Title': [job_title],
                    'Company Name': [company_name],
                    'Location': [company_location],
                    'Salary Range': [salary_range],
                    'Summary': [summary],
                    'Link': [job_url],
                    'Work Arrangement': [work_arrangement],
                    'Date Listed': [date_listed_parsed],
                    'Date Extracted': [today]  # New column for date extracted
                })
                df = pd.concat([df, new_data], ignore_index=True)

            # Move to next page
            try:
                url = root_url + soup.find('a', {'aria-label':'Next'}).get('href')
            except AttributeError:
                break

    # csv_filename = f"jobstreet_jobs_{today}.csv"
    excel_filename = f"{title}_jobstreet_{today}.xlsx"

    # df.to_csv(csv_filename, index=True)
    df.to_excel(excel_filename, index=False)

if __name__ == '__main__':
    main()