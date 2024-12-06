import requests
from bs4 import BeautifulSoup

# Define the URL
url = "https://rguhs.karnataka.gov.in/rguresult/"  # Replace with the actual URL from the Network tab

# Form data
data = {
    "reg_no": "21P2613",  # Replace with your registration number
    "semester": "PHAR6E - B.PHARM SEMESTER-V (RS6)",  # Replace with the actual dropdown value
}

# Headers (optional)
headers = {
    "User-Agent": "Mozilla/5.0",
    # Add other headers if needed, e.g., cookies
}

# Send POST or GET request
response = requests.post(url, data=data, headers=headers)

# Parse the response
if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    # Extract the result table or specific data
    result_table = soup.find("table")  # Adjust this selector
    print(result_table.text)
else:
    print(f"Failed to fetch results. Status code: {response.status_code}")