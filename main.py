from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import csv

def isSlot(s):
    if len(s) < 2: return False
    return s[:-1].isdigit() and s[-1] in 'AB'

def getNextSlot(slot, slotMsg):
    slotNumber = int(slot[:-1]) + 1
    track = slot[-1]
    if "->" in slotMsg:
        track = 'B'
    elif "<-" in slotMsg:
        track = 'A'
        slotNumber += 1
    return str(slotNumber) + track

def getSlotData(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    # input("Press any key to continue...")

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    lastSlot = "-"
    trackName = []
    slotData = dict()
    for row in soup.find_all("tr"):
        cells = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
        # 1) table head
        # 2) is track number
        # 3) content
        if cells[0] == '#':
            trackName = cells[1:]
        elif isSlot(cells[0]):
            lastSlot = cells[0]
        elif(lastSlot != '-'):
            # print(lastSlot, cells)
            slotData[lastSlot] = cells
            lastSlot = '-'

    driver.quit()

    return trackName, slotData

def stripSlotName(slotName):
    if '<-' in slotName:
        slotName = " ".join(slotName.split()[2:])
    elif '->' in slotName:
        slotName = slotName.split("->")[0].strip()
    return slotName

def getRewardDict():
    rewardDict = dict()
    with open('itemValue.csv', mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 0: continue
            count, item = row
            rewardDict[item.strip()] = int(count)
    return rewardDict;


url = "https://ampuri.github.io/bc-normal-seed-tracking/?seed=647505473&banners=ce%2Clt%2Cn&lastCat=Bird+Cat&selected=c%2C304823453%2Cn"
trackName, slotData = getSlotData(url)
items = {stripSlotName(e) for v in slotData.values() for e in v}

tickets = {'silver' : 50, 'lucky' : 50}

def isTrackSwitch(itemList):
    for i in itemList:
        if('->' in i or '<-' in i): return True
    return False


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
bestPath, bestReward = optimizedPath(rewardDict, slotData, '1A', 100)
print(recur)
print(bestReward)
for i, j in bestPath:
    print(i, j)
    
## dupe same track two time make track switch