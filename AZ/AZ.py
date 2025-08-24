import csv
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Config ---
input_file = "secured_party_names.txt"
output_file = "ucc_results.csv"
url = "https://apps.azsos.gov/apps/ucc/search/"

# --- Read names ---
with open(input_file, "r", encoding="utf-8") as f:
    secured_party_names = [line.strip() for line in f if line.strip()]

# --- CSV Setup ---
with open(output_file, "w", newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Secured Party", "Filing Number", "Filing Type", "Filing Date", "Debtor Name", "Status"])

    for name in secured_party_names:
        # Open new browser instance
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Optional: only enable after testing
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 15)

        try:
            driver.get(url)
            time.sleep(5)  # Cloudflare challenge time

            # Select "Organization" radio
            org_radio = wait.until(EC.element_to_be_clickable((By.ID, "PageContent_PageContent_OrganizationRadioButtonList_1")))
            org_radio.click()
            time.sleep(1.5)

            # Type secured party name
            name_input = driver.find_element(By.ID, "ctl00_ctl00_PageContent_PageContent_OrganizationTextBox")
            name_input.clear()
            time.sleep(0.5)
            name_input.send_keys(name)
            time.sleep(1.5)

            # Input date (7 days ago)
            begin_date = (datetime.today() - timedelta(days=37)).strftime("%m/%d/%Y")
            date_input = driver.find_element(By.ID, "ctl00_ctl00_PageContent_PageContent_BeginDatePicker_dateInput")
            date_input.clear()
            time.sleep(0.5)
            date_input.send_keys(begin_date)
            time.sleep(1.5)

            # Click Search
            search_btn = driver.find_element(By.ID, "ctl00_ctl00_PageContent_PageContent_SearchButton_input")
            search_btn.click()
            time.sleep(5)  # Wait for table to load

            # Scrape results
            try:
                results_table = wait.until(EC.presence_of_element_located((By.ID, "ctl00_ctl00_PageContent_PageContent_ResultsGridView_ctl00")))
                rows = results_table.find_elements(By.XPATH, ".//tr")[1:]  # skip header
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    row_data = [col.text.strip() for col in cols]
                    writer.writerow(row_data)
            except Exception as inner_e:
                print(f"No results for '{name}' or table error: {inner_e}")

        except Exception as e:
            print(f"Error during processing '{name}': {e}")

        finally:
            driver.quit()
            time.sleep(2)  # Slight delay before reopening

print(f"\n✅ All done. Results saved to {output_file}")
