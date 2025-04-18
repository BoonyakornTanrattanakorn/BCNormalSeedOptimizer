import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import csv
import sys

class SlotContainer:
    """
    Container class for slot items, tracking the track name and associated items.
    """
    def __init__(self, track_name='X', item=None, track_switch_item=None):
        self.trackName = track_name
        self.item = item
        self.trackSwitchItem = track_switch_item
    
    def __repr__(self):
        if self.trackSwitchItem:
            return f"[{self.trackName}] {self.item} ({self.trackSwitchItem})"
        else:
            return f"[{self.trackName}] {self.item}"

class PathContainer:
    def __init__(self, item_list=[], reward_=0):
        self.itemList = item_list
        self.reward = reward_

class Tickets:
    def __init__(self, silver_ticket=0, lucky_ticket=0):
        self.silverTicket = silver_ticket
        self.luckyTicket = lucky_ticket     

    def __eq__(self, other):
        if not isinstance(other, Tickets):
            return False
        return (self.silverTicket, self.luckyTicket) == (other.silverTicket, other.luckyTicket)

    def __hash__(self):
        return hash((self.silverTicket, self.luckyTicket))

    def __repr__(self):
        return f"Tickets(silver_ticket={self.silverTicket}, lucky_ticket={self.luckyTicket})"

def getRewardDict() -> dict:
    """
    Loads item values from a CSV file where each row contains a count and an item name.
    
    The CSV file should have exactly two columns: count and item name.
    Each row contains one count-item pair.
    
    Returns:
        dict: A dictionary mapping item names (str) to their count values (int)
    
    Example CSV format:
        10,Rare Cat Ticket
        150,Cat Food
    """
    reward_dict = {}
    
    try:
        with open('itemValue.csv', mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                # Skip rows that don't have exactly 2 columns
                if len(row) != 2:
                    continue
                    
                count, item = row
                # Strip whitespace from item name and convert count to integer
                reward_dict[item.strip()] = int(count)
                
        return reward_dict
    except FileNotFoundError:
        print("Error: itemValue.csv file not found.")
        return {}
    except ValueError as e:
        print(f"Error parsing CSV: {e}")
        return {}

def getSlotData(url: str) -> dict:
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
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, "html.parser")
    
    trackNames, slotData = [], {}
    lastSlot = None
    
    for row in soup.find_all("tr"):
        cells = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
        
        if not cells or all(cell == '' for cell in cells):
            continue
            
        if cells[0] == '#':
            trackNames = cells[1:]  # Store header row (track names)
            # print(f"Track names: {trackNames}")
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
                
            # print(f"Found slot {lastSlot} with initial items: {slot_containers}")
                
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
            
            # print(f"Updated slot {lastSlot}, now contains: {slotData[lastSlot]}")
                
            lastSlot = None  # Reset after processing the slot's items
    
    
    # Final debug print of the entire slotData dictionary
    # print("\nFinal slotData dictionary:")
    for slot, items in slotData.items():
        items.sort(key=lambda container: container.trackName, reverse=True)
        print(f"{slot:>5}: {items}")
    
    return slotData

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
            container.trackSwitchItem = strip_track_switch_name(item)
            return
    
    # No container with this track name found, create a new one
    containers.append(SlotContainer(track_name=track_name, item=item))

def strip_track_switch_name(name):
    """
    Strips any prefix or suffix text from a track switch name, leaving just the core cat name.
    
    Args:
        name: The raw track switch item name
        
    Returns:
        Cleaned cat name (e.g., "Cat Energy" from various formats like 
        "Rare Cat Energy -> 7B" or "<- 6AR Axe Cat")
    """
    if not name:
        return None
        
    # Remove arrow notations (both -> and <-) and anything after/before them
    if "->" in name:
        name = name.split("->")[0].strip()
    if "<-" in name:
        name = name.split("<-")[1].strip()
    
    # Strip any slot references (like "6AR")
    name = re.sub(r'\d+[ABR]+\s+', '', name)
    
    return name

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

def getNextSlot(currentSlot: str, trackSwitch: bool) -> str:
    trackNumber = int(currentSlot[:-1])
    trackName = currentSlot[-1]
    
    if trackSwitch:
        if trackName == 'A':
            trackNumber += 1
            trackName = 'B'
        else: # trackName == 'B'
            trackNumber += 2
            trackName = 'A'
    else:
        trackNumber += 1
    return f"{trackNumber}{trackName}"

def getNextTickets(bannerName:str, tickets: Tickets) -> Tickets:
    next_tickets = Tickets(tickets.silverTicket, tickets.luckyTicket)
    if bannerName in ['Normal', 'Catseye']:
        if next_tickets.silverTicket == 0: return None
        next_tickets.silverTicket -= 1
    elif bannerName == 'Lucky':
        if next_tickets.luckyTicket == 0: return None
        next_tickets.luckyTicket -= 1
    return next_tickets

def optimizedPath(memorizedDict: dict, slotData: list, rewardDict: dict, tickets: Tickets, currentSlot: str, lastItem: str, depth: int) -> PathContainer:
    if currentSlot not in slotData or depth == 0:
        return PathContainer()
    if (currentSlot, tickets) in memorizedDict:
        return memorizedDict[(currentSlot, tickets)]

    global node_count
    node_count += 1
    
    bestPath = PathContainer()
    containers = slotData[currentSlot]

    for container in containers:
        item = container.item
        trackSwitch = False
        # track switch logic
        if item == lastItem and container.trackSwitchItem:
            item = container.trackSwitchItem
            trackSwitch = True

        nextTickets = getNextTickets(container.trackName, tickets)
        if nextTickets == None: continue

        nextSlot = getNextSlot(currentSlot, trackSwitch)
        nextPath = optimizedPath(memorizedDict, slotData, rewardDict, nextTickets, nextSlot, item, depth-1)

        if item not in rewardDict:
             raise KeyError(f"{item} is not in the itemValue.csv!")
        reward = rewardDict[item] + nextPath.reward
        if reward > bestPath.reward:
            bestPath.itemList = [(currentSlot, item)] + nextPath.itemList
            bestPath.reward = reward

    memorizedDict[(currentSlot, tickets)] = bestPath
    return bestPath
        
node_count = 0

if __name__ == "__main__":
    sys.setrecursionlimit(10000) 

    # config
    depth = 1000
    silverTicketCount = 1000
    luckyTicketCount = 1000

    # code
    slotData = getSlotData(f'https://ampuri.github.io/bc-normal-seed-tracking/?seed=355591313&banners=lt%2Cn&lastCat=Cat+Energy&selected=c%2C304823453%2Cn&rolls={depth+50}')
    rewardDict = getRewardDict()
    tickets = Tickets(silverTicketCount, luckyTicketCount)
    memorizedDict = dict()

    startTime = time.time()

    bestPath = optimizedPath(memorizedDict, slotData, rewardDict, tickets, '1A', '', depth)
 
    print(f"{'Track':<6} | {'Name'}")
    print("-" * 40)
    for track, name in bestPath.itemList:
        print(f"{track:<6} | {name}")

    print(f"node count: {node_count}")
    print(bestPath.reward)
    print(f"Total time: {round(time.time()-startTime, 2)} s!")
