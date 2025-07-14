from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import csv
import time
from datetime import datetime

# Read secured party names from file
def read_secured_party_names(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

# Filter table data for UCC-1 records only
def filter_ucc1_records(table_data):
    if not table_data or len(table_data) < 2:  # Need at least header and one data row
        return []

    header = table_data[0]
    
    # Filter rows where Type contains "UCC-1"
    filtered_data = [header]  # Keep header
    for row in table_data[1:]:
        # Check if any cell in the row contains "UCC-1"
        if any('UCC-1' in str(cell).upper() for cell in row):
            filtered_data.append(row)
    
    return filtered_data

# Get current date for filename
current_date = datetime.now().strftime("%Y-%m-%d")
OUTPUT_CSV = f"WV_UCC1_{current_date}.csv"

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

try:
    # Navigate to the search page
    driver.get("https://apps.wv.gov/SOS/UCC/Search")
    time.sleep(2)

    # Click the 'Secured Party Search' button/tab
    search_type_button = driver.find_element(By.XPATH, '//*[@id="SearchTerms"]/div[1]/div/a[2]')
    search_type_button.click()
    time.sleep(1)

    # Set 'From Date' to 8 days before today using the datepicker
    from datetime import timedelta
    target_date = datetime.now() - timedelta(days=8)
    target_day = target_date.day
    target_month_year = target_date.strftime('%B %Y')

    from_date_field = driver.find_element(By.ID, 'txtFromDate')
    from_date_field.click()
    time.sleep(0.5)

    # Navigate to the correct month and year
    while True:
        switch = driver.find_element(By.CSS_SELECTOR, '.datepicker-days .datepicker-switch')
        current_month_year = switch.text.strip()
        if current_month_year == target_month_year:
            break
        elif target_date > datetime.strptime(current_month_year, '%B %Y'):
            next_btn = driver.find_element(By.CSS_SELECTOR, '.datepicker-days .next')
            next_btn.click()
        else:
            prev_btn = driver.find_element(By.CSS_SELECTOR, '.datepicker-days .prev')
            prev_btn.click()
        time.sleep(0.3)

    # Click the correct day
    day_cells = driver.find_elements(By.CSS_SELECTOR, '.datepicker-days td.day')
    for cell in day_cells:
        if cell.text == str(target_day) and 'old' not in cell.get_attribute('class') and 'new' not in cell.get_attribute('class'):
            cell.click()
            break
    time.sleep(1)

    for secured_party_name in secured_party_names:
        print(f"Processing: {secured_party_name}")
        
        # Type SECURED_PARTY_NAME into the search form
        search_form = driver.find_element(By.ID, 'searchTerm')
        search_form.clear()
        search_form.send_keys(secured_party_name)
        time.sleep(1)

        # Click the add button
        add_button = driver.find_element(By.XPATH, '//*[@id="SearchTerms"]/div[2]/div/form/button')
        add_button.click()
        time.sleep(10)

    # Click all available buttons in tblSearchTermResults/tbody/tr/td/button, rescanning after each click
    while True:
        buttons = driver.find_elements(By.XPATH, '//*[@id="tblSearchTermResults"]/tbody/tr/td/button')
        found_new = False
        for idx, button in enumerate(buttons):
            try:
                button.click()
                found_new = True
                time.sleep(10)
                break
            except Exception as e:
                print(f"Could not click button {idx}: {e}")
        if not found_new:
            break
    time.sleep(2)

    # Scan the ucc_table and download it to a CSV file
    try:
        ucc_table_xpath = '//*[@id="search"]/div[2]/div/div[1]/div/table'
        ucc_table = driver.find_element(By.XPATH, ucc_table_xpath)
        rows = ucc_table.find_elements(By.TAG_NAME, 'tr')
        table_data = []
        for row_idx in range(len(rows)):
            row = rows[row_idx]
            cols = row.find_elements(By.TAG_NAME, 'th')
            if not cols:
                cols = row.find_elements(By.TAG_NAME, 'td')
            table_data.append([col.text for col in cols[1:]])  # Skip first column

        # Filter for UCC-1 records only
        filtered_data = filter_ucc1_records(table_data)
        
        if filtered_data:
            if csv_header is None:
                csv_header = filtered_data[0]
            all_results.extend(filtered_data[1:])
            print(f"Found {len(filtered_data)-1} UCC-1 records")
        else:
            print(f"No UCC-1 records found")
            
    except Exception as e:
        print(f"Error processing table: {e}")

    # Save all results to CSV
    if all_results:
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Filing Number'] + csv_header)
            writer.writerows(all_results)
        print(f"Saved {len(all_results)} UCC-1 records to {OUTPUT_CSV}")
    else:
        print("No UCC-1 records found for any secured party")
finally:
    driver.quit()
