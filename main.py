from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import csv
from time import time

def isSlot(s: str) -> bool:
    return len(s) >= 2 and s[:-1].isdigit() and s[-1] in 'AB'

def getNextSlot(slotName: str, slot: list, trackIdx: str, lastTrackIdx: str) -> str:
    slotNumber = int(slotName[:-1])+1
    track = slotName[-1]
    if trackIdx == lastTrackIdx:
        item = slot[trackIdx]
        if '->' in item:
            track = 'B'
        elif '<-' in item:
            track = 'A'
            slotNumber += 1
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
    elif trackName == 'Catfruit':
        tmp[0] -= 1
    elif trackName == 'Lucky Ticket':
        tmp[1] -= 1
    return tuple(tmp)

def optimizedPath(trackName: list, dp: dict, rewardDict: dict, slotData: dict, tickets: tuple, currentSlot: str, lastTrackIdx: int, depth: int) -> tuple[list, int]:
    if currentSlot not in slotData or depth == 0:
        return [], 0
    if (currentSlot, tickets) in dp:
        return dp[(currentSlot, tickets)]

    slot = slotData[currentSlot]
    bestReward = -1
    bestChoices = []

    for idx in range(len(slot)):
        item = slot[idx]
        itemReward = rewardDict[stripSlotName(item)]
        nextSlot = getNextSlot(currentSlot, slot, idx, lastTrackIdx)

        nextTickets = useTicket(trackName[idx], tickets)
        if -1 in nextTickets: continue

        nextChoices, nextReward = optimizedPath(trackName, dp, rewardDict, slotData, nextTickets, nextSlot, idx, depth-1)

        totalReward = itemReward + nextReward
        if totalReward > bestReward:
            bestReward = totalReward
            bestChoices = [(currentSlot, stripSlotName(item), trackName[idx])] + nextChoices
    dp[(currentSlot, tickets)] = (bestChoices, bestReward)
    return dp[(currentSlot, tickets)]

def getBanners(banner: list) -> str:
    tmp = []
    for b in banner:
        if b == 'Normal':
            tmp.append('n')
        elif b == 'Normal+':
            tmp.append('np')
        elif b == 'Catfruit':
            tmp.append('cf')
        elif b == 'Catseye':
            tmp.append('ce')
        elif b == 'Lucky Ticket':
            tmp.append('lt')
        elif b == 'Lucky Ticket G':
            tmp.append('ltg')
    return "%2C".join(tmp)


# for k, v in slotData.items():
#     print(k, v)
seed = 3676097164
# ['Normal', 'Normal+', 'Catfruit', 'Catseye', 'Lucky Ticket', 'Lucky Ticket G']
banners = getBanners(['Normal', 'Catfruit', 'Lucky Ticket'])

url = f"https://ampuri.github.io/bc-normal-seed-tracking/?seed={seed}&banners={banners}&rolls=999"
trackName, slotData = getSlotData(url)
items = {stripSlotName(e) for v in slotData.values() for e in v}

# silver, lucky
tickets = (70, 23)

print('start')
start = time()
dp = dict()
rewardDict = getRewardDict()
bestPath, bestReward = optimizedPath(trackName, dp, rewardDict, slotData, tickets, '1A', None, 999)
print(trackName)
print(bestReward)
itemDict = dict()
for i, j, k in bestPath:
    print(f"{i:>5} {j:>20} {k:>20}")
    itemDict[j] = itemDict.get(j, 0) + 1
print("Total item:")
for i, j in sorted(itemDict.items(), key=lambda item: item[1], reverse=True):
    print(i, j)
end = time()
print(f"{round(end-start, 2)} s")

# TODO
# Fix track switch logic where for example
# 9A   30K XP
# 10A  30K XP (10K XP -> 11B)
# expected behaviour is if choose 9A and 10A track will switch
# but current behavious is choose 10A and track switch