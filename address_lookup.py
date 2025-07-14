import csv
import requests
import time
import urllib.parse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def get_zip_code(address):
    """
    Get ZIP code for an address using a free geocoding service.
    """
    try:
        if not address or "WV" not in address:
            return ""
        
        # Use a free geocoding service to get ZIP code
        # Option 1: US Census Bureau Geocoding API
        api_url = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"
        params = {
            'address': address,
            'benchmark': 'Public_AR_Current',
            'vintage': 'Current_Current',
            'format': 'json'
        }
        
        response = requests.get(api_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'result' in data and 'addressMatches' in data['result']:
                matches = data['result']['addressMatches']
                
                if matches:
                    match = matches[0]
                    address_components = match.get('addressComponents', {})
                    
                    # Extract ZIP code
                    if 'zip' in address_components:
                        zip_code = address_components['zip']
                        print(f"Found ZIP code for '{address}': {zip_code}")
                        return zip_code
        
        # Option 2: OpenStreetMap Nominatim (fallback)
        encoded_address = urllib.parse.quote(address)
        nominatim_url = f"https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        
        response = requests.get(nominatim_url, params=params, headers={
            'User-Agent': 'UCC_Address_Lookup/1.0'
        })
        
        if response.status_code == 200:
            data = response.json()
            if data:
                result = data[0]
                if 'address' in result:
                    addr = result['address']
                    if 'postcode' in addr:
                        zip_code = addr['postcode']
                        print(f"Found ZIP code for '{address}': {zip_code}")
                        return zip_code
        
        print(f"No ZIP code found for address: {address}")
        return ""
        
    except Exception as e:
        print(f"Error getting ZIP code for {address}: {e}")
        return ""

def setup_driver():
    """Set up Chrome driver for web scraping."""
    options = Options()
    # options.add_argument('--headless')  # Run in background
    options.add_argument('--disable-gpu')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def lookup_address_naics(driver, name, entity_type):
    """
    Look up address for a given name using NAICS Company Lookup Tool.
    """
    try:
        # Clean the name for search
        search_name = name.strip()
        if not search_name:
            return ""
        
        print(f"Looking up address for {entity_type}: {search_name}")
        
        # Navigate to NAICS lookup tool
        driver.get("https://www.naics.com/company-lookup-tool/")
        time.sleep(2)
        
        # Find and fill the company name field
        try:
            
            # Click the tab
            tab_element = driver.find_element(By.XPATH, '//*[@id="tablabel2"]')
            tab_element.click()
            time.sleep(1)
            
            # Type company name
            company_field = driver.find_element(By.XPATH, '//*[@id="company2"]')
            company_field.clear()
            company_field.send_keys(search_name)
            time.sleep(1)
            
            # Select WV option from state dropdown
            wv_option_element = driver.find_element(By.XPATH, '//*[@id="qstate"]/option[49]')
            wv_option_element.click()
            time.sleep(1)
            
            # Click search button
            search_button_element = driver.find_element(By.XPATH, '//*[@id="nameAddressLU"]/div[3]/p/input[2]')
            search_button_element.click()
            time.sleep(3)
            
            # Find street, city, state from results
            try:
                # Start with first result row (tr[2])
                row_index = 2
                max_rows = 10  # Limit to prevent infinite loop
                first_address = None  # Store first address found
                
                while row_index <= max_rows:
                    try:
                        # Get street, city, state from current row
                        street_element = driver.find_element(By.XPATH, f'//*[@id="searchResultsTable"]/tbody/tr[{row_index}]/td[3]')
                        city_element = driver.find_element(By.XPATH, f'//*[@id="searchResultsTable"]/tbody/tr[{row_index}]/td[4]')
                        state_element = driver.find_element(By.XPATH, f'//*[@id="searchResultsTable"]/tbody/tr[{row_index}]/td[5]')
                        
                        street = street_element.text.strip()
                        city = city_element.text.strip()
                        state = state_element.text.strip()
                        
                        # Build address for this row
                        address_parts = []
                        if street:
                            address_parts.append(street)
                        if city:
                            address_parts.append(city)
                        if state:
                            address_parts.append(state)
                        
                        current_address = ', '.join(address_parts)
                        
                        # Store first address found
                        if first_address is None:
                            first_address = current_address
                        
                        # Check if state is WV
                        if state == "WV":
                            # Get ZIP code for this address
                            zip_code = get_zip_code(current_address)
                            if zip_code:
                                current_address = f"{current_address}, {zip_code}"
                            
                            print(f"Found WV address for {entity_type} '{name}': {current_address}")
                            return current_address
                        else:
                            # State is not WV, move to next row
                            print(f"Row {row_index}: State is {state}, not WV. Moving to next row.")
                            row_index += 1
                            
                    except Exception as e:
                        # No more rows or element not found
                        print(f"No more results or error at row {row_index}: {e}")
                        break
                
                # If no WV address found, return first address with ZIP code
                if first_address:
                    # Get ZIP code for first address
                    zip_code = get_zip_code(first_address)
                    if zip_code:
                        first_address = f"{first_address}, {zip_code}"
                    
                    print(f"No WV address found for {entity_type} '{name}'. Using first result: {first_address}")
                    return first_address
                else:
                    print(f"No address found for {entity_type}: {name}")
                    return ""
                
            except Exception as e:
                print(f"Error extracting address: {e}")
                return ""
            
        except Exception as e:
            print(f"Error filling form for {name}: {e}")
            return ""
        
    except Exception as e:
        print(f"Error looking up address for {name}: {e}")
        return ""

def process_ucc_csv(input_csv, output_csv):
    """
    Read the UCC CSV, look up addresses using NAICS, and create a new CSV with address columns.
    """
    rows = []
    
    # Read the original CSV first to get all data
    with open(input_csv, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Get the header row
        
        # Add address columns to header
        new_header = header + ['Debtor Address', 'Secured Party Address']
        rows.append(new_header)
        
        # Store all data rows for processing
        data_rows = list(reader)
    
    # Process each data row with a new browser for each
    for i, row in enumerate(data_rows):
        if len(row) >= 5:  # Ensure we have enough columns
            filing_number = row[0]
            debtor = row[3]  # Assuming Debtor is in column 3
            secured_party = row[4]  # Assuming Secured Party is in column 4
            
            print(f"Processing filing {i+1}/{len(data_rows)}: {filing_number}")
            
            # Look up debtor address with new browser
            print(f"Looking up debtor address for: {debtor}")
            debtor_address = ""
            try:
                driver = setup_driver()
                debtor_address = lookup_address_naics(driver, debtor, "debtor")
            except Exception as e:
                print(f"Error looking up debtor address: {e}")
            finally:
                driver.quit()
            
            # Look up secured party address with new browser
            print(f"Looking up secured party address for: {secured_party}")
            secured_party_address = ""
            try:
                driver = setup_driver()
                secured_party_address = lookup_address_naics(driver, secured_party, "secured_party")
            except Exception as e:
                print(f"Error looking up secured party address: {e}")
            finally:
                driver.quit()
            
            # Add addresses to the row
            new_row = row + [debtor_address, secured_party_address]
            rows.append(new_row)
            
            # Add delay between processing
            time.sleep(1)
    
    # Write the new CSV with addresses
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    
    print(f"Address lookup completed. Results saved to {output_csv}")

if __name__ == "__main__":
    # Get the most recent UCC CSV file
    current_date = datetime.now().strftime("%Y-%m-%d")
    input_csv = f"WV_UCC1_{current_date}.csv"
    output_csv = f"WV_UCC1_with_addresses_{current_date}.csv"
    
    try:
        process_ucc_csv(input_csv, output_csv)
    except FileNotFoundError:
        print(f"Input file {input_csv} not found. Please run the main scraping script first.")
    except Exception as e:
        print(f"Error processing CSV: {e}") 