import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# --- Config ---
input_file = "secured_party_names.txt"
output_file = "ucc1_extracted_data.csv"
url = "https://corp.sec.state.ma.us/corpweb/uccsearch/uccSearch.aspx"

# --- Read names ---
with open(input_file, "r", encoding="utf-8") as f:
    secured_party_names = [line.strip() for line in f if line.strip()]

# --- Open output CSV file ---
with open(output_file, "w", encoding='utf-8', newline='') as f_out:
    writer = csv.writer(f_out)
    writer.writerow([
        "Filing Number", "Filing Date", "Debtor Name", "Debtor Address", "Debtor City",
        "Secured Party Name", "Secured Party Address", "Secured Party City"
    ])

    for name in secured_party_names:
        chrome_options = Options()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 15)

        try:
            driver.get(url)
            time.sleep(5)

            wait.until(EC.element_to_be_clickable((By.ID, "MainContent_rdoSearchO"))).click()
            time.sleep(5)

            name_input = wait.until(EC.element_to_be_clickable((By.ID, "MainContent_txtName")))
            name_input.clear()
            time.sleep(0.5)
            name_input.send_keys(name)
            time.sleep(1.5)

            wait.until(EC.element_to_be_clickable((By.ID, "MainContent_UCCSearchMethodO"))).click()
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="MainContent_UCCSearchMethodO"]/option[2]'))).click()
            time.sleep(5)

            wait.until(EC.element_to_be_clickable((By.ID, "MainContent_chkDebtor"))).click()
            time.sleep(5)

            wait.until(EC.element_to_be_clickable((By.ID, "MainContent_chkSecuredParty"))).click()
            time.sleep(5)

            wait.until(EC.element_to_be_clickable((By.ID, "MainContent_ddRecordsPerPage"))).click()
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="MainContent_ddRecordsPerPage"]/option[2]'))).click()
            time.sleep(5)

            driver.find_element(By.ID, "MainContent_btnSearch").click()
            time.sleep(10)

            links = driver.find_elements(By.XPATH, '//a[contains(@href, "UCCFilingHistory.aspx?sysvalue=")]')

            for i in range(0, len(links)):
                links = driver.find_elements(By.XPATH, '//a[contains(@href, "UCCFilingHistory.aspx?sysvalue=")]')
                link = links[i]
                href = link.get_attribute("href")
                if href:
                    driver.execute_script("window.open(arguments[0], '_blank');", href)
                    time.sleep(1)
                    driver.switch_to.window(driver.window_handles[-1])
                    time.sleep(5)

                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    rows = soup.select("table#MainContent_tblFilingHistory tr")

                    filing_number = filing_date = ""
                    debtor_name = debtor_address = debtor_city = ""
                    secured_name = secured_address = secured_city = ""

                    is_ucc1 = False
                    in_debtor_section = False
                    in_secured_section = False

                    for tr in rows:
                        if tr.get("style") == "color:White;background-color:Gray;":
                            is_ucc1 = "UCC-1" in tr.get_text(strip=True).upper()
                            in_debtor_section = False
                            in_secured_section = False
                            continue

                        if is_ucc1:
                            if not filing_number and "filing number" in tr.get_text().lower():
                                tds = tr.find_all("td")
                                lines = tds[1].get_text(separator="\n").strip().split("\n")
                                if len(lines) >= 2:
                                    filing_number = lines[0].strip()
                                    filing_date = lines[1].strip()
                            if tr.get_text(strip=True) == "Debtor(s)":
                                in_debtor_section = True
                                in_secured_section = False
                                continue

                            if tr.get_text(strip=True) == "Secured Parties":
                                in_secured_section = True
                                in_debtor_section = False
                                continue

                            if in_debtor_section and not debtor_name:
                                tds = tr.find_all("td")
                                if tds:
                                    lines = tds[0].get_text(separator="\n").split("\n")
                                    if len(lines) >= 3:
                                        debtor_name = lines[0].strip()
                                        debtor_address = lines[1].strip()
                                        debtor_city = lines[2].strip()

                            if in_secured_section and not secured_name:
                                tds = tr.find_all("td")
                                if tds:
                                    lines = tds[0].get_text(separator="\n").split("\n")
                                    if len(lines) >= 3:
                                        secured_name = lines[0].strip()
                                        secured_address = lines[1].strip()
                                        secured_city = lines[2].strip()
                                break

                    if is_ucc1:
                        writer.writerow([
                            filing_number, filing_date, debtor_name, debtor_address, debtor_city,
                            secured_name, secured_address, secured_city
                        ])

                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    time.sleep(1)

        except Exception as e:
            print(f"⚠️ Error during processing '{name}': {e}")

        finally:
            driver.quit()
            time.sleep(2)

print(f"\n✅ All done. Data saved to {output_file}")
