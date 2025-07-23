import csv

input_file = 'combined_al_output.csv'
output_file = 'combined_al_output_with_official.csv'

with open(input_file, newline='', encoding='utf-8') as infile, \
     open(output_file, 'w', newline='', encoding='utf-8') as outfile:
    reader = csv.DictReader(infile)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        if 'citibank' in row.get('secured_party_name', '').strip().lower():
            row['official_designation'] = row['secured_party_name']
            row['official_address'] = row.get('secured_party_address', '')
        writer.writerow(row)

print(f"Updated file written to {output_file}")
