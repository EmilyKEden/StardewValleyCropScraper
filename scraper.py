import requests
from bs4 import BeautifulSoup
import re
import csv

#Parses a list to find the index that contains a substring
def find_index_regex(the_list, regexSubstring):
    i = 0
    for l in the_list:
        s = str(l)
        x = re.search(regexSubstring, s)
        if x:
            return i
        else:
            i = i + 1
    return -1

#get the URL for Stardew Valley Crops list
page = requests.get("https://stardewvalleywiki.com/Crops")
#Beautiful Soup this Bitch
soup = BeautifulSoup(page.content, 'html.parser')

#Use the no-wrap class to parse through the prices of seeds as well as
#Selling price data for crops
prices = soup.find_all(class_="no-wrap") #returns a list
#used regex in order to narrow my prices list
endOfHeadersIndex = find_index_regex(prices, ".Pierre.")
ancientFruitIndex = find_index_regex(prices, ".Ancient_Seed.")
prices = prices[endOfHeadersIndex:ancientFruitIndex]

#Scrape for the sections that include the amount of time it takes for a crop to grow
#This sections has no mess in the header so we only need to cut it off when it starts
#At ancient fruit
harvest = soup.find_all(class_="wikitable roundedborder")
ancientFruitIndex = find_index_regex(harvest, ".Ancient_Seed.")
harvest = harvest[:ancientFruitIndex]

#Scrape the headlines, which should be seasons and crop names
headlines = soup.find_all(class_="mw-headline") #returns a list
#Remove headers that come before the crops and seasons (the information at the top of the page)
endOfHeadersIndex = find_index_regex(headlines, "Spring Crops")
winterCropsIndex = find_index_regex(headlines, "Winter Crops")
headlines = headlines[endOfHeadersIndex:winterCropsIndex]

#This loop parses through prices and pulls the data and puts them into
#lists for easy combination later
seedPricesList = []
cropPricesList = []
for p in prices:
    q = str(p)
    #remove Coffee beans from prices
    x = re.search(".Coffee.", q)
    if x:
        prices.remove(p)
    else:
        pierre = re.findall("General Store\">Pierre\'s</a>: <span class=\"no-wrap\" data-sort-value=\"[0-9]{2,3}", q)
        oasis = re.findall("Oasis</a>: <span class=\"no-wrap\" data-sort-value=\"[0-9]{2,3}", q)
        eggFestival = re.findall("Egg Festival</a>: <span class=\"no-wrap\" data-sort-value=\"[0-9]{2,3}", q)
        if pierre:
            seedPrice = re.findall("[0-9]{2,3}", str(pierre))
            seedPricesList.extend(seedPrice)
        elif oasis:
            seedPrice = re.findall("[0-9]{2,3}", str(oasis))
            seedPricesList.extend(seedPrice)
        elif eggFestival:
            seedPrice = re.findall("[0-9]{2,3}", str(eggFestival))
            seedPricesList.extend(seedPrice)
        else:
            r = re.sub("\n", "", q)
            cropSell = re.findall("<div class=\"qualityindicator\"></div></div></div></td><td>[0-9]{2,3}g", r)
            if cropSell:
                cropSellPrice = re.findall("[0-9]{2,3}", str(cropSell))
                cropPricesList.extend(cropSellPrice)

#In case I forget, I have this here because if I try to remove coffee
#in the harvest loop, as I did in the previous loop where it works fine, it screws up garlic
#for some reason, I need to completely remove coffee from my loop BEFORE grabbing
#the total days of harvest in order for it to work properly
for h in harvest:
    g = str(h)
    x = re.search(".Coffee.", g)
    if x:
        harvest.remove(h)
j = 0
harvestTimesList = []
regrowthDataList = []
for h in harvest:
    g = str(h)
    r = re.sub("\n", "", g)
    r = re.sub("<br/>"," ", r)
    total = re.findall("Total: [0-9]{1,2} day.", r)
    withRegrow = re.findall("Regrowth: [0-9]{1,2} day.", r)
    j = j + 1
    if withRegrow:
        total = re.findall("[0-9]{1,2}", str(total))
        harvestTimesList.extend(total)
        withRegrow = re.findall("[0-9]{1,2}", str(withRegrow))
        regrowthDataList.extend(withRegrow)
    elif total:
        total = re.findall("[0-9]{1,2}", str(total))
        if len(total) > 1:
            harvestTimesList.append(total)
            regrowthDataList.append("NA")
        else:
            harvestTimesList.extend(total)
            regrowthDataList.append("NA")
        
#pulls out the names from headlines, and categorizes
#them by seasons, put into a list of lists
plantDataList = []
i = 0
for h in headlines:
    name = h.text
    name = name.strip()
    #Removing instance of Coffee Bean. Coffee Beans are really an outlier
    #as far as crops go, so it will be analyzed separately
    if name != "Coffee Bean":
        x = re.search("Crops$", name)
        if x:
            #Using regex to remove the word crop for better categorizing later
            y = re.split("\s", name)
            season = y[0]
        else:
            tempList = [season, name, seedPricesList[i], cropPricesList[i], harvestTimesList[i], regrowthDataList[i]]
            plantDataList.append(tempList)
            i = i + 1
columnNames = ["season","plant_name", "seed_cost", "crop_sell_price", "time_until_harvest", "time_until_regrowth"]
plantDataList.insert(0, columnNames)

#For any plant that my have had 2 grow times due to irrigation, split
#that into two data points
for plant in plantDataList:
    if type(plant[4]) == list:
        tempPlant = plant
        plantDataList.remove(plant)
        plant1 = [plant[0], plant[1], plant[2], plant[3], plant[4][0], plant[5]]
        plant2 = [plant[0], plant[1], plant[2], plant[3], plant[4][1], plant[5]]
        plantDataList.append(plant1)
        plantDataList.append(plant2)

with open("stardewOutput.csv", "w", newline="") as f:
   writer = csv.writer(f)
   writer.writerows(plantDataList)