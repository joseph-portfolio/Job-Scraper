import requests
from bs4 import BeautifulSoup
from lxml import etree
from datetime import datetime
import pandas as pd
from seleniumbase import SB

def get_url (title, location, last_listed, work_type, experience):
    template = 'https://www.linkedin.com/jobs/search?keywords={}&location={}&geoId=103121230&f_TPR={}&f_WT={}&f_E={}&position=1&pageNum=0'
    url = template.format(title, location, last_listed, work_type, experience)
    return url

def main():
    title = 'Python'
    location = 'Philippines'
    tpr = '' # Last listed
    # work_type = '3%2C2' # Hybrid + Remote + Listed Past Month
    work_type = '3%2C3' # Hybrid + Remote + Listed Past Week
    experience = '2' # Entry level

    url = get_url (title, location, tpr, work_type, experience)

    with SB(uc_cdp=True, incognito=True) as sb:
        sb.open(url)
        sb.sleep(2)

        # Close login popup if it exists
        if sb.is_element_present("#base-contextual-sign-in-modal > div > section > button"):
            sb.click("#base-contextual-sign-in-modal > div > section > button")
            sb.sleep(1)

        end_message = "You've viewed all jobs for this search"

        while True:
            # Scroll to bottom with smooth behavior (more human-like)
            sb.execute_script("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
            sb.sleep(0.25)  # Slightly longer pause to allow loading
            
            # Check if we've reached the end (no more content loaded)
            if sb.is_text_visible(end_message):
                break
                
            # Try to click "See More" button if it appears (with better waiting)
            see_more_button = 'button:contains("See more jobs")'
            if sb.is_element_present(see_more_button):
                try:
                    sb.scroll_to(see_more_button)
                    sb.click(see_more_button)
                    sb.sleep(1)
                    continue
                except:
                    pass  # Continue with scrolling if click fails 

        raw_html = sb.get_page_source()
        soup = BeautifulSoup(raw_html, 'lxml')
        tree = etree.HTML(str(soup))
        cards = tree.xpath('//*[@id="main-content"]/section[2]/ul/li[*]/div')
        print(len(cards))

        today = datetime.now().strftime("%Y-%m-%d")

        df = pd.DataFrame({
            'Job Title': [''], #
            'Company Name': [''], #
            'Location': [''], #
            'Salary Range': [''],
            'Summary': [''],
            'Work Arrangement': [''],
            'Date Listed': [''], #
            'Date Extracted': [''], #
            'Link': [''] #
        })
        for i, card in enumerate (cards , start=1):
            try:
                # Click job posting
                job_link_selector = f'//*[@id="main-content"]/section[2]/ul/li[{i}]/div/a'
                
                sb.wait_for_element_visible(job_link_selector, timeout=10)
                sb.wait_for_element_clickable(job_link_selector, timeout=10)
                
                sb.scroll_to(job_link_selector)
                sb.sleep(0.5)  # Small pause after scrolling
                
                # Click using JavaScript as a fallback
                try:
                    sb.click(job_link_selector)
                except:
                    sb.js_click(job_link_selector)
                
                sb.sleep(4)

                try:
                    job_title = card.xpath('.//*[@class="base-search-card__title"]')[0].text.strip()
                except Exception:
                    job_title = None

                try:
                    company_name = card.xpath('.//*[@class="base-search-card__subtitle"]/a')[0].text.strip()
                except Exception:
                    company_name = None

                try:
                    location = card.xpath('.//*[@class="job-search-card__location"]')[0].text.strip()
                except Exception:
                    location = None

                try:
                    date_listed = card.xpath('.//time[@class="job-search-card__listdate"]/@datetime')[0].strip()
                except Exception:
                    date_listed = None

                try:
                    job_url = card.xpath('.//a[@href]/@href')[0].strip()
                except Exception:
                    job_url = None

                try:
                    # Get fresh HTML after clicking the job posting
                    raw_html = sb.get_page_source()
                    soup = BeautifulSoup(raw_html, 'lxml')
                    tree = etree.HTML(str(soup))
                    
                    descriptions = tree.xpath('//div[contains(@class, "show-more-less-html__markup")]//li/text()')
                    summary = ' '.join(descriptions)
                except Exception:
                    summary = None

                new_data = pd.DataFrame({
                    'Job Title': [job_title],
                    'Company Name': [company_name],
                    'Location': [location],
                    'Summary': [summary],
                    'Date Listed': [date_listed],
                    'Date Extracted': [today], 
                    'Link': [job_url]
                })
                df = pd.concat([df, new_data], ignore_index=True)

            except Exception as e:
                print(f"Failed to click job {i}: {str(e)}")
                continue  # Skip to next job if this one fails

    # csv_filename = f"{title}_linkedin_{today}.csv"
    excel_filename = f"{title}_linkedin_{today}.xlsx"

    # df.to_csv(csv_filename, index=True)
    df.to_excel(excel_filename, index=False)

if __name__ == '__main__':
    main()


