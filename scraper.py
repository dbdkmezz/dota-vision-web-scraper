from bs4 import BeautifulSoup
import re
import requests

ALL_HERO_NAMES_URL = "http://www.dota2.com/heroes/"

class HeroAndAdvantage:
    name = ""
    database_name = ""
    advantage = ""

    def __init__(self, name, advantage):
        self.name = name
        self.database_name = name.replace("'", "")
        self.advantage = advantage


class AdvantageDataForAHero:
    ADVANTAGES_URL_START = "http://www.dotabuff.com/heroes/"
    ADVANTAGES_URL_END = "/matchups"

    HERO_ROLES_URL = "http://wiki.teamliquid.net/dota2/Hero_Roles"
    CARRY_STRING = "Carry"
    SUPPORT_STRING = "Support"

    MID_LANES_URL = "http://www.dotabuff.com/heroes/lanes?lane=mid"
    MINIUM_MID_PRESENCE = 30

    name = ""
    database_name = ""
    advantages_data = []

    # These must be given with the boolean values True and False because, instead 
    # shuold use 0 or 1 because that's what's needed when saving to the database.
    is_carry = None
    is_support = None
    is_mid = None

    def __init__(self, name):
        self.name = name
        self.database_name = name.replace("'", "")
        self.load_roles()
        self.load_advantages_data()

    def load_roles(self):
        web_content = load_url(self.HERO_ROLES_URL)
        soup = BeautifulSoup(web_content, "html.parser")
        self.is_carry = self.is_role(soup, self.name, self.CARRY_STRING)
        self.is_support = self.is_role(soup, self.name, self.SUPPORT_STRING)

        self.is_mid = self.is_mid()

    def load_advantages_data(self):
        url = self.ADVANTAGES_URL_START + self.name_to_url_name(self.name) + self.ADVANTAGES_URL_END
        web_content = load_url(url)
        self.advantages_data = self.get_advantages_from_string(web_content)

    @staticmethod
    def is_role(soup, hero_name, role_name):
        comparison_name = hero_name.replace("-", "")
        role_column = AdvantageDataForAHero.get_role_column(soup, role_name)
        table_soup = soup.find("table", class_="wikitable sortable collapsible collapsed")
        rows = table_soup.find_all("tr")
        for row in rows:
            if(re.search(comparison_name, row.get_text(), flags=re.IGNORECASE) != None):
                if(re.search("★", row.find_all("td")[role_column].get_text())):
                    return 1
        
        return 0

    @staticmethod
    def get_role_column(soup, role_name):
        table_soup = soup.find("table", class_="wikitable sortable collapsible collapsed")
        headings = table_soup.find_all("th")
        i = 0
        for h in headings:
            if(h.get_text() == role_name):
                return i
            i += 1

        return None

    def is_mid(self):
        return self.static_is_mid(BeautifulSoup(load_url(self.MID_LANES_URL), "html.parser"), self.name)

    # This is a static method, becuase that's better for testing
    @staticmethod
    def static_is_mid(soup, hero_name):
        table_soup = soup.find("table", class_="sortable")
        for row in table_soup.find_all("tr"):
            name_cell = row.find("td", class_="cell-xlarge")
            if((name_cell is not None) and (name_cell.get_text() == hero_name)):
                # Find the cell with a "%" character in the string
                presence_cell = row.find(string=re.compile("%"))
                presence_value = AdvantageDataForAHero.get_num_from_percent(presence_cell)
                if(presence_value >= AdvantageDataForAHero.MINIUM_MID_PRESENCE):
                    return 1
                else:
                    return 0
        
        return 0
    
    @staticmethod
    def name_to_url_name(name):
        name = name.lower()
        name = name.replace(" ", "-")
        name = name.replace("'", "")
        return name

    @staticmethod
    def get_advantages_from_string(web_content):
        soup = BeautifulSoup(web_content, "html.parser")
        soup = soup.find("table", class_="sortable")

        list = []

        for row in soup.find_all(AdvantageDataForAHero.has_data_link_to_attr):
            name = row.find(class_="cell-xlarge").get_text()
            advantage_cell = row.find(string=re.compile("%"))
            advantage = AdvantageDataForAHero.get_num_from_percent(advantage_cell)
            list.append(HeroAndAdvantage(name, advantage))

        return list

    @staticmethod
    def has_data_link_to_attr(tag):
        return tag.has_attr("data-link-to") 

    @staticmethod
    def has_data_value_attr(tag):
        return tag.has_attr("data-value") 

    @staticmethod
    def get_num_from_percent(string):
        string = string.replace("%", "")
        if(len(string) == 0):
            return 0
        return float(string)


def load_file(filename):
    with open(filename, "r") as content_file:
        return content_file.read()

def load_url(url):
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"}
    r = requests.get(url, headers=headers)
    return r.text

def get_hero_names_from_string(content):
    soup = BeautifulSoup(content, "html.parser")
    soup = soup.find(id="filterName")

    list = []

    for row in soup.find_all("option"):
        text = row.get_text()
        if(text != "HERO NAME" and text != "All"):
            list.append(text)

    return list

def load_all_hero_data():
    web_content = load_url(ALL_HERO_NAMES_URL)
    hero_list = get_hero_names_from_string(web_content)
    results = []
    total_loaded = 0
    for hero in hero_list:
        print("{}. Loading {}".format(total_loaded, hero))
        total_loaded += 1
        results.append(AdvantageDataForAHero(hero))
        
    return results
