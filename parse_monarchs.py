import requests
from bs4 import BeautifulSoup
import re
import plotly.graph_objects as go

# URL of the Wikipedia page
url = "https://en.wikipedia.org/wiki/List_of_Chinese_monarchs"

# Send a request to fetch the HTML content
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Function to extract monarchs' personal names, reign, and starting year from a table
def extract_monarchs(table, dynasty_name):
    monarchs = []
    rows = table.find_all("tr")
    
    for row in rows:
        cells = row.find_all(["td", "th"])
        if len(cells) == 1 and cells[0].has_attr('colspan'):
            # This row contains the dynasty name
            dynasty_name_match = re.search(r'[A-Za-z ]+', cells[0].text.strip())
            if dynasty_name_match:
                dynasty_name = dynasty_name_match.group(0)
        else:
            if dynasty_name == "":
                continue

            headers = table.find_all("th")
            personal_name_idx = -1
            reign_idx = -1
            
            # Identify the column index for 'Personal name' and 'Reign'
            for idx, header in enumerate(headers):
                if 'Personal name' in header.text:
                    personal_name_idx = idx
                elif 'Reign' in header.text:
                    reign_idx = idx

            if personal_name_idx == -1 or reign_idx == -1:
                continue

            cell_data = []
            for cell in cells:
                cell_text = cell.get_text(strip=True)
                colspan = int(cell.get("colspan", 1))
                for _ in range(colspan):
                    cell_data.append(cell_text)

            if len(cell_data) > max(personal_name_idx, reign_idx):
                personal_name = cell_data[personal_name_idx]
                if re.search(r'[\u4e00-\u9fff]+', personal_name):
                    reign = cell_data[reign_idx]
                    start_year = extract_start_year(reign)
                    monarchs.append({"Personal name": personal_name, "Reign": reign, "Start Year": start_year, "Dynasty": dynasty_name})
    
    return monarchs

# Function to extract the start year from the reign string
def extract_start_year(reign):
    # Extract the first year found in the string
    match = re.search(r'(\d+\s+[A-Za-z]+\s+\d+)', reign)
    if match:
        date_str = match.group(0)
        try:
            # Use dateutil.parser to parse the date string
            year_match = re.search(r'\d{1,4}$', date_str)
            if year_match:
                year = int(year_match.group(0))
                return -year if 'BC' in reign else year
        except ValueError:
            # If parsing fails, extract the year directly
            year = int(re.search(r'\d{1,4}', date_str).group(0))
            return -year if 'BC' in reign else year
    else:
        # If parsing fails, extract the year directly
        m = re.search(r'\d{1,4}', reign)
        if m:
            year = int(m.group(0))
            return -year if 'BC' in reign else year
    return None

# Extract all tables
tables = soup.find_all("table", {"class": "wikitable"})

# Parse each table and extract personal names, reigns, and start years
'''
all_monarchs = []
for table in tables:
    monarchs = extract_monarchs(table)
    all_monarchs.extend(monarchs)
'''
all_monarchs = []
for table in tables:
    caption = table.find("caption")
    if caption:
        dynasty_name = re.search(r'[A-Za-z ]+', caption.text.strip())
        if dynasty_name:
            dynasty_name = dynasty_name.group(0)
            monarchs = extract_monarchs(table, dynasty_name)
            all_monarchs.extend(monarchs)

# Display the extracted personal names, reigns, and start years
for monarch in all_monarchs:
    print(monarch)















# URL of the Wikipedia page
url = "https://en.wikipedia.org/wiki/Dynasties_of_China"

# Send a request to fetch the HTML content
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Function to extract major dynasties from the table
def extract_major_dynasties(soup):
    dynasties = []
    table = soup.find("table", {"class": "wikitable"})
    rows = table.find_all("tr")
    for row in rows[1:]:  # Skip the header row
        cols = row.find_all("td")
        if len(cols) >= 2:
            name = re.search(r'[\u4e00-\u9fff]+', cols[1].text.strip()).group(0)
            e_name = re.search(r'[A-Za-z ]+', cols[1].text.strip()).group(0)
            print(f'e-name: {e_name}')
            year = cols[5].text.strip()
            dynasties.append({"name": name, "year": year, "e-name": e_name})
    return dynasties

# Extract major dynasties
major_dynasties = extract_major_dynasties(soup)

# Function to convert year period to start and end years
def parse_year(year):
    try:
        parts = year.split("–")
        # print(parts)
        start = int(re.search(r'(\d+)', parts[0]).group(0)) if parts else 0
        end = int(re.search(r'(\d+)', parts[1]).group(0)) if parts else 0
        # print(f'{start}, {end}')
        return -start if "BC" in year else start, end if "AD" in year else -end
    except:
        return None, None

# Parse the dynasties with years
parsed_dynasties = []
for dynasty in major_dynasties:
    start, end = parse_year(dynasty["year"])
    if start and end:
        parsed_dynasties.append({
            "name": dynasty["name"],
            "e-name": dynasty["e-name"],
            "start": start,
            "end": end
        })


# Combine traces
# print(parsed_dynasties)

# Define y positions to avoid overlap and match the visual appearance

# Create traces for Chinese dynasties with boxes
scaling = 1
dynasty_traces = []
y_pos = len(parsed_dynasties) * scaling
y_positions = {}
for dynasty in parsed_dynasties:
    y_pos = y_pos - scaling;#y_positions.get(dynasty["name"], -20)  # default to -20 if event not found
    y_positions[dynasty["name"]] = y_pos
    dynasty_traces.append(go.Scatter(
        x=[dynasty["start"], dynasty["end"], dynasty["end"], dynasty["start"], dynasty["start"]],
        y=[y_pos + 0.3, y_pos + 0.3, y_pos - 0.3, y_pos - 0.3, y_pos + 0.3],
        mode='lines+text',
        fill='toself',
        text=[dynasty["name"], '', '', '', dynasty["name"]],
        textposition='middle center',
        fillcolor='rgba(100, 100, 255, 0.5)',
        line=dict(width=2, color='rgba(0, 0, 0, 1)'),
        name=dynasty["name"]
    ))

# print(dynasty_traces)

# Assign monarchs to the correct dynasty based on start year
dynasty_monarchs = {dynasty['name']: [] for dynasty in parsed_dynasties}
for monarch in all_monarchs:
    for dynasty in parsed_dynasties:
        if dynasty["e-name"].strip().casefold() == monarch["Dynasty"].strip().casefold(): # or dynasty['start'] <= monarch['Start Year'] <= dynasty['end']:
            dynasty_monarchs[dynasty['name']].append(monarch)
            break

# Create traces for monarchs
monarch_traces = []
for dynasty, monarchs in dynasty_monarchs.items():
    for monarch in monarchs:
        monarch_traces.append(go.Scatter(
            x=[monarch["Start Year"]],
            y=[y_positions[dynasty]],
            mode='markers+text',
            text=[monarch["Personal name"]],
            textposition='top center',
            marker=dict(size=6, color='red'),
            name=monarch["Personal name"]
        ))

# Combine traces
traces_image = dynasty_traces + monarch_traces

# Create the layout
layout_image = go.Layout(
    title='Timeline of Major Chinese Dynasties',
    xaxis=dict(title='Years', range=[-2100, 2025], dtick=500),
    yaxis=dict(title='', tickvals=list(y_positions.values()), ticktext=list(y_positions.keys())),#, range=[y_positions[], 31]),
    showlegend=False
)

# Create the figure
fig_image = go.Figure(data=traces_image, layout=layout_image)

# Save the plot to an HTML file
fig_image.write_html("Timeline_of_Major_Chinese_Dynasties.html")