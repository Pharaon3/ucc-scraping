import csv
import glob
import os
import re
from datetime import datetime

# Output columns as in the sample, plus secured party address fields
OUTPUT_COLUMNS = [
    'filing_number', 'debtor_name', 'Debtor_Street', 'Debtor_City', 'Debtor_State', 'Debtor_Zip',
    'filing_date', 'secured_party_name', 'secured_party_address', 'secured_party_city', 'secured_party_state', 'secured_party_zip',
    'lapse_date', 'official_designation', 'official_name', 'official_address', 'Processed'
]

# Helper to parse address into street, city, state, zip
ADDRESS_REGEX = re.compile(r"^(.*?),\s*([A-Za-z .'-]+),\s*([A-Z]{2})\s+(\d{5})(?:-(\d{4}))?$")
SIMPLE_CITY_STATE_ZIP = re.compile(r"^([A-Za-z .'-]+),\s*([A-Z]{2})\s+(\d{5})(?:-(\d{4}))?$")

# New: combine address parts if needed, then parse

def parse_address(address1, address2=None):
    # Combine if two parts are given
    if address2:
        address = f"{address1}, {address2}".replace('\n', ' ').strip()
    else:
        address = address1.replace('\n', ' ').strip()
    # Try full match: street, city, state, zip
    match = ADDRESS_REGEX.match(address)
    if match:
        street = match.group(1).strip()
        city = match.group(2).strip()
        state = match.group(3).strip()
        zip_code = match.group(4).strip()
        # Only use the first 5 digits
        return street, city, state, zip_code
    # Try just city, state, zip (no street)
    match2 = SIMPLE_CITY_STATE_ZIP.match(address)
    if match2:
        zip_code = match2.group(3).strip()
        return '', match2.group(1).strip(), match2.group(2).strip(), zip_code
    # Fallback: put everything in street
    return address, '', '', ''

def extract_blocks(lines):
    blocks = []
    block = []
    for line in lines:
        if line.strip().startswith('----Filing Type----'):
            if block:
                blocks.append(block)
                block = []
        block.append(line)
    if block:
        blocks.append(block)
    return blocks

def parse_block(block):
    filing_number = filing_date = lapse_date = ''
    debtor_names = []
    debtor_addresses = []
    secured_party_names = []
    secured_party_addresses = []
    section = None
    i = 0
    while i < len(block):
        line = block[i].strip()
        if not line or line == '""' or line.startswith('Back') or line.startswith('New Search'):
            i += 1
            continue
        if line.startswith('----Filing Type----'):
            i += 1
            continue
        if line.startswith('Business') or line.startswith('Finance Statement'):
            parts = [x.strip() for x in line.split(',')]
            if len(parts) >= 6:
                filing_date = parts[1]
                lapse_date = parts[3]
                filing_number = parts[5]
            i += 1
            continue
        if line.startswith('Debtor(s)'):
            section = 'debtor'
            i += 1
            continue
        if line.startswith('Secured'):
            section = 'secured'
            i += 1
            continue
        if section == 'debtor':
            # Debtor name and address may be on two consecutive lines
            name = line
            address1 = ''
            address2 = None
            if i+1 < len(block):
                next_line = block[i+1].strip()
                if next_line and not next_line.startswith('Secured') and not next_line.startswith('Debtor'):
                    address1 = next_line
                    i += 1
                    # Check for a second address line (city/state/zip)
                    if i+1 < len(block):
                        next2 = block[i+1].strip()
                        if SIMPLE_CITY_STATE_ZIP.match(next2):
                            address2 = next2
                            i += 1
            debtor_names.append(name.strip())
            debtor_addresses.append((address1.strip(), address2.strip() if address2 else None))
            i += 1
            continue
        if section == 'secured':
            # Secured party name and address may be on two consecutive lines
            name = line
            address1 = ''
            address2 = None
            if i+1 < len(block):
                next_line = block[i+1].strip()
                if next_line and not next_line.startswith('Secured') and not next_line.startswith('Debtor'):
                    address1 = next_line
                    i += 1
                    # Check for a second address line (city/state/zip)
                    if i+1 < len(block):
                        next2 = block[i+1].strip()
                        if SIMPLE_CITY_STATE_ZIP.match(next2):
                            address2 = next2
                            i += 1
            secured_party_names.append(name.strip())
            secured_party_addresses.append((address1.strip(), address2.strip() if address2 else None))
            i += 1
            continue
        i += 1
    # Combine all debtor/secured party pairs
    rows = []
    for dname, daddr_tuple in zip(debtor_names, debtor_addresses):
        d_street, d_city, d_state, d_zip = parse_address(*daddr_tuple)
        for sname, saddr_tuple in zip(secured_party_names, secured_party_addresses):
            s_street, s_city, s_state, s_zip = parse_address(*saddr_tuple)
            row = {
                'filing_number': filing_number,
                'debtor_name': dname,
                'Debtor_Street': d_street,
                'Debtor_City': d_city,
                'Debtor_State': d_state,
                'Debtor_Zip': d_zip,
                'filing_date': filing_date,
                'secured_party_name': sname,
                'secured_party_address': s_street,
                'secured_party_city': s_city,
                'secured_party_state': s_state,
                'secured_party_zip': s_zip,
                'lapse_date': lapse_date,
                'official_designation': '',
                'official_name': '',
                'official_address': '',
                'Processed': datetime.now().strftime('%m/%d/%Y'),
            }
            rows.append(row)
    return rows

def main():
    all_rows = []
    for fname in glob.glob('al_*.csv'):
        with open(fname, encoding='utf-8') as f:
            # Remove all double quotes from each line before further processing
            lines = [line.replace('"', '') for line in f.readlines()]
        blocks = extract_blocks(lines)
        for block in blocks:
            rows = parse_block(block)
            all_rows.extend(rows)
    # Remove duplicates
    unique_rows = []
    seen = set()
    for row in all_rows:
        # Remove any extraneous quotes from all output fields
        for k, v in row.items():
            if isinstance(v, str):
                row[k] = v.replace('"', '').strip()
        row_tuple = tuple(row.get(col, '') for col in OUTPUT_COLUMNS)
        if row_tuple not in seen:
            seen.add(row_tuple)
            unique_rows.append(row)
    # Write output
    with open('combined_al_output.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in unique_rows:
            writer.writerow(row)
    print(f'Wrote {len(unique_rows)} unique records to combined_al_output.csv')

if __name__ == '__main__':
    main() 