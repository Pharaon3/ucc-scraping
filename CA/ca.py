import time
import csv
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Read secured party names
with open('secured_party_names.txt', 'r', encoding='utf-8') as f:
    party_names = [line.strip() for line in f if line.strip()]

output_file = 'ucc_results.csv'
header = ['Party Name']
rows_data = []
sidebar_fields_set = set()

def parse_address(address: str) -> dict:
    """Parse a full address string into components."""
    if not address or address.strip() == '':
        return {'street': '', 'city': '', 'state': '', 'zip_code': ''}
    
    address = address.strip()
    
    # Handle PO Box addresses
    if address.upper().startswith('PO BOX') or address.upper().startswith('P.O. BOX'):
        return parse_po_box_address(address)
    
    # Handle complex addresses with multiple lines or special formatting
    if ',' in address:
        return parse_comma_separated_address(address)
    
    # Handle simple addresses without commas
    return parse_simple_address(address)

def parse_po_box_address(address: str) -> dict:
    """Parse PO Box addresses."""
    po_match = re.search(r'PO\.?\s*BOX\s+(\d+)', address, re.IGNORECASE)
    if po_match:
        po_number = po_match.group(1)
        remaining = address.replace(po_match.group(0), '').strip()
        if remaining.startswith(','):
            remaining = remaining[1:].strip()
        
        city_state_zip = parse_city_state_zip(remaining)
        
        return {
            'street': f"PO BOX {po_number}",
            'city': city_state_zip.get('city', ''),
            'state': city_state_zip.get('state', ''),
            'zip_code': city_state_zip.get('zip_code', '')
        }
    
    return {'street': address, 'city': '', 'state': '', 'zip_code': ''}

def parse_comma_separated_address(address: str) -> dict:
    """Parse addresses with comma separators."""
    parts = [part.strip() for part in address.split(',')]
    
    if len(parts) >= 3:
        street = parts[0]
        city = parts[1]
        state_zip = parts[2]
        
        state_zip_parsed = parse_city_state_zip(state_zip)
        
        return {
            'street': street,
            'city': city,
            'state': state_zip_parsed.get('state', ''),
            'zip_code': state_zip_parsed.get('zip_code', '')
        }
    elif len(parts) == 2:
        street = parts[0]
        city_state_zip = parts[1]
        
        parsed = parse_city_state_zip(city_state_zip)
        
        return {
            'street': street,
            'city': parsed.get('city', ''),
            'state': parsed.get('state', ''),
            'zip_code': parsed.get('zip_code', '')
        }
    else:
        return {'street': address, 'city': '', 'state': '', 'zip_code': ''}

def parse_simple_address(address: str) -> dict:
    """Parse addresses without comma separators."""
    state_zip_parsed = parse_city_state_zip(address)
    
    remaining = address
    if state_zip_parsed.get('state'):
        remaining = remaining.replace(state_zip_parsed['state'], '').strip()
    if state_zip_parsed.get('zip_code'):
        remaining = remaining.replace(state_zip_parsed['zip_code'], '').strip()
    
    remaining = re.sub(r'\s+', ' ', remaining).strip()
    if remaining.endswith(','):
        remaining = remaining[:-1].strip()
    
    return {
        'street': remaining,
        'city': state_zip_parsed.get('city', ''),
        'state': state_zip_parsed.get('state', ''),
        'zip_code': state_zip_parsed.get('zip_code', '')
    }

def parse_city_state_zip(text: str) -> dict:
    """Parse city, state, and zip code from a string."""
    if not text:
        return {'city': '', 'state': '', 'zip_code': ''}
    
    state_pattern = r'\b([A-Z]{2})\s+(\d{5}(?:-\d{4})?)\b'
    match = re.search(state_pattern, text)
    
    if match:
        state = match.group(1)
        zip_code = match.group(2)
        
        city_part = text[:match.start()].strip()
        if city_part.endswith(','):
            city_part = city_part[:-1].strip()
        
        return {
            'city': city_part,
            'state': state,
            'zip_code': zip_code
        }
    
    state_zip_pattern = r'\b([A-Z]{2})\s+(\d{5}(?:-\d{4})?)\b'
    match = re.search(state_zip_pattern, text)
    
    if match:
        state = match.group(1)
        zip_code = match.group(2)
        
        city_part = text[:match.start()].strip()
        if city_part.endswith(','):
            city_part = city_part[:-1].strip()
        
        return {
            'city': city_part,
            'state': state,
            'zip_code': zip_code
        }
    
    return {
        'city': text.strip(),
        'state': '',
        'zip_code': ''
    }

chrome_options = Options()
# chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=chrome_options)

url = 'https://bizfileonline.sos.ca.gov/search/ucc'

