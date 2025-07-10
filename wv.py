from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

SECURED_PARTY_NAME = "Bank of America"  # Change this
OUTPUT_CSV = "WV_UCC1_Summary.csv"

# Set up headless Chrome browser with webdriver_manager
options = Options()
# options.add_argument('--headless')
options.add_argument('--disable-gpu')
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    # Navigate to the search page
    driver.get("https://apps.wv.gov/SOS/UCC/Search")
    time.sleep(2)

    # Click the 'Secured Party Search' button/tab
    search_type_button = driver.find_element(By.XPATH, '//*[@id="SearchTerms"]/div[1]/div/a[2]')
    search_type_button.click()
    time.sleep(1)

    # Type SECURED_PARTY_NAME into the search form
    search_form = driver.find_element(By.ID, 'searchTerm')
    search_form.clear()
    search_form.send_keys(SECURED_PARTY_NAME)
    time.sleep(1)

    # Click the add button
    add_button = driver.find_element(By.XPATH, '//*[@id="SearchTerms"]/div[2]/div/form/button')
    add_button.click()
    time.sleep(10)

    # Click all available buttons in tblSearchTermResults/tbody/tr/td/button, rescanning after each click
    clicked_indices = set()
    while True:
        buttons = driver.find_elements(By.XPATH, '//*[@id="tblSearchTermResults"]/tbody/tr/td/button')
        found_new = False
        for idx, button in enumerate(buttons):
            if idx not in clicked_indices:
                try:
                    button.click()
                    clicked_indices.add(idx)
                    found_new = True
                    time.sleep(5)
                    break  # Re-scan after each click
                except Exception as e:
                    print(f"Could not click button {idx}: {e}")
                    clicked_indices.add(idx)
        if not found_new:
            break
    time.sleep(2)

    # Scan the ucc_table and download it to a CSV file
    ucc_table_xpath = '//*[@id="search"]/div[2]/div/div[1]/div/table'
    ucc_table = driver.find_element(By.XPATH, ucc_table_xpath)
    rows = ucc_table.find_elements(By.TAG_NAME, 'tr')
    table_data = []
    for row_idx in range(len(rows)):
        print("row_idx: ", row_idx)
        # Re-find the table and rows to avoid stale references
        ucc_table = driver.find_element(By.XPATH, ucc_table_xpath)
        rows = ucc_table.find_elements(By.TAG_NAME, 'tr')
        row = rows[row_idx]
        print("row: ", row)
        cols = row.find_elements(By.TAG_NAME, 'th')
        if not cols:
            cols = row.find_elements(By.TAG_NAME, 'td')
        table_data.append([col.text for col in cols])

    # Save to CSV
    df = pd.DataFrame(table_data)
    df.to_csv('ucc_table.csv', index=False, header=False)


finally:
    driver.quit()
