import re

# Input and output file paths
input_file = "1000x_drop.txt"   # your source file
output_file = "cleaned.txt"     # the result file

# Regex pattern for lines like 1234567890123456|02|25|123
pattern = re.compile(r"^\d{8,}\|\d{2}\|\d{2}\|\d{3}$")

# Read and filter lines
with open(input_file, "r") as infile:
    lines = infile.readlines()

matches = [line.strip() for line in lines if pattern.match(line.strip())]

# Write results to a new file
with open(output_file, "w") as outfile:
    outfile.write("\n".join(matches))

print(f"✅ Done! Extracted {len(matches)} matching lines into '{output_file}'.")
