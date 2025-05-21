from bs4 import BeautifulSoup
from seleniumbase import SB
import pandas as pd

def get_url (indeed_url, job_title, location, job_type):
    template = '{}/jobs?q={}&l={}&sc={}'
    url = template.format(indeed_url,job_title, location, job_type)
    return url

def main():
    indeed_url = "https://ph.indeed.com"
    title = 'python'
    location = 'philippines'
    filter = '0kf%3Aattr%287EQCZ%29%3B'

    df = pd.DataFrame({
        'Job Title': [''],
        'Company Name': [''],
        'Location': [''],
        'Salary Range': [''],
        'Summary': [''],
        'Link': ['']
    })

    with SB(uc_cdp=True, incognito=True) as sb:
        while True:  # Loop until the text is found
            url = get_url(indeed_url, title, location, filter)
            sb.open(url)
            sb.uc_gui_click_captcha()
            sb.sleep(20) # Adjust values depending on load time

            try:
                sb.assert_text("Find jobs", "button.yosegi-InlineWhatWhere-primaryButton[type='submit']")
                print("Text Found")
                break  # Exit loop if text is found
            except Exception:
                print("Text not found. Retrying...")
                continue  # Retry from sb.open(url)

        raw_html = sb.get_page_source()
        soup = BeautifulSoup(raw_html, 'lxml')
        cards = soup.find_all('div', 'job_seen_beacon')
        
        # Testing for single record

        for card in cards:
            td_tag = card.table.tbody.tr.td

            # Job Title and URL
            try:
                job_div = td_tag.find('div', {'class','css-pt3vth e37uo190'}).h2.a
                job_title = job_div.span.get('title')
            except AttributeError:
                job_title = None
            try:
                job_url = indeed_url + job_div.get('href')
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
                'Link': [job_url]
            })
            df = pd.concat([df, new_data], ignore_index=True)

            print(df)

            # print(job_title)
            # print(job_url)
            # print(company_name)
            # print(company_location)
            # print(salary_range)
            # print(summary)

if __name__ == '__main__':
    main()