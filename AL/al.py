from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import csv
import time
from datetime import datetime, timedelta

# Read secured party names from file
def read_secured_party_names(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

from datetime import datetime

# Get current date for filename
current_date = datetime.now().strftime("%Y-%m-%d")
OUTPUT_CSV = f"AL_UCC1_{current_date}.csv"

# Read secured party names
secured_party_names = read_secured_party_names("secured_party_names.txt")
all_results = []
csv_header = None

# Set up headless Chrome browser with webdriver_manager
options = Options()
# options.add_argument('--headless')
options.add_argument('--disable-gpu')
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

driver.maximize_window()

for secured_party_name in secured_party_names:
    print(f"Processing: {secured_party_name}")
        
    try:
        driver.get("https://www.alabamainteractive.org/ucc_filing/NewSearch.do")
        time.sleep(2)

        from selenium.common.exceptions import NoSuchElementException

        filer_type_xpath = '/html/body/table/tbody/tr[1]/td/table/tbody/tr[7]/td/form/table/tbody/tr[4]/td/table/tbody/tr[12]/td[2]/input[3]'
        try:
            filer_type_button = driver.find_element(By.XPATH, filer_type_xpath)
        except NoSuchElementException:
            # If not found, reload and try again once
            driver.refresh()
            time.sleep(2)
            filer_type_button = driver.find_element(By.XPATH, filer_type_xpath)
        filer_type_button.click()
        time.sleep(1)

        entry_type_button = driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/table/tbody/tr[7]/td/form/table/tbody/tr[4]/td/table/tbody/tr[13]/td[2]/input[3]')
        entry_type_button.click()
        time.sleep(1)

        # filing_state_button = driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/table/tbody/tr[7]/td/form/table/tbody/tr[4]/td/table/tbody/tr[14]/td[2]/input[2]')
        # filing_state_button.click()
        # time.sleep(1)

        search_option_button = driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/table/tbody/tr[7]/td/form/table/tbody/tr[4]/td/table/tbody/tr[19]/td[2]/input[1]')
        search_option_button.click()
        time.sleep(1)

        search_form = driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/table/tbody/tr[7]/td/form/table/tbody/tr[4]/td/table/tbody/tr[22]/td[2]/input')
        search_form.clear()
        search_form.send_keys(secured_party_name)
        time.sleep(1)

        continue_button = driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/table/tbody/tr[7]/td/form/table/tbody/tr[4]/td/table/tbody/tr[24]/td/input[1]')
        continue_button.click()
        time.sleep(10)

        # Find all <a> elements whose href attribute starts with "SearchDetail.do?id="
        detail_links = driver.find_elements(By.XPATH, '//a[starts-with(@href, "SearchDetail.do?id=")]')
        for i in range(len(detail_links)):
            try:
                detail_links = driver.find_elements(By.XPATH, '//a[starts-with(@href, "SearchDetail.do?id=")]')
                link = detail_links[i]
                link.click()
                time.sleep(10)

                # Locate the table
                table = driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/table/tbody/tr[6]/td/table')
                rows = table.find_elements(By.TAG_NAME, "tr")

                # Extract table data
                table_data = []
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if not cells:
                        cells = row.find_elements(By.TAG_NAME, "th")
                    row_data = [cell.text.strip() for cell in cells]
                    if row_data:
                        table_data.append(row_data)

                # Set header if not set
                if table_data and csv_header is None:
                    csv_header = table_data[0]

                # Add all data rows (skip header)
                if table_data and len(table_data) > 1:
                    all_results.extend(table_data[1:])

                driver.back()
                time.sleep(5)
            except Exception as e:
                print(f"Could not click detail link: {e}")
    except Exception as e:
        print(f"Error processing table: {e}")

# Write all results to a single CSV at the end
if csv_header and all_results:
    with open(OUTPUT_CSV, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(csv_header)
        writer.writerows(all_results)
    print(f"Saved {len(all_results)} records to {OUTPUT_CSV}")
else:
    print("No records found to save.")
