import csv
import sys

def decompose_mapping(mapping_file, target_header, target_value, output_file):
    # Step 1: Read the hot mapping CSV and create a dictionary with the hot mapping for the specified header
    print("DEBUG: Starting step 1...")
    hot_mapping = {}
    with open(mapping_file, 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        for row in reader:
            # Hot mapping has entries in format:
            # Header,Header Value,Mapping,Mapping Value
            header, value, mapping_value = row[0], row[1], int(row[3])
            # print(f"header: {header}")
            if header != target_header:
                continue
            hot_mapping[value] = mapping_value
    print("DEBUG: Completed step 1. Starting step 2...")
    # print(hot_mapping)
    # Step 2: Decompose the combined mapping value
    decomposed_values = []
    for header_value, hot_value in hot_mapping.items():
        # print(f"Testing {target_header} = {header_value}")
        if target_value & hot_value:  # Check if the bit is set
            print(f"FOUND {target_header} = {header_value}")
            decomposed_values.append(header_value)
    # Step 3: Write output to CSV file
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([target_header])
        for value in decomposed_values:
            writer.writerow([value])
    return decomposed_values

def main():
    sys.set_int_max_str_digits(0)
    
    # EDIT THESE TO SEE WHAT A VALUE CORRESPONDS TO
    target_header = 'Host'
    header_value = 3731581000814441671924614274482394021365783314243111167506086308095339790336
    
    hot_mapping_file = "90percent_header_data_mappings.csv"
    output_file = "decomposed_results.csv"
    
    results = decompose_mapping(hot_mapping_file, target_header, header_value, output_file)
    print(f"Decomposed results saved to {output_file}")

if __name__ == "__main__":
    main()
