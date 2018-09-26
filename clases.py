import datetime
import csv
import sys
sys.setrecursionlimit(10000)
from tabulate import tabulate
import csv




class City:
    def __init__(self, id, city):
        self.id = id
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
        ref.city = self.home.city

    def has_all_refs(self):
        if len(self.referees) < 3:
            return 0
        return 1


class Referee:
    def __init__(self, id, type, city, income, aditional_income):
        self.id = id
        self.type = type

        self.home = city
        self.prev_city = city
        self.city = city
        self.city.add_referee(self)

        self.income = income
        self.aditional_income = aditional_income

        self.resting = 0
        self.days_away = 0

        self.moved_today = 0
        self.moved_yesterday = 0
        self.refdays = []
        self.refgames = []

        self.timeline = []

    def is_valid(self, game):
        if self in game.referees:
            return 0
        if self.moved_today == 1:
            return 0
        if self.home == game.home.city:
            return 0
        if 0 < self.resting < 3:
            return 0
        if self.days_away > 4:
            return 0
        return 1

    def move_home(self):
        self.resting = 1
        self.days_away = 0
        self.prev_city = self.city
        self.city = self.home

    # def move_back(self):
    #     self.resting = 0

    def assign_game(self, game):
        self.prev_city = self.city
        self.city = game.home.city
        # self.days_away += 1
        self.refdays.append(game.day)
        self.refgames.append(game)
        game.referees.append(self)
        self.moved_yesterday = self.moved_today
        self.moved_today = 1

    def unassign_game(self, game):

        self.city = self.prev_city
        # self.days_away -= 1
        self.refdays.remove(game.day)
        self.refgames.remove(game)
        game.referees.remove(self)
        self.moved_today = self.moved_yesterday
        # self.moved_today = 0



class NBA:
    def __init__(self):
        self.cities = {}  # dict with {[NAME] = City}
        self.channels = {}  # dict with {[NAME] = Channel}
        self.teams = {}  # dict with {[CODE] = Team}
        self.games = {}  # dict with {[DATE] = [Games]}
        self.referees = {}  # dict wirh {[CODE] = Referee}

    def update_all_refs(self):
        refs =  [r for r in self.referees.values()]
        for ref in refs:
            ref.moved_today = 0
            if ref.resting:
                ref.resting += 1
            if ref.days_away > 4:
                ref.move_home()
            if ref.city != ref.home:
                ref.days_away += 1
            ref.timeline.append(ref.city.id)


    def revert_all_refs(self):
        print("REEVEVVEERTTTT")
        refs =  [r for r in self.referees.values()]
        for ref in refs:
            ref.timeline = ref.timeline[:-1]
    #





    def pick_city(self, id, name):
        if name not in self.cities:
            self.cities[name] = City(id, name)
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
        if game.day not in self.games:
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
                id = line["ID"]
                city = self.pick_city(id, line["CITY"])
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

    def make_timeline(self):
        refs =  [r for r in self.referees.values()]
        for r in refs:
            for day in self.games:
                if day in r.refdays:
                    for game in r.refgames:
                        if game.day == day:
                            r.timeline.append(game.home.code)
                            break
                else:
                    r.timeline.append("-")






def backtrack(nba, day, num_game):
    if (day >= 178):                        # END CONDITION
        return 1
    if (day in nba.games):                  # SOME DAYS DON'T HAVE GAMES
        game = nba.games[day][num_game-1]
        refs = nba.order_costs(game)
    else:
        nba.update_all_refs()
        return backtrack(nba, day + 1, 1)

    for ref in refs:
        if ref.is_valid(game):
            ref.assign_game(game)                           # IF VALID: ASSIGN
            #move the ref there
            if not game.has_all_refs():
                return backtrack(nba, day, num_game)        # STAY ON THIS DAY and GAME
            else:
                if num_game >= len(nba.games[day]):
                    nba.update_all_refs()
                    if backtrack(nba, day+1, 1):             # IF LAST GAME, GO TO NEXT DAY
                        return (1)
                    # revert_all_refs();
                else:
                    if backtrack(nba, day, num_game + 1):   # GO TO NEXT GAME
                        return (1)
            ref.unassign_game(game)
            #move ref back
    return (0)


def export():
    csvfile = "datos/timeline.csv"
    refs =  [r for r in nba.referees.values()]
    data = [t.timeline for t in refs]
    days = [i for i in range(1,178)]
    data.insert(0, days)
    data[0].insert(0, "-")
    i = 0
    for d in data:
        if i != 0:
            d.insert(0,i)
        i += 1

    with open(csvfile, "w") as output:
        writer = csv.writer(output, lineterminator='\n')
        writer.writerows(data)


if __name__ == "__main__":
    nba = NBA()

    print("Cargando seeds")
    nba.seed_locations("datos/locations.csv")
    nba.seed_games("datos/games.csv")
    nba.seed_distances("datos/distances (mi & km).csv")
    nba.seed_flight_costs("datos/flight costs.csv")
    nba.seed_referees("datos/referees.csv")
    print("Seeds terminado")

    backtrack(nba, 1, 1)

    for i in range(1,178):
        if i in nba.games:
            print("--------- DAY " + str(i) + " -----------")
            g = 1
            for game in nba.games[i]:
                refs =  [r.id for r in game.referees]
                print("Game " + str(g) +": " + str(refs))
                g += 1
    export()




    refs =  [r for r in nba.referees.values()]
    refs.sort(key=lambda x: len(set(x.timeline)), reverse=False)
    for ref in refs:
        print ("ID:" + str(ref.id) + "\nHOME: " + str(ref.home.city_name) + "\nDIF.CITIES:" + str(len(set(ref.timeline))) + "\nCITIES:" + str(set(ref.timeline)) + "\n")
        # print(str(ref.timeline))
