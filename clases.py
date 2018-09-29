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
    def city_state(self):
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
        if self.has_all_refs:
            raise Exception("All refs are assigned to this game {}".format(vars(self)))

        if not self.can_assign_ref(ref):
            raise Exception("Error. Can't assign referee or it will be invalid")

        self.referees.append(ref)
        ref.city = self.home.city

    def can_assign_ref(self, ref):  # check if referee is allowed to be assigned
        if self.channel and self.channel.name == "ESPN":
            if len(self.referees) >= 3:
                return False
        else:
            if len(self.referees) >= 2:
                return False

        if ref.type == "principal y colaborador":
            return True

        principales = 0
        colaboradores = 0
        for referee in self.referees + [ref]:
            if "principal" in referee.type:  # use lowercase
                principales += 1
            if "colaborador" in referee.type:
                colaboradores += 1

        principales_limit = 1
        colaboradores_limit = 1
        if self.channel and self.channel.name == "ESPN":  # this combination must have 3 referees
            colaboradores_limit = 2

        if principales >= principales_limit:
            return False
        if colaboradores >= colaboradores_limit:
            return False

        return True  # if neither of the other, return True

    def has_all_refs(self):  # checks if all refs depending on type and ref type are correct
        if len(self.referees) < 2:  # every game must have at least 2 referees
            return False

        principales = 0
        colaboradores = 0
        for referee in self.referees:
            if "principal" in referee.type:  # use lowercase
                principales += 1
            if "colaborador" in referee.type:
                colaboradores += 1

        if self.channel and self.channel.name == "ESPN":  # this combination must have 3 referees
            if len(self.referees) < 3:
                return False
            else:
                if not (principales >= 1 and colaboradores >= 2):
                    return False
        else:
            if not (principales >= 1 and colaboradores >= 1):
                return False

        return True  # if neither of the if, return True


