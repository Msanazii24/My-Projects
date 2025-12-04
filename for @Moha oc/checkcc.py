import re

print("Enter your lines (type 'END' to finish):")

lines = []
while True:
    line = input()
    if line.strip().upper() == 'END':
        break
    lines.append(line)

# Join all lines into one string
data = '\n'.join(lines)

# Extract card data pattern
matches = re.findall(r'\b\d{13,16}\|\d{1,2}\|\d{4}\|\d{3,4}\b', data)

# Print each match on a new line
print("\nExtracted card data:")
print('\n'.join(matches))
