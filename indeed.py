from bs4 import BeautifulSoup
from seleniumbase import SB
import pandas as pd
from datetime import datetime 

def get_url (root_url, job_title, location, job_type):
    template = '{}/jobs?q={}&l={}&sc={}'
    url = template.format(root_url,job_title, location, job_type)
    return url

def main():
    root_url = "https://ph.indeed.com"
    title = 'python'
    location = 'philippines'
    # job_type = '0kf%3Aattr%287EQCZ%29%3B' # Fresh Grad
    job_type = ''

    today = datetime.now().strftime("%Y%m%d_%H%M%S")

    df = pd.DataFrame({
        'Job Title': [''],
        'Company Name': [''],
        'Location': [''],
        'Salary Range': [''],
        'Summary': [''],
        'Link': [''],
        'Date Extracted': ['']
    })

    #  Initial url
    url = get_url(root_url, title, location, job_type)

    with SB(uc_cdp=True, incognito=True) as sb:
        while True:
            """Bypass cloudflare"""
            while True:
                sb.open(url)
                sb.uc_gui_click_captcha()
                sb.sleep(10)

                try:
                    sb.assert_text("Find jobs", "button.yosegi-InlineWhatWhere-primaryButton[type='submit']")
                    print("Success")
                    break
                except Exception:
                    print("Retrying...")
                    continue 

            raw_html = sb.get_page_source()
            soup = BeautifulSoup(raw_html, 'lxml')
            cards = soup.find_all('div', 'job_seen_beacon')
            
            for card in cards:
                td_tag = card.table.tbody.tr.td

                # Job Title and URL
                try:
                    job_div = td_tag.find('div', {'class','css-pt3vth e37uo190'}).h2.a
                    job_title = job_div.span.get('title')
                except AttributeError:
                    job_title = None
                try:
                    job_url = root_url + job_div.get('href')
                except Exception:
                    job_url = None

                # Company Name
                try:
                    company_div = td_tag.find('div', {'class','company_location css-i375s1 e37uo190'})
                    company_name = company_div.find('div', {'class','css-1afmp4o e37uo190'}).span.text.strip()
                except AttributeError:
                    company_name = None

                # Company Location
                try:
                    company_location = company_div.find('div', {'class','css-1restlb eu4oa1w0'}).text.strip()
                except Exception:
                    company_location = None

                # Salary Range
                try:
                    metadata_div = td_tag.find('div', {'class','jobMetaDataGroup css-qspwa8 eu4oa1w0'}).ul
                    salary_range = metadata_div.find('li', {'class','css-u74ql7 eu4oa1w0'}).div.div.text.strip()
                except AttributeError:
                    salary_range = None

                # Summary
                try:
                    summary = card.find('div',{'class', 'underShelfFooter'}).div.div.ul.li.text.strip()
                except AttributeError:
                    summary = None

                new_data = pd.DataFrame({
                    'Job Title': [job_title],
                    'Company Name': [company_name],
                    'Location': [company_location],
                    'Salary Range': [salary_range],
                    'Summary': [summary],
                    'Link': [job_url],
                    'Date Extracted': [today]
                })
                df = pd.concat([df, new_data], ignore_index=True)

            # Move to next page
            try:
                url = root_url + soup.find('a', {'aria-label':'Next Page'}).get('href')
            except AttributeError:
                break
            
    # csv_filename = f"{title}_indeed_{today}.csv"
    excel_filename = f"{title}_indeed_{today}.xlsx"

    # df.to_csv(csv_filename, index=True)
    df.to_excel(excel_filename, index=False)

if __name__ == '__main__':
    main()