class Referee:
    def __init__(self, id, type, city, income, aditional_income):
        self.id = id
        self.type = type.strip().lower()

        self.home = city
        #self.prev_city = city  # hay q cambiar a timeline para poder retroceder mas de un dia
        #self.city = city
        self.home.add_referee(self)

        self.income = income
        self.aditional_income = aditional_income

        self.resting = 0
        self.days_away = 0

        self.moved_today = False
        self.moved_yesterday = False
        self.refdays = []
        self.refgames = []

        self.timeline = [self.home]  # cities where it've been

    @property
    def city(self):
        return self.timeline[-1]

    def is_valid(self, game):
        if self in game.referees:  # it's already on the game
            return False
        #if self.moved_today:  # can't refer on the same day
        #    return False
        if self.home == game.home.city:  # can't refer at home
            return False
        if self.city == self.home and 0 < self.resting < 3:  # if at home, it must rest at least 3 days
            return False
        if self.days_away > 4:  # can't be more than 4 days outside
            return False
        return game.can_assign_ref(self)
        #return True

    def move_city(self, from_city, to_city):
        if from_city == to_city:
            raise Exception("Cant move to the same city")

        self.timeline.append(to_city)
        from_city.referees.remove(self)
        to_city.referees.append(self)

    def move_home(self):
        self.resting = 1
        self.days_away = 0
        self.move_city(self.timeline[-1], self.home)

    # def move_back(self):
    #     self.resting = 0

    def assign_game(self, game):
        if self.city != game.home.city:  # if he needs to move
            self.move_city(self.timeline[-1], game.home.city)
        # self.days_away += 1
        self.refdays.append(game.day)
        self.refgames.append(game)
        game.referees.append(self)
        self.moved_yesterday = self.moved_today
        self.moved_today = True

    def unassign_game(self, game):
        print("unassign")
        # recibe game, pero retrocede una ciudad, no elimina la ciudad de ese game :/
        self.move_city(self.timeline[-1], self.timeline[-2])  # go back one city
        self.timeline = self.timeline[:-2]  # delete last city (-2 item) and avoid duplicated city (-1 item)
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
        self.referees = {}  # dict with {[CODE] = Referee}

    def update_all_refs(self):
        refs = [r for r in self.referees.values()]
        for ref in refs:
            ref.moved_today = False
            if ref.resting:
                ref.resting += 1
            if ref.days_away > 4:
                ref.move_home()
            if ref.city != ref.home:
                ref.days_away += 1
            #ref.timeline.append(ref.city.id)

    def revert_all_refs(self):
        print("REEVEVVEERTTTT")
        refs = [r for r in self.referees.values()]
        for ref in refs:
            ref.move_city(ref.timeline[-1], ref.timeline[-2])  # go back one city
            ref.timeline = ref.timeline[:-2]  # delete last city (-2 item) and avoid duplicated city (-1 item)
            #ref.timeline = ref.timeline[:-1]

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
                    if cost == 0 or not cost:  # misma ciudad
                        cost = 0

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
                    city_name, city_state = city.split(",", 1)
                    city_name = city_name.strip().lower()
                    city_state = city_state.strip().lower()
                else:  # Washington DC
                    city_name = "Washington".strip().lower()
                    city_state = "D.C."

                translate = {"auburn hills": "detroit",  # esto esta por mientras
                             "filadelfia": "philadelphia",
                             "los ángeles": "los angeles",
                             "nueva orleans": "new orleans",
                             "indianápolis": "indianapolis",
                             "nueva york": "new york"}

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
        refs = [r for r in self.referees.values()]
        refs.sort(key=lambda x: int(x.city.flights[game.home.city]), reverse=False)
        return refs

    def make_timeline(self):
        refs = [r for r in self.referees.values()]
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
    if day >= 178:  # END CONDITION
        return True

    if day in nba.games:  # SOME DAYS DON'T HAVE GAMES
        game = nba.games[day][num_game - 1]
        refs = nba.order_costs(game)
    else:
        nba.update_all_refs()
        return backtrack(nba, day + 1, 1)

    for ref in refs:
        if ref.is_valid(game):
            ref.assign_game(game)  # IF VALID: ASSIGN

            if not game.has_all_refs():
                if backtrack(nba, day, num_game):  # STAY ON THIS DAY and GAME
                    return True
            else:
                if num_game >= len(nba.games[day]):
                    nba.update_all_refs()
                    if backtrack(nba, day + 1, 1):  # IF LAST GAME, GO TO NEXT DAY
                        return True
                    # revert_all_refs();
                else:
                    if backtrack(nba, day, num_game + 1):  # GO TO NEXT GAME
                        return True

            ref.unassign_game(game)
            # move ref back
    return False


def export():
    csvfile = "datos/timeline.csv"
    refs = [r for r in nba.referees.values()]
    data = [t.timeline for t in refs]
    days = [i for i in range(1, 178)]
    data.insert(0, days)
    data[0].insert(0, "-")
    i = 0
    for d in data:
        if i != 0:
            d.insert(0, i)
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

    with open("games-days.txt", "w") as day_games:
        for i in range(1, 178):
            if i in nba.games:
                print("--------- DAY " + str(i) + " -----------")
                day_games.write("--------- DAY " + str(i) + " -----------\n")
                g = 1
                for game in nba.games[i]:
                    refs = [r.id for r in game.referees]

                    string = "Game {}: {}; Channel: {}".format(g, refs, game.channel and game.channel.name)
                    print(string)
                    day_games.write(string + "\n")

                    g += 1
    #export()

    refs = [r for r in nba.referees.values()]
    refs.sort(key=lambda x: len(set(x.timeline)), reverse=False)
    with open("refs-info.txt", "w") as refs_info:
        for ref in refs:
            string = "ID: {0.id}\n" \
                     "Home: {0.home.city_name}\n" \
                     "Dif Cities: {1}\n" \
                     "Cities: {2}\n".format(ref, len(set(ref.timeline)), set(map(lambda x: x.city, ref.timeline)))
            print(string)
            refs_info.write(string + "\n")
