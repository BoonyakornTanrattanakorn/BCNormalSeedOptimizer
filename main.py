from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import csv
from time import time

def isSlot(s: str) -> bool:
    return len(s) >= 2 and s[:-1].isdigit() and s[-1] in 'AB'

def getNextSlot(slot: str, slotMsg: str) -> str:
    slotNumber = int(slot[:-1]) + (2 if '<-' in slotMsg else 1)
    track = 'A' if '<-' in slotMsg else ('B' if '->' in slotMsg else slot[-1])
    return f"{slotNumber}{track}"


def getSlotData(url: str) -> tuple[list, dict]:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
    
    with webdriver.Chrome(options=options) as driver:
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, "html.parser")

    trackName, slotData, lastSlot = [], {}, None

    for row in soup.find_all("tr"):
        cells = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
        if not cells:
            continue
        if cells[0] == '#':
            trackName = cells[1:]
        elif isSlot(cells[0]):
            lastSlot = cells[0]
        elif lastSlot:
            slotData[lastSlot] = cells
            lastSlot = None

    return trackName, slotData


def stripSlotName(slotName: str) -> str:
    if '<-' in slotName:
        return " ".join(slotName.split()[2:])
    if '->' in slotName:
        return slotName.split("->")[0].strip()
    return slotName

def getRewardDict() -> dict:
    with open('itemValue.csv', mode='r') as file:
        return {
            item.strip(): int(count)
            for row in csv.reader(file)
            if len(row) == 2
            for count, item in [row]
        }

def isTrackSwitch(itemList: list) -> bool:
    for i in itemList:
        if('->' in i or '<-' in i): return True
    return False

def useTicket(trackName: str, tickets: tuple) -> tuple:
    tmp = list(tickets)
    if trackName == 'Normal':
        tmp[0] -= 1
    elif trackName == 'Catseye':
        tmp[0] -= 1
    elif trackName == 'Lucky Ticket':
        tmp[1] -= 1
    return tuple(tmp)

def optimizedPath(trackName: list, dp: dict, rewardDict: dict, slotData: dict, tickets: tuple, currentSlot: str, depth: int) -> tuple[list, int]:
    if currentSlot not in slotData or depth == 0:
        return [], 0
    if (currentSlot, tickets) in dp:
        return dp[(currentSlot, tickets)]

    slot = slotData[currentSlot]
    bestReward = float('-inf')
    bestChoices = []

    for idx in range(len(slot)):
        item = slot[idx]
        itemReward = rewardDict[stripSlotName(item)]
        nextSlot = getNextSlot(currentSlot, item)

        nextTickets = useTicket(trackName[idx], tickets)
        if -1 in nextTickets: continue
        nextChoices, nextReward = optimizedPath(trackName, dp, rewardDict, slotData, nextTickets, nextSlot, depth-1)

        totalReward = itemReward + nextReward
        if totalReward > bestReward:
            bestReward = totalReward
            bestChoices = [(currentSlot, stripSlotName(item))] + nextChoices

    dp[(currentSlot, tickets)] = (bestChoices, bestReward)
    return dp[(currentSlot, tickets)]


# for k, v in slotData.items():
#     print(k, v)

url = "https://ampuri.github.io/bc-normal-seed-tracking/?seed=647505473&banners=ce%2Clt%2Cn&lastCat=Bird+Cat&selected=c%2C304823453%2Cn&rolls=999"
trackName, slotData = getSlotData(url)
items = {stripSlotName(e) for v in slotData.values() for e in v}

# silver, lucky
tickets = (20, 1)

start = time()
dp = dict()
rewardDict = getRewardDict()
bestPath, bestReward = optimizedPath(trackName, dp, rewardDict, slotData, tickets, '1A', 20)
print(trackName)
print(bestReward)
for i, j in bestPath:
    print(i, j)
end = time()
print(f"{round(end-start, 2)} s")
# TODO
# dupe same track two time make track switch
# search depending on available ticket