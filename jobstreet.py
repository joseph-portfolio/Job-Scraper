from seleniumbase import SB
import pandas as pd
import datetime
from lxml import etree
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from ai_summarize import summarize
import asyncio

def get_url (root_url, job_title, location, date_range, salary_range, salary_type, work_arrangement):
    job_title = job_title.replace(' ', '-')
    location = location.replace(' ', '-')
    template = '{}/{}-jobs/in-{}?daterange={}&salaryrange={}&salarytype={}&workarrangement={}'
    url = template.format(root_url,job_title, location, date_range, salary_range, salary_type, work_arrangement)

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
    title = 'Python'
    location = 'Metro Manila'
    date_range = '31' # Listed in the last X days
    salary_range = '30000-50000'
    salary_type = 'monthly'
    work_arrangement = '2%2C3' # Hybrid + Remote

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%H%M%S")

    df = pd.DataFrame()

    url = get_url(root_url, title, location, date_range, salary_range, salary_type, work_arrangement)

    with SB(uc_cdp=True, incognito=True) as sb:
        sb.driver.set_page_load_timeout(15)

        while True:
            sb.open(url)
            sb.sleep(1)

            raw_html = sb.get_page_source()
            soup = BeautifulSoup(raw_html, 'lxml')
            tree = etree.HTML(raw_html)
            articles = tree.xpath('//article[@data-card-type="JobCard"]')
            print(f"Number of jobs: {len(articles)}")
            
            for i, article in enumerate(articles, start=1):
                try:
                    # Click job posting
                    job_link_selector = f'//*[@id="jobcard-{i}"]/div[2]/a'
                    sb.wait_for_element_visible(job_link_selector, timeout=10)
                    sb.wait_for_element_clickable(job_link_selector, timeout=10)
                    sb.scroll_to(job_link_selector)

                    try:
                        sb.click(job_link_selector)
                    except:
                        sb.js_click(job_link_selector)

                    sb.sleep(1)

                    # Get updated job detail HTML
                    raw_html = sb.get_page_source()
                    tree = etree.HTML(raw_html)

                    # Job Title
                    try:
                        job_title = article.get('aria-label')
                    except:
                        job_title = None

                    # Job URL
                    try:
                        job_url = root_url + article.xpath('.//a[@data-automation="jobTitle"]/@href')[0]
                    except:
                        job_url = None

                    # Company Name
                    try:
                        company_name = article.xpath('.//a[@data-type="company"]//text()')[0].strip()
                    except:
                        company_name = None

                    # Company Location
                    try:
                        location = article.xpath('.//span[@data-type="location"]//text()')
                        company_location = ', '.join(location) if location else None
                    except:
                        company_location = None

                    # Salary Range
                    try:
                        salary_range = article.xpath('.//span[@data-automation="jobSalary"]//text()')[0].strip()
                    except:
                        salary_range = None
                    
                    # Summary (quick preview on card)
                    try:
                        summary_items = article.xpath('.//div[4]/ul/li/div[2]/span/text()')
                        summary = " ".join([item.strip() for item in summary_items if item.strip()]) or None
                    except:
                        summary = None

                    # Work Arrangement
                    try:
                        work_arrangement = article.xpath('.//span[@data-testid="work-arrangement"]//text()')[1].strip()
                    except:
                        work_arrangement = None

                    # Date Listed
                    try:
                        date_listed = article.xpath('.//div[3]/text()')[0].strip()
                        date_listed_parsed = parse_date_listed(date_listed, today)
                    except:
                        date_listed_parsed = None

                    try:
                        summary_items = article.xpath('.//div[4]/ul/li/div[2]/span/text()')
                        summary = " ".join([item.strip() for item in summary_items if item.strip()]) if summary_items else None
                    except Exception:
                        summary = None

                    # Extract full job description with retries
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            descriptions = tree.xpath('.//div[@data-automation="jobAdDetails"]//text()')
                            full_description = ' '.join(d.strip() for d in descriptions if d.strip())

                            ai_response = asyncio.run(summarize(full_description))
                            ai_summary = ai_response.get("summary")
                            hard_skills = ai_response.get("hard_skills")
                            soft_skills = ai_response.get("soft_skills")
                            required_experience = ai_response.get("required_experience")
                            # work_arrangement = ai_response.get("work_arrangement")

                            break
                        except Exception as e:
                            print(f"Attempt {attempt + 1} failed to extract full description for job {job_title}: {e}")
                            try:
                                sb.click(job_link_selector)
                            except:
                                sb.js_click(job_link_selector)
                            sb.sleep(1)
                            if attempt == max_retries - 1:
                                print("Failed to extract. None detected.")
                                ai_summary = hard_skills = soft_skills = required_experience = None

                    # Collect data
                    new_data = pd.DataFrame({
                        'Date Listed': [date_listed_parsed],
                        'Job Title': [job_title],
                        'Summary': [summary],
                        'AI Summary': [ai_summary],
                        'Hard Skills': [hard_skills],
                        'Soft Skills': [soft_skills],
                        'Required Experience': [required_experience],
                        'Company Name': [company_name],
                        'Location': [company_location],
                        'Link': [job_url],
                        'Date Extracted': [today],
                        'Salary Range': [salary_range],
                        'Salary Type': [salary_type],
                        'Work Arrangement': [work_arrangement]
                    })
                    df = pd.concat([df, new_data], ignore_index=True)

                except Exception as e:
                    print(f"Failed to scrape job {i}: {str(e)}")
                    continue

            # Move to next page
            try:
                url = root_url + soup.find('a', {'aria-label':'Next'}).get('href')
            except AttributeError:
                break

    title_filename = title.strip().replace(" ", "_")
    excel_filename = f"{title_filename}_jobstreet_{today}_{timestamp}.xlsx"
    df.to_excel(excel_filename, index=False)

if __name__ == '__main__':
    main()