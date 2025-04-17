import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class SlotContainer:
    """
    Container class for slot items, tracking the track name and associated items.
    """
    def __init__(self, track_name='X', item=None, dupe_item=None):
        self.trackName = track_name
        self.item = item
        self.dupeItem = dupe_item
    
    def __repr__(self):
        return f"SlotContainer(trackName='{self.trackName}', item={self.item}, dupeItem={self.dupeItem})"

def getSlotData(url: str) -> tuple[list, dict]:
    """
    Scrapes battle cats track data from the provided URL.
    
    Args:
        url: The URL of the webpage containing the track data
        
    Returns:
        A tuple containing:
        - Track names (header row)
        - Dictionary mapping slot positions (e.g. '1A') to lists of SlotContainer objects
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
   
    with webdriver.Chrome(options=options) as driver:
        driver.get(url)
        # Wait for content to load fully
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
    
    trackNames, slotData = [], {}
    lastSlot = None
    
    for row in soup.find_all("tr"):
        cells = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
        
        if not cells or all(cell == '' for cell in cells):
            continue
            
        if cells[0] == '#':
            trackNames = cells[1:]  # Store header row (track names)
            print(f"Track names: {trackNames}")
            continue
            
        if isSlot(cells[0]):
            lastSlot = cells[0]
            slot_containers = []
            
            # Store non-empty items from the same row as the slot (indexed by track)
            for i, item in enumerate(cells[1:], 0):
                if item:
                    # Associate items with track name (if we have enough track names)
                    track_name = trackNames[i] if i < len(trackNames) else "X"
                    add_item_to_containers(slot_containers, track_name, item)
            
            # Initialize the slot data
            if slot_containers:
                slotData[lastSlot] = slot_containers
            else:
                slotData[lastSlot] = []
                
            print(f"Found slot {lastSlot} with initial items: {slot_containers}")
                
        elif lastSlot:
            # For rows after a slot, process items
            if lastSlot not in slotData:
                slotData[lastSlot] = []
                
            # For rows after a slot, add items and associate with correct track
            for i, item in enumerate(cells, 0):
                if item:
                    # Associate items with track name (if we have enough track names)
                    track_name = trackNames[i] if i < len(trackNames) else "X"
                    add_item_to_containers(slotData[lastSlot], track_name, item)
            
            print(f"Updated slot {lastSlot}, now contains: {slotData[lastSlot]}")
                
            lastSlot = None  # Reset after processing the slot's items
    
    # Final debug print of the entire slotData dictionary
    print("\nFinal slotData dictionary:")
    for slot, items in slotData.items():
        print(f"{slot}: {items}")
    
    return trackNames, slotData

def add_item_to_containers(containers, track_name, item):
    """
    Adds an item to the appropriate container based on the track name.
    If a container with the same track name exists, adds to its dupeItem.
    Otherwise, creates a new container.
    
    Args:
        containers: List of SlotContainer objects
        track_name: The track name for this item
        item: The item to add
    """
    # Check if there's already a container with this track name
    for container in containers:
        if container.trackName == track_name:
            # Found a container with the same track name, add this item as a dupe
            container.dupeItem = item
            return
    
    # No container with this track name found, create a new one
    containers.append(SlotContainer(track_name=track_name, item=item))

def isSlot(text: str) -> bool:
    """
    Determines if the given text represents a slot (like '1A', '2A', etc.)
    
    Args:
        text: String to check
        
    Returns:
        True if text matches slot pattern, False otherwise
    """
    # Checks for patterns like '1A', '10A', '1B', etc.
    return bool(re.match(r'^\d+[AB]$', text))

getSlotData('https://ampuri.github.io/bc-normal-seed-tracking/?seed=355591313&banners=lt%2Cn&lastCat=Cat+Energy&selected=c%2C304823453%2Cn&rolls=100')