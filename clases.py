import datetime
import csv


class City:
    def __init__(self, city):
        self.city = city
        self._hotel_cost = None
        self.team = None

        self.distances = {}  # dict with {[City] = distance (mi)}
        self.flights = {}  # dict with {[City] = cost}
        self.referees = []  # list with actual refeeres (Referee)

    @property
    def hotel_cost(self):
        return self._hotel_cost

    @hotel_cost.setter
    def hotel_cost(self, cost):
        self._hotel_cost = int(cost)

    @property
    def city_name(self):
        return str(self.city.split(",")[0].strip().lower())

    @property
    def state(self):
        return str(self.city.split(",")[1].strip().lower())

    def add_distance(self, city, distance):
        if not distance:
            distance = 0
        distance = int(distance)
        if self == city or distance == 0:
            self.distances[city] = 0
            return

        if city not in self.distances:
            self.distances[city] = distance

        if self not in city.distances:
            city.distances[self] = distance

    def add_flight(self, to_city, cost):
        cost = int(cost)
        if self == to_city or cost == 0:
            return

        if to_city not in self.flights:
            self.flights[to_city] = cost

    def add_referee(self, referee):
        if referee not in self.referees:
            self.referees.append(referee)
            return True
        return False


class Team:
    def __init__(self, code):
        self.name = None
        self.code = code
        self.arena = None
        self.city = None
        self.games = []

    def add_game(self, game):
        if game not in self.games:
            self.games.append(game)
            return True
        return False

    def set_city(self, city):
        self.city = city
        city.team = self


class Channel:
    def __init__(self, name):
        self.name = name
        self.games = []

    def add_game(self, game):
        if game not in self.games:
            self.games.append(game)
            return True
        return False


class Game:
    def __init__(self, home, away, date, day, channel):
        self.home = home
        self.home.add_game(self)

        self.away = away
        self.away.add_game(self)

        self.date = date
        self.day = int(day)
        self.referees = []

        self.channel = channel
        if self.channel:
            self.channel.add_game(self)

    def assign_ref(self, ref):
        self.referees.append(ref)
        ref.city = self.home


class Referee:
    def __init__(self, id, type, city, income, aditional_income):
        self.id = id
        self.type = type

        self.home = city
        self.city = city
        self.city.add_referee(self)

        self.income = income
        self.aditional_income = aditional_income

        self.resting = 0
        self.days_away = 0



