import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Config ---
input_file = "secured_party_names.txt"
output_file = "links.txt"
url = "https://web.sos.ky.gov/ftucc/(S(ay1wb2mthqchiqgedu15z3xa))/search.aspx"

# --- Read names ---
with open(input_file, "r", encoding="utf-8") as f:
    secured_party_names = [line.strip() for line in f if line.strip()]

# --- Open output file ---
with open(output_file, "w", encoding='utf-8', newline='') as f_out:

    for name in secured_party_names:
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Optional for silent run
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 15)

        try:
            driver.get(url)
            time.sleep(5)  # Cloudflare challenge

            # Input secured party name
            name_input = wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_SearchForm1_tOrgname")))
            name_input.clear()
            time.sleep(0.5)
            name_input.send_keys(name)
            time.sleep(1.5)

            # Click Search
            search_btn = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_SearchForm1_bSearch")
            search_btn.click()
            time.sleep(15)


            # Extract result links
            links = driver.find_elements(By.XPATH, '//a[contains(@href, "search.aspx?filing=")]')

            for link in links:
                href = link.get_attribute("href")
                if href:
                    f_out.write(f"{name},{href}\n")

        except Exception as e:
            print(f"⚠️ Error during processing '{name}': {e}")

        finally:
            driver.quit()
            time.sleep(2)

print(f"\n✅ All done. Links saved to {output_file}")
