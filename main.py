from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import csv

def isSlot(s):
    return len(s) >= 2 and s[:-1].isdigit() and s[-1] in 'AB'

def getNextSlot(slot, slotMsg):
    slotNumber = int(slot[:-1]) + (2 if '<-' in slotMsg else 1)
    track = 'A' if '<-' in slotMsg else ('B' if '->' in slotMsg else slot[-1])
    return f"{slotNumber}{track}"


def getSlotData(url):
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


def stripSlotName(slotName):
    if '<-' in slotName:
        return " ".join(slotName.split()[2:])
    if '->' in slotName:
        return slotName.split("->")[0].strip()
    return slotName

def getRewardDict():
    with open('itemValue.csv', mode='r') as file:
        return {
            item.strip(): int(count)
            for row in csv.reader(file)
            if len(row) == 2
            for count, item in [row]
        }

def isTrackSwitch(itemList):
    for i in itemList:
        if('->' in i or '<-' in i): return True
    return False

url = "https://ampuri.github.io/bc-normal-seed-tracking/?seed=647505473&banners=ce%2Clt%2Cn&lastCat=Bird+Cat&selected=c%2C304823453%2Cn&rolls=999"
trackName, slotData = getSlotData(url)
items = {stripSlotName(e) for v in slotData.values() for e in v}

tickets = {'silver' : 50, 'lucky' : 50}

recur = 0
dp = dict()
def optimizedPath(rewardDict, slotData, currentSlot, depth):
    global recur
    global dp
    if currentSlot not in slotData or depth == 0:
        return [], 0
    if currentSlot in dp:
        return dp[currentSlot]
    slot = slotData[currentSlot]
    bestItemReward = max(rewardDict[stripSlotName(item)] for item in slot)
    bestItems = [item for item in slot if rewardDict[stripSlotName(item)] == bestItemReward]

    bestChoices, bestReward = [], 0
    for item in bestItems:
        nextSlot = getNextSlot(currentSlot, item)
        nextChoices, nextReward = optimizedPath(rewardDict, slotData, nextSlot, depth - 1)
        if nextReward >= bestReward:
            bestChoices = [(currentSlot, stripSlotName(item))] + nextChoices
            bestReward = nextReward
    recur += 1
    dp[currentSlot] = (bestChoices, bestReward + bestItemReward)
    return bestChoices, bestReward + bestItemReward

# for k, v in slotData.items():
#     print(k, v)

rewardDict = getRewardDict()
bestPath, bestReward = optimizedPath(rewardDict, slotData, '1A', 1001)
print(recur)
print(bestReward)
for i, j in bestPath:
    print(i, j)

# TODO
# dupe same track two time make track switch
# search depending on available ticket