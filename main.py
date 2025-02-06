from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options

def isSlot(s):
    if len(s) < 2: return False
    return s[:-1].isdigit() and s[-1] in 'AB'

def getNextSlot(slot, slotMsg):
    slotNumber = int(slot[:-1])
    track = slot[-1]
    if "->" in slotMsg:
        track = 'B'
        slotNumber += 1
    elif "<-" in slotMsg:
        track = 'A'
        slotNumber += 2
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


url = "https://ampuri.github.io/bc-normal-seed-tracking/?seed=647505473&banners=ce%2Clt%2Cn&lastCat=Bird+Cat&selected=c%2C304823453%2Cn"
trackName, slotData = getSlotData(url)
items = {stripSlotName(e) for v in slotData.values() for e in v}

tickets = {'silver' : 50, 'lucky' : 50}

def isTrackSwitch(itemList):
    for i in itemList:
        if('->' in i or '<-' in i): return True
    return False

def optimizedPath(trackName, slotData, currentSlot, depth):
    if isTrackSwitch(slotData[currentSlot]):
        # branch
    else:
        



optimizedPath(trackName, slotData, '1A', 100)