class NBA:
    def __init__(self):
        self.cities = {}  # dict with {[NAME] = City}
        self.channels = {}  # dict with {[NAME] = Channel}
        self.teams = {}  # dict with {[CODE] = Team}
        self.games = {}  # dict with {[DATE] = [Games]}
        self.referees = {}  # dict wirh {[CODE] = Referee}

    def pick_city(self, name):
        if name not in self.cities:
            self.cities[name] = City(name)
        return self.cities[name]

    def pick_channel(self, name):
        if name not in self.channels:
            self.channels[name] = Channel(name)
        return self.channels[name]

    def pick_team(self, code):
        if code not in self.teams:
            self.teams[code] = Team(code)
        return self.teams[code]

    def pick_team_name(self, name):
        for code in self.teams:
            if self.teams[code].name == name:
                return self.teams[code]
        return False

    def add_game(self, game):
        if game.date not in self.games:
            self.games[game.day] = []
        self.games[game.day].append(game)
        return True

    def seed_locations(self, file):
        with open(file) as csvfile:
            lines = csv.DictReader(csvfile)
            for line in lines:
                team = self.pick_team(line["CODE"])
                team.name = line["TEAM"]
                team.arena = line["ARENA"]

                city = self.pick_city(line["CITY"])
                city.hotel_cost = line["HOTEL COST"]

                team.set_city(city)
                self.teams[line["CODE"]] = team

    def seed_games(self, file):
        with open(file) as csvfile:
            lines = csv.DictReader(csvfile)
            for line in lines:
                channel_name = line["CHANNEL"]
                channel = None
                if channel_name != "X":
                    channel = self.pick_channel(line["CHANNEL"])


                away = self.pick_team_name(line["AWAY"])
                home = self.pick_team_name(line["HOME"])



                date = datetime.datetime.strptime(line["DATE"], "%m/%d").date()
                if date.month >= 10:
                    date = date.replace(year=2018)
                else:
                    date = date.replace(year=2019)

                day = int(line["DAY"])

                game = Game(home, away, date, day, channel)
                self.add_game(game)

    def seed_distances(self, file):
        with open(file) as csvfile:
            lines = csv.reader(csvfile)
            teams = next(lines)[1:]  # el header

            for idx1, line in enumerate(lines):
                team = line[0]
                index_team = teams.index(team)
                distances = line[index_team + 1:]

                from_city = self.teams[team].city

                for idx2, distance in enumerate(distances):
                    to_city = self.teams[teams[idx1 + idx2]].city
                    from_city.add_distance(to_city, distance)

    def seed_flight_costs(self, file):
        with open(file) as csvfile:
            lines = csv.reader(csvfile)
            teams = next(lines)[1:]  # el header

            for line in lines:
                team = line[0]
                costs = line[1:]

                from_city = self.teams[team].city

                for idx1, cost in enumerate(costs):
                    if cost == 0 or not cost:
                        continue

                    to_city = self.teams[teams[idx1]].city
                    from_city.add_flight(to_city, cost)

    def seed_referees(self, file):
        with open(file, encoding='utf-8-sig') as csvfile:
            lines = csv.DictReader(csvfile)
            for line in lines:
                code = line["Código del árbitro"]
                type = line["Tipo de árbitro"]
                income = line["Sueldo mensual [USD]"]
                aditional_income = line["Pago adicional por partido dirigido [USD]"]

                city = line["Ciudad en que vive"]
                if "," in city:
                    city_name, state = city.split(",", 1)
                    city_name = city_name.strip().lower()
                    state = state.strip().lower()
                else:  # Washington DC
                    city_name = "Washington".strip().lower()
                    state = "D.C."

                translate = {"auburn hills": "detroit",  # esto esta por mientras
                             "filadelfia": "philadelphia",
                             "los ángeles": "los angeles",
                             "nueva orleans": "new orleans",
                             "indianápolis": "indianapolis",
                             "nueva york": "new york" }

                if city_name in translate:
                    city_name = translate[city_name]

                city_found = None
                for i in self.cities.values():
                    if i.city_name == city_name:
                        city_found = i
                        break

                if not city_found:
                    raise Exception("No es posible encontrar la ciudad '{}' para arbitro id '{}'".format(city, code))

                referee = Referee(code, type, city_found, income, aditional_income)
                self.referees[code] = referee

    def order_costs(self, game):
        refs =  [r for r in self.referees.values()]
        refs.sort(key=lambda x: int(x.city.distances[game.home.city]), reverse=False)
        return refs

def is_valid(ref, game):
    if ref.home == game.home.city:
        return 0
    #blah blah

def backtrack(nba, day, num_game):
    if (day >= 177 && numb_game >= 10)
        return 1
    if (day > 1 and num_game == 1):
        #update_all_refs()
    game = nba.games[day][num_game]
    refs = nba.order_costs(game)
    for ref in refs:
        if is_valid(ref, game):
            #move the ref there
            if num_game == len(nba.games[day]):
                if backtrack(nba, day+1, 1):
                    return (1)
                #revert_all_refs();
            else:
                if backtrack(nba, day, num_game + 1):
                    return (1)
            #move ref back
    return (0);




if __name__ == "__main__":
    nba = NBA()

    print("Cargando seeds")
    nba.seed_locations("datos/locations.csv")
    nba.seed_games("datos/games.csv")
    nba.seed_distances("datos/distances (mi & km).csv")
    nba.seed_flight_costs("datos/flight costs.csv")
    nba.seed_referees("datos/referees.csv")
    print("Seeds terminado")
    # for game in nba.games:
    #     print(str(nba.games[game][0].home.city) + " vs " + str(nba.games[game][0].away.city))
    test_game = next(iter(nba.games.values()))[0]
    test_refs = nba.order_costs(test_game)
    print(test_game.home.city.city_name)
    for r in test_refs:
        print (str(r.id) + ": " + str(test_game.home.city.distances[r.city]))
        # i+=1
    # print(test_refs[0].id)
    # print(test_game.home.city.city_name)