for name in party_names:
    driver.get(url)
    wait = WebDriverWait(driver, 20)

    search_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div[1]/div/main/div/div[3]/div[1]/form/input')))
    search_input.clear()
    search_input.send_keys(name)

    adv_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="root"]/div/div[1]/div/main/div/div[3]/div[2]/button')))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", adv_btn)
    time.sleep(0.5)
    adv_btn.click()
    time.sleep(0.5)

    status_select = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="field-STATUS"]')))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", status_select)
    time.sleep(0.5)
    status_select.click()
    status_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="field-STATUS"]/option[2]')))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", status_option)
    time.sleep(0.5)
    status_option.click()

    start_date_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="field-date-FILING_DATEs"]')))
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%m/%d/%Y')
    start_date_input.clear()
    start_date_input.send_keys(seven_days_ago)

    time.sleep(3)

    search_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'advanced-search-button')))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", search_btn)
    time.sleep(0.5)
    search_btn.click()

    try:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div[1]/div/main/div[3]/table'))
        )
        time.sleep(1)
        table_rows = table.find_elements(By.TAG_NAME, 'tr')
        # Get main table headers
        main_headers = [th.text for th in table_rows[0].find_elements(By.TAG_NAME, 'th')]
        if len(header) == 1:
            header.extend(main_headers)
        # For each data row
        for row_idx, row in enumerate(table_rows[1:], start=1):
            cols = [col.text for col in row.find_elements(By.TAG_NAME, 'td')]
            if not cols:
                continue
            # Click the button in the first cell
            btn_xpath = f'//*[@id="root"]/div/div[1]/div/main/div[3]/table/tbody/tr[{row_idx}]/td[1]/div'
            try:
                btn = wait.until(EC.element_to_be_clickable((By.XPATH, btn_xpath)))
                # Scroll to make the button visible with some padding
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", btn)
                time.sleep(0.5)  # Small delay to ensure scrolling is complete
                btn.click()
                time.sleep(2)
                # Wait for sidebar table
                sidebar_table = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div[1]/div/main/div[5]/div/div[2]/div/div/table'))
                )
                sidebar_rows = sidebar_table.find_elements(By.TAG_NAME, 'tr')
                sidebar_data = {}
                for srow in sidebar_rows:
                    scells = srow.find_elements(By.TAG_NAME, 'td')
                    if len(scells) == 2:
                        key = scells[0].text.strip()
                        val = scells[1].text.strip()
                        sidebar_data[key] = val
                        sidebar_fields_set.add(key)
                # Close sidebar if needed (optional: add code if sidebar must be closed)
            except Exception as e:
                print(f"Sidebar not found for row {row_idx}: {e}")
                sidebar_data = {}
            # Merge row data
            row_dict = {'Party Name': name}
            for h, v in zip(main_headers, cols):
                row_dict[h] = v
            row_dict.update(sidebar_data)
            
            # Parse addresses if they exist
            if 'Debtor Address' in row_dict:
                debtor_parsed = parse_address(row_dict['Debtor Address'])
                row_dict['Debtor Street'] = debtor_parsed['street']
                row_dict['Debtor City'] = debtor_parsed['city']
                row_dict['Debtor State'] = debtor_parsed['state']
                row_dict['Debtor Zip'] = debtor_parsed['zip_code']
            
            if 'Secured Party Address' in row_dict:
                secured_parsed = parse_address(row_dict['Secured Party Address'])
                row_dict['Secured Party Street'] = secured_parsed['street']
                row_dict['Secured Party City'] = secured_parsed['city']
                row_dict['Secured Party State'] = secured_parsed['state']
                row_dict['Secured Party Zip'] = secured_parsed['zip_code']
            
            rows_data.append(row_dict)
        
    except Exception as e:
        print(f"No table found for {name}: {e}")
    time.sleep(10)

driver.quit()

# Write all data to CSV with dynamic headers
all_headers = header + sorted(sidebar_fields_set - set(header))

# Add address parsing columns to headers
address_columns = [
    'Debtor Street', 'Debtor City', 'Debtor State', 'Debtor Zip',
    'Secured Party Street', 'Secured Party City', 'Secured Party State', 'Secured Party Zip'
]

# Insert address columns after the original address columns
final_headers = []
for header_name in all_headers:
    final_headers.append(header_name)
    if header_name == 'Debtor Address':
        final_headers.extend(['Debtor Street', 'Debtor City', 'Debtor State', 'Debtor Zip'])
    elif header_name == 'Secured Party Address':
        final_headers.extend(['Secured Party Street', 'Secured Party City', 'Secured Party State', 'Secured Party Zip'])

with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=final_headers)
    writer.writeheader()
    for row in rows_data:
        writer.writerow(row)

print(f"Done. Results saved to {output_file}")
