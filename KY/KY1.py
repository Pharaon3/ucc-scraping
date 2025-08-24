import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Config ---
input_file = "links.txt"
output_file = "KY_UCC1.csv"

# --- Read links ---
with open(input_file, "r", encoding="utf-8") as f:
    rows = [line.strip().split(",") for line in f if line.strip()]
    name_link_pairs = [(row[0], row[1]) for row in rows if len(row) == 2]

# --- CSV Output Setup ---
with open(output_file, "w", newline='', encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([
        "Secured Party Name",
        "File Number", "File Date", "Lapse Date", "Status", "Action",
        "Debtor", "Debtor Address", "Debtor City",
        "Secured Party", "Secured Party Address", "Secured Party City",
        "Filer", "Filer Address", "Filer City", "Document Type", "Processed"
    ])

    for secured_party_name, link in name_link_pairs:
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Optional for silent run
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 15)

        try:
            driver.get(link)
            time.sleep(3)

            def get_text(xpath):
                try:
                    return driver.find_element(By.XPATH, xpath).text.strip()
                except:
                    return ""

            def get_textnode(xpath, index):
                try:
                    node = driver.find_element(By.XPATH, xpath)
                    return node.parent.execute_script("return arguments[0].textContent", node).split('\n')[index].strip()
                except:
                    return ""

            # Extract data
            file_number = get_text('//*[@id="ctl00_ContentPlaceHolder1_showentity1_Filenumber"]')
            file_date = get_text('//*[@id="ctl00_ContentPlaceHolder1_showentity1_Filedate"]')
            lapse_date = get_text('//*[@id="ctl00_ContentPlaceHolder1_showentity1_Lapsedate"]')
            status = get_text('//*[@id="ctl00_ContentPlaceHolder1_showentity1_status"]')
            action = get_text('//*[@id="ctl00_ContentPlaceHolder1_showentity1_actionstable"]/tbody/tr[2]/td[1]')
            document_type = get_text('//*[@id="ctl00_ContentPlaceHolder1_showentity1_imagestable"]/tbody/tr[2]/td[1]')

            # For text nodes, we extract them from parent td manually
            def extract_td_texts(row, td, index):
                try:
                    td_element = driver.find_element(By.XPATH, f'//*[@id="ctl00_ContentPlaceHolder1_showentity1_namestable"]/tbody/tr[{row}]/td[{td}]')
                    lines = td_element.text.split("\n")
                    return lines[index].strip() if index < len(lines) else ""
                except:
                    return ""

            debtor = extract_td_texts(2, 1, 1)
            debtor_address = extract_td_texts(2, 3, 0)
            debtor_city = extract_td_texts(2, 3, 1)

            secured_party = extract_td_texts(3, 1, 1)
            secured_party_address = extract_td_texts(3, 3, 0)
            secured_party_city = extract_td_texts(3, 3, 1)

            filer = extract_td_texts(4, 1, 1)
            filer_address = extract_td_texts(4, 3, 0)
            filer_city = extract_td_texts(4, 3, 1)

            processed = time.strftime("%Y-%m-%d %H:%M:%S")

            writer.writerow([
                secured_party_name,
                file_number, file_date, lapse_date, status, action,
                debtor, debtor_address, debtor_city,
                secured_party, secured_party_address, secured_party_city,
                filer, filer_address, filer_city, document_type, processed
            ])

        except Exception as e:
            print(f"⚠️ Error processing {link}: {e}")

        finally:
            driver.quit()
            time.sleep(1)

print(f"\n✅ All done. Data saved to {output_file}")
