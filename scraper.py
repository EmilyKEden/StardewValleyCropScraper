import requests
from bs4 import BeautifulSoup
import re
import csv


def find_index_regex(the_list, regex_substring):
    """Parses a list to find the index that contains a substring."""
    i = 0
    for l in the_list:
        s = str(l)
        x = re.search(regex_substring, s)
        if x:
            return i
        else:
            i = i + 1
    return -1


def main():
    # get the URL for Stardew Valley Crops list
    page = requests.get("https://stardewvalleywiki.com/Crops")
    # Beautiful Soup this Bitch
    soup = BeautifulSoup(page.content, 'html.parser')

    # Use the no-wrap class to parse through the prices of seeds as well as
    # selling price data for crops
    prices = soup.find_all(class_="no-wrap")  # returns a list
    # used regex in order to narrow my prices list
    end_of_headers_index = find_index_regex(prices, ".Pierre.")
    ancient_fruit_index = find_index_regex(prices, ".Ancient_Seed.")
    prices = prices[end_of_headers_index:ancient_fruit_index]

    # Scrape for the sections that include the amount of time it takes for a crop to grow
    # This section has no mess in the header so we only need to cut it off when it starts
    # at ancient fruit
    harvest = soup.find_all(class_="wikitable roundedborder")
    ancient_fruit_index = find_index_regex(harvest, ".Ancient_Seed.")
    harvest = harvest[:ancient_fruit_index]

    # Scrape the headlines, which should be seasons and crop names
    headlines = soup.find_all(class_="mw-headline")  # returns a list
    # Remove headers that come before the crops and seasons (the information at the top of the page)
    end_of_headers_index = find_index_regex(headlines, "Spring Crops")
    winter_crops_index = find_index_regex(headlines, "Winter Crops")
    headlines = headlines[end_of_headers_index:winter_crops_index]

    # This loop parses through prices and pulls the data and puts them into
    # lists for easy combination later
    seed_prices_list = []
    crop_prices_list = []
    for p in prices:
        q = str(p)
        # remove Coffee beans from prices
        x = re.search(".Coffee.", q)
        if x:
            prices.remove(p)
        else:
            # this line is too long and needs to be split, but I couldn't figure out the best way
            pierre = re.findall("General Store\">Pierre\'s</a>: <span class=\"no-wrap\" data-sort-value=\"[0-9]{2,3}", q)
            oasis = re.findall("Oasis</a>: <span class=\"no-wrap\" data-sort-value=\"[0-9]{2,3}", q)
            egg_festival = re.findall("Egg Festival</a>: <span class=\"no-wrap\" data-sort-value=\"[0-9]{2,3}", q)
            if pierre:
                seed_price = re.findall("[0-9]{2,3}", str(pierre))
                seed_prices_list.extend(seed_price)
            elif oasis:
                seed_price = re.findall("[0-9]{2,3}", str(oasis))
                seed_prices_list.extend(seed_price)
            elif egg_festival:
                seed_price = re.findall("[0-9]{2,3}", str(egg_festival))
                seed_prices_list.extend(seed_price)
            else:
                r = re.sub("\n", "", q)
                crop_sell = re.findall("<div class=\"qualityindicator\"></div></div></div></td><td>[0-9]{2,3}g", r)
                if crop_sell:
                    crop_sell_price = re.findall("[0-9]{2,3}", str(crop_sell))
                    crop_prices_list.extend(crop_sell_price)

    # In case I forget, I have this here because if I try to remove coffee
    # in the harvest loop, as I did in the previous loop where it works fine, it screws up garlic
    # for some reason, I need to completely remove coffee from my loop BEFORE grabbing
    # the total days of harvest in order for it to work properly
    for h in harvest:
        g = str(h)
        x = re.search(".Coffee.", g)
        if x:
            harvest.remove(h)
    j = 0
    harvest_times_list = []
    regrowth_data_list = []
    for h in harvest:
        g = str(h)
        r = re.sub("\n", "", g)
        r = re.sub("<br/>", " ", r)
        total = re.findall("Total: [0-9]{1,2} day.", r)
        with_regrow = re.findall("Regrowth: [0-9]{1,2} day.", r)
        j = j + 1
        if with_regrow:
            total = re.findall("[0-9]{1,2}", str(total))
            harvest_times_list.extend(total)
            with_regrow = re.findall("[0-9]{1,2}", str(with_regrow))
            regrowth_data_list.extend(with_regrow)
        elif total:
            total = re.findall("[0-9]{1,2}", str(total))
            if len(total) > 1:
                harvest_times_list.append(total)
                regrowth_data_list.append("NA")
            else:
                harvest_times_list.extend(total)
                regrowth_data_list.append("NA")

    # pulls out the names from headlines, and categorizes
    # them by seasons, put into a list of lists
    plant_data_list = []
    i = 0
    for h in headlines:
        name = h.text
        name = name.strip()
        # Removing instance of Coffee Bean. Coffee Beans are really an outlier
        # as far as crops go, so it will be analyzed separately
        if name != "Coffee Bean":
            x = re.search("Crops$", name)
            if x:
                # Using regex to remove the word crop for better categorizing later
                # to do: change \s, PyCharm says "PEP 8: W605 invalid escape sequence '\s'"
                y = re.split("\s", name)
                season = y[0]
            else:
                # PyCharm warning: "Local variable 'season' might be referenced before assignment"
                temp_list = [season, name, seed_prices_list[i], crop_prices_list[i], harvest_times_list[i],
                             regrowth_data_list[i]]
                plant_data_list.append(temp_list)
                i = i + 1
    column_names = ["season", "plant_name", "seed_cost", "crop_sell_price", "time_until_harvest", "time_until_regrowth"]
    plant_data_list.insert(0, column_names)

    # For any plant that my have had 2 grow times due to irrigation, split
    # that into two data points
    for plant in plant_data_list:
        if type(plant[4]) == list:
            # The variable temp_plant is never used. Consider removing it unless needed
            temp_plant = plant
            plant_data_list.remove(plant)
            plant1 = [plant[0], plant[1], plant[2], plant[3], plant[4][0], plant[5]]
            plant2 = [plant[0], plant[1], plant[2], plant[3], plant[4][1], plant[5]]
            plant_data_list.append(plant1)
            plant_data_list.append(plant2)

    with open("stardewOutput.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(plant_data_list)


if __name__ == '__main__':
    main()
