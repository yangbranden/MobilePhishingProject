import pandas as pd

def get_reasoning_statistics(csv_file):
    try:
        # Read the CSV file
        data = pd.read_csv(csv_file)

        # Check if the column 'reasoning' exists
        if 'reasoning' not in data.columns:
            print("Error: Column 'reasoning' not found in the CSV file.")
            return

        # Count the occurrences of each value in the 'reasoning' column
        reasoning_counts = data['reasoning'].value_counts()

        # Print the statistics
        print("Statistics for 'reasoning' column:")
        for value, count in reasoning_counts.items():
            print(f"{value}: {count}")

    except FileNotFoundError:
        print("Error: The specified file does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

print("### Batch Data Statistics ###")
get_reasoning_statistics('batch_data_1_17_2025.csv')
print()
print("### Targeted Data Statistics ###")
get_reasoning_statistics('targeted_data_1_17_2025.csv')
print()