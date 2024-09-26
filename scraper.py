import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import urllib3
import logging

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def scrape_race_data():
    base_url = "https://www.livetiming.pedalcarracing.info/"
    url = urljoin(base_url, "timing-full.php")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        logger.debug(f"Attempting to fetch data from {url}")
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        logger.debug(f"Successfully fetched data. Status code: {response.status_code}")
        logger.debug(f"Response content: {response.text[:500]}...")  # Log first 500 characters of the response
    except requests.RequestException as e:
        logger.error(f"Error fetching the webpage: {e}")
        if isinstance(e, requests.exceptions.SSLError):
            logger.error(f"SSL Error details: {str(e)}")
        return None, None, None

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')

    if not table:
        logger.error("No table found on the page")
        return None, None, None

    # Extract table data manually
    headers = [th.text.strip() for th in table.find_all('th')]
    rows = []
    for tr in table.find_all('tr')[1:]:  # Skip header row
        row = [td.text.strip() for td in tr.find_all('td')]
        rows.append(row)

    # Keep the first column as the 'Position' column
    headers = ['Position'] + headers[1:]
    
    logger.debug(f"Updated table headers: {headers}")
    logger.debug(f"First row of updated data: {rows[0] if rows else 'No data'}")

    # Find the index of the car number column (now the third column after keeping Position)
    car_column_index = 2
    name_column_index = 3  # Assuming the name column is the fourth column (index 3)

    df = pd.DataFrame(rows, columns=headers)
    
    logger.debug(f"DataFrame columns: {df.columns}")
    logger.debug(f"First few rows of the DataFrame:\n{df.head()}")
    logger.debug(f"Raw DataFrame:\n{df}")
    
    lap_times = {}
    positions = {}
    
    for row in rows:
        logger.debug(f"Processing row: {row}")
        logger.debug(f"Car number (before strip): '{row[car_column_index]}', After strip: '{row[car_column_index].strip()}'")
        
        car_number = row[car_column_index].strip()
        if not car_number.isdigit():
            logger.debug(f"Skipping non-numeric car number: {car_number}")
            continue

        car_number = int(car_number)
        
        # Check if 'Laps' column exists, if not, set lap_count to 0
        laps_column_index = headers.index('Laps') if 'Laps' in headers else None
        lap_count = int(row[laps_column_index]) if laps_column_index is not None else 0
        
        # Check if 'Last' column exists, if not, set last_lap_time to '0:00.000'
        last_column_index = headers.index('Last') if 'Last' in headers else None
        last_lap_time = row[last_column_index] if last_column_index is not None else '0:00.000'

        # Get the position
        position = int(row[0])

        logger.debug(f"Car number: {car_number}, Lap count: {lap_count}, Last lap time: {last_lap_time}, Position: {position}")

        # Convert last_lap_time to seconds
        time_parts = last_lap_time.split(':')
        seconds = float(time_parts[-1])
        if len(time_parts) > 1:
            seconds += int(time_parts[-2]) * 60
        
        lap_times[car_number] = (lap_count, seconds)
        positions[car_number] = position
    
    logger.debug(f"Processed lap times and positions for {len(lap_times)} cars")

    # Filter out non-numeric values and ensure we're only using the third column
    car_numbers = []
    for row in rows:
        if len(row) > car_column_index:
            car_number = row[car_column_index].strip()
            if car_number.isdigit():
                car_numbers.append(int(car_number))

    # Remove duplicate car numbers and sort them
    car_numbers = sorted(list(set(car_numbers)))

    # Add more detailed logging
    logger.debug(f"All values in the car number column: {[row[car_column_index] for row in rows if len(row) > car_column_index]}")
    logger.debug(f"Final filtered car numbers: {car_numbers}")

    return lap_times, positions, df, car_numbers
