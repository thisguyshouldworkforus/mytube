#!/opt/projects/mytube/venv/bin/python3

import subprocess

def generate_requirements_file():
    # Run the 'pip list' command and capture the output
    result = subprocess.run(['pip', 'list'], stdout=subprocess.PIPE, text=True)
    
    # Split the output into lines
    lines = result.stdout.splitlines()
    
    # Skip the header lines
    package_lines = lines[2:]
    
    # Create the requirements.txt content
    requirements = []
    for line in package_lines:
        parts = line.split()
        if len(parts) == 2:
            package, version = parts
            requirements.append(f"{package}>={version}")
    
    # Write the requirements to a file
    with open('requirements.txt', 'w') as f:
        f.write('\n'.join(requirements))

    print("requirements.txt file has been generated.")

if __name__ == "__main__":
    generate_requirements_file()
