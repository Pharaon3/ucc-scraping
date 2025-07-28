import csv
import re

def final_parse_address(address: str) -> dict:
    """Final robust address parser that handles all edge cases."""
    if not address or address.strip() == '':
        return {'street': '', 'city': '', 'state': '', 'zip_code': ''}
    
    address = address.strip()
    
    # Handle PO Box addresses
    if address.upper().startswith('PO BOX') or address.upper().startswith('P.O. BOX'):
        return parse_po_box_address_final(address)
    
    # Handle addresses with "C/O" (Care Of)
    if 'C/O' in address.upper():
        return parse_care_of_address_final(address)
    
    # Handle addresses with multiple parts separated by commas
    if ',' in address:
        return final_parse_comma_address(address)
    
    # Handle simple addresses
    return final_parse_simple_address(address)

def parse_po_box_address_final(address: str) -> dict:
    """Parse PO Box addresses with improved logic."""
    po_match = re.search(r'PO\.?\s*BOX\s+(\d+)', address, re.IGNORECASE)
    if po_match:
        po_number = po_match.group(1)
        remaining = address.replace(po_match.group(0), '').strip()
        if remaining.startswith(','):
            remaining = remaining[1:].strip()
        
        city_state_zip = final_parse_state_zip(remaining)
        
        return {
            'street': f"PO BOX {po_number}",
            'city': city_state_zip.get('city', ''),
            'state': city_state_zip.get('state', ''),
            'zip_code': city_state_zip.get('zip_code', '')
        }
    
    return {'street': address, 'city': '', 'state': '', 'zip_code': ''}

def parse_care_of_address_final(address: str) -> dict:
    """Parse addresses with 'C/O' (Care Of) format."""
    parts = re.split(r'C/O', address, flags=re.IGNORECASE)
    if len(parts) >= 2:
        care_of = parts[0].strip()
        actual_address = parts[1].strip()
        
        parsed = final_parse_comma_address(actual_address)
        
        if parsed['street']:
            parsed['street'] = f"C/O {care_of}, {parsed['street']}"
        else:
            parsed['street'] = f"C/O {care_of}"
        
        return parsed
    
    return {'street': address, 'city': '', 'state': '', 'zip_code': ''}

def final_parse_comma_address(address: str) -> dict:
    """Final parsing for comma-separated addresses."""
    parts = [part.strip() for part in address.split(',')]
    
    if len(parts) >= 3:
        # Format: "street, city, state zip"
        street = parts[0]
        city = parts[1]
        state_zip_part = parts[2]
        
        state_zip_parsed = final_parse_state_zip(state_zip_part)
        
        return {
            'street': street,
            'city': city,
            'state': state_zip_parsed.get('state', ''),
            'zip_code': state_zip_parsed.get('zip_code', '')
        }
    elif len(parts) == 2:
        # Format: "street, city state zip" or "street, state zip"
        street = parts[0]
        city_state_zip = parts[1]
        
        parsed = final_parse_state_zip(city_state_zip)
        
        return {
            'street': street,
            'city': parsed.get('city', ''),
            'state': parsed.get('state', ''),
            'zip_code': parsed.get('zip_code', '')
        }
    else:
        return {'street': address, 'city': '', 'state': '', 'zip_code': ''}

def final_parse_simple_address(address: str) -> dict:
    """Final parsing for addresses without commas."""
    state_zip_parsed = final_parse_state_zip(address)
    
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

def final_parse_state_zip(text: str) -> dict:
    """Final robust parsing of city, state, and zip code."""
    if not text:
        return {'city': '', 'state': '', 'zip_code': ''}
    
    # Clean the text
    text = text.strip()
    
    # Enhanced patterns to handle more formats
    patterns = [
        # Standard: "CITY STATE ZIP"
        r'^(.+?)\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$',
        # Just state and zip: "STATE ZIP"
        r'^([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$',
        # City with extra spaces: "CITY  STATE   ZIP"
        r'^(.+?)\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 3:
                city = match.group(1).strip()
                state = match.group(2)
                zip_code = match.group(3)
                return {'city': city, 'state': state, 'zip_code': zip_code}
            elif len(match.groups()) == 2:
                state = match.group(1)
                zip_code = match.group(2)
                return {'city': '', 'state': state, 'zip_code': zip_code}
    
    # If no pattern matches, try to extract just state and zip from anywhere in the text
    state_zip_match = re.search(r'\b([A-Z]{2})\s+(\d{5}(?:-\d{4})?)\b', text)
    if state_zip_match:
        state = state_zip_match.group(1)
        zip_code = state_zip_match.group(2)
        city_part = text[:state_zip_match.start()].strip()
        if city_part.endswith(','):
            city_part = city_part[:-1].strip()
        return {'city': city_part, 'state': state, 'zip_code': zip_code}
    
    # Try to find just a state abbreviation
    state_match = re.search(r'\b([A-Z]{2})\b', text)
    if state_match:
        state = state_match.group(1)
        # Remove the state from text to get city
        city_part = text.replace(state, '').strip()
        if city_part.endswith(','):
            city_part = city_part[:-1].strip()
        return {'city': city_part, 'state': state, 'zip_code': ''}
    
    # If still no match, return the whole text as city
    return {'city': text.strip(), 'state': '', 'zip_code': ''}

def process_csv_final(input_file: str, output_file: str):
    """Process the CSV file with the final address parser."""
    
    rows = []
    with open(input_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        original_headers = reader.fieldnames
        
        new_headers = []
        for header in original_headers:
            new_headers.append(header)
            if header == 'Debtor Address':
                new_headers.extend(['Debtor Street', 'Debtor City', 'Debtor State', 'Debtor Zip'])
            elif header == 'Secured Party Address':
                new_headers.extend(['Secured Party Street', 'Secured Party City', 'Secured Party State', 'Secured Party Zip'])
        
        for row in reader:
            new_row = row.copy()
            
            if 'Debtor Address' in row:
                debtor_parsed = final_parse_address(row['Debtor Address'])
                new_row['Debtor Street'] = debtor_parsed['street']
                new_row['Debtor City'] = debtor_parsed['city']
                new_row['Debtor State'] = debtor_parsed['state']
                new_row['Debtor Zip'] = debtor_parsed['zip_code']
            
            if 'Secured Party Address' in row:
                secured_parsed = final_parse_address(row['Secured Party Address'])
                new_row['Secured Party Street'] = secured_parsed['street']
                new_row['Secured Party City'] = secured_parsed['city']
                new_row['Secured Party State'] = secured_parsed['state']
                new_row['Secured Party Zip'] = secured_parsed['zip_code']
            
            rows.append(new_row)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=new_headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    
    print(f"Processed {len(rows)} rows with final parser")
    print(f"Original file: {input_file}")
    print(f"Output file: {output_file}")

if __name__ == "__main__":
    input_file = "ucc_results.csv"
    output_file = "ucc_results_parsed_final.csv"
    
    process_csv_final(input_file, output_file) 