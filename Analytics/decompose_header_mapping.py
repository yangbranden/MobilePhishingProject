import csv
import sys

def decompose_mapping(mapping_file, target_value, output_file):
    # Step 1: Read the hot mapping CSV and create a dictionary with the hot mapping for the specified header
    print("DEBUG: Starting step 1...")
    hot_mapping = {}
    with open(mapping_file, 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        for row in reader:
            # Hot mapping has entries in format:
            # Header,Mapping,Mapping Value
            header, mapping_value = row[0], int(row[2])
            # print(f"header: {header}")
            hot_mapping[header] = mapping_value
    print("DEBUG: Completed step 1. Starting step 2...")
    # print(hot_mapping)
    # Step 2: Decompose the combined mapping value
    decomposed_values = []
    for header, hot_value in hot_mapping.items():
        # print(f"Testing {target_header} = {header}")
        if target_value & hot_value:  # Check if the bit is set
            print(f"FOUND {header}")
            decomposed_values.append(header)
    # Step 3: Write output to CSV file
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Header'])
        for value in decomposed_values:
            writer.writerow([value])
    return decomposed_values

def main():
    sys.set_int_max_str_digits(0)
    
    # EDIT THESE TO SEE WHAT A VALUE CORRESPONDS TO
    header_value = 8498207885068273579033411304839498037273489883632510771191106211206456957773635883826600036243668570702229271779944016245545269402443315830552319660265397631101300333366291504507650048
    # The mapping file determines what subset we are looking for
    hot_mapping_file = "all_header_presence_mappings.csv" 
    # hot_mapping_file = "request_header_presence_mappings.csv" 
    # hot_mapping_file = "response_header_presence_mappings.csv" 
    output_file = "decomposed_results.csv"
    
    results = decompose_mapping(hot_mapping_file, header_value, output_file)
    print(f"Decomposed results saved to {output_file}")

if __name__ == "__main__":
    main()
