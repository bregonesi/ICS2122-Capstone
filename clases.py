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

        self.costs = {}

    @property
    def cost(self):
        total_cost = 0
        for item in self.costs.values():
            for entry in item.values():
                total_cost = sum(entry)
        return total_cost

    def add_cost(self, producer_key, detail_key, cost):
        cost = int(cost)

        if producer_key not in self.costs:
            self.costs[producer_key] = {}

        if detail_key not in self.costs[producer_key]:
            self.costs[producer_key][detail_key] = []

        self.costs[producer_key][detail_key].append(cost)

    def remove_cost(self, producer_key, detail_key, cost):
        cost = int(cost)

        self.costs[producer_key][detail_key].remove(cost)

        if not self.costs[producer_key][detail_key]:
            del self.costs[producer_key][detail_key]

        if not self.costs[producer_key]:
            del self.costs[producer_key]

    def assign_ref(self, ref, type):
        if self.has_all_refs():
            raise Exception("All refs are assigned to this game {}".format(vars(self)))

        if not self.can_assign_ref(ref):
            raise Exception("Error. Can't assign referee or it will be invalid")

        if not ref.current_city == self.home.city:
            raise Exception("Error. Referee has not travelled yet.")

        self.referees.append(ref)
        ref.refgames.append(self)

    def undo_assign_ref(self, ref, type):
        self.referees.remove(ref)
        ref.refgames.remove(self)

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
            if referee.type == "principal":  # use lowercase
                principales += 1
            if referee.type == "colaborador":
                colaboradores += 1

        for referee in self.referees + [ref]:
            if referee.type == "principal y colaborador":  # use lowercase
                if principales == 0:
                    principales += 1
                else:
                    colaboradores += 1

        principales_limit = 1
        colaboradores_limit = 1
        if self.channel and self.channel.name == "ESPN":  # this combination must have 3 referees
            colaboradores_limit = 2

        #print("channel: {} | principales: {} | colaboradores: {}".format(self.channel and self.channel.name, principales, colaboradores))

        if principales > principales_limit:
            return False

        if colaboradores > colaboradores_limit:
            return False

        return True  # if neither of the other, return True

    def has_all_refs(self):  # checks if all refs depending on type and ref type are correct
        if len(self.referees) < 2:  # every game must have at least 2 referees
            return False

        principales = 0
        colaboradores = 0
        for referee in self.referees:
            if referee.type == "principal":  # use lowercase
                principales += 1
            if referee.type == "colaborador":
                colaboradores += 1

        for referee in self.referees:
            if referee.type == "principal y colaborador":  # use lowercase
                if principales == 0:
                    principales += 1
                else:
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

        self.income = int(income)
        self.aditional_income = int(aditional_income)

        self.resting = 0
        self.days_away = 0

        self.moved_today = False
        self.moved_yesterday = False
        #self.refdays = []
        self.refgames = []

        self.timeline = [self.home]  # cities where it've been

        self.seven_days_out = 1
        self.four_days_out = 8

    @property
    def current_city(self):
        return self.timeline[-1]

    @property
    def last_day_refer(self):
        return self.refgames[-1].day if self.refgames else 0

    @property
    def max_days_away(self):
        if self.seven_days_out > 0:
            return 7
        elif self.four_days_out > 0:
            return 4
        return 3  # else

    def is_valid(self, game):
        if self in game.referees:  # it's already on the game
            #print("on game")
            return False

        if self.last_day_refer > game.day:  # esto no deberia pasar, pero asi chequeamos que todo vaya bien
            raise Exception("There is an error. Last day refer {}, game day {}".format(self.last_day_refer, game.day))

        if self.last_day_refer == game.day:  # only can refer once a day
            #print("one per day")
            return False

        if self.home == game.home.city:  # can't refer at home
            #print("not at home")
            return False

        if self.current_city == self.home and 0 < self.resting <= 3:  # if at home, it must rest at least 3 days
            #print("resting: {}".format(self.resting))
            return False

        if self.days_away > self.max_days_away:  # can't be more than 4 days outside
            #print("days away")
            return False

        return game.can_assign_ref(self)
        #return True

    def travel_to(self, to_city):
        if self.current_city != to_city:
            self.current_city.referees.remove(self)
            to_city.referees.append(self)

        self.timeline.append(to_city)

    def undo_travel_to(self):
        old_city = self.current_city
        self.timeline = self.timeline[:-1]

        if self.current_city != old_city:
            old_city.referees.remove(self)
            self.current_city.referees.append(self)  # current city now is the old (-1) city

    def move_home(self):
        self.travel_to(self.home)
        self.resting = 1
        self.days_away = 0

    def assign_game(self, game, type):
        game.add_cost(self, "travel_to_game", self.flight_cost_to_game(game))
        self.travel_to(game.home.city)
        game.assign_ref(self, type)

    def undo_assign_game(self, game, type):
        self.undo_travel_to()
        game.undo_assign_ref(self, type)
        game.remove_cost(self, "travel_to_game", self.flight_cost_to_game(game))

    def flight_cost_to_game(self, game):
        return self.current_city.flights[game.home.city]

    def cost_to_game(self, game):
        flight_cost_from = self.flight_cost_to_game(game)

        hotel_cost_current = self.current_city.hotel_cost
        days_waiting = 0
        if self.current_city != self.home:
            days_waiting = game.day - self.last_day_refer - 1

        hotel_cost_game = game.home.city.hotel_cost

        flight_cost_to_home = game.home.city.flights[self.home]

        old_flight_cost_to_home = 0
        if self.current_city != self.home:
            old_flight_cost_to_home = self.current_city.flights[self.home]

        total_cost = flight_cost_from + \
                     (hotel_cost_current + self.aditional_income) * days_waiting + \
                     (hotel_cost_game + self.aditional_income) * 1 + \
                     flight_cost_to_home - \
                     old_flight_cost_to_home

        return total_cost

    def better_before(self, game):
        hotel_cost_current = self.current_city.hotel_cost
        hotel_cost_game = game.home.city.hotel_cost
        return hotel_cost_game < hotel_cost_current and self.current_city != self.home

class NBA:
    def __init__(self):
        self.cities = {}  # dict with {[NAME] = City}
        self.channels = {}  # dict with {[NAME] = Channel}
        self.teams = {}  # dict with {[CODE] = Team}
        self.games = {}  # dict with {[DATE] = [Games]}
        self.referees = {}  # dict with {[CODE] = Referee}

    def update_all_refs(self, day):
        for ref in self.referees.values():
            if ref.resting > 0:
                ref.resting += 1

            if ref.current_city != ref.home:
                ref.days_away += 1

            if ref.current_city != ref.home and day - ref.last_day_refer >= 3:
                # si estuvo mas de 3 dias sin arbitrar, mejor devolverlo el dia despues de arbitrar

                gap = day - ref.last_day_refer
                #print(gap)
                #print("should return")
                ref.move_home()  # lo movemos 'hoy'
                ref.resting += gap - 1  # pero le sumamos 'resting' para simular que lo movimos hace dos dias

            if ref.days_away >= ref.max_days_away:
                if ref.days_away >= 7:
                    ref.seven_days_out -= 1
                elif ref.days_away >= 4:
                    ref.four_days_out -= 1

                ref.move_home()

            #ref.timeline.append(ref.city.id)

    def revert_all_refs(self):
        print("REEVEVVEERTTTT")
        refs = [r for r in self.referees.values()]
        for ref in refs:
            if ref.resting > 0:
                ref.resting -= 1
            if ref.resting == 0:
                ref.undo_travelto()
            if ref.current_city != ref.home:
                ref.days_away -= 1

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
        refs.sort(key=lambda x: x.cost_to_game(game), reverse=False)
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

class Backtrack:
    def __init__(self, nba):
        self.nba = nba
        self.list_game_options = {}  # dict with {game: [options]}
        self.assigned = 0
        self.reused = 0

    def day_valid(self, day):
        for game in self.nba.games[day]:
            if not game.has_all_refs():
                return False
        return True

    def set_referees(self, game):
        referees = iter(self.nba.referees.values())
        while not game.has_all_refs():
            referee = next(referees)
            if referee.is_valid(game):
                referee.assign_game(game, "type not defined yet")


    def all_options(self, game, referees_list):  # calculate all the referees options with its cost of a game
        if game.has_all_refs():
            refs = [ref.id for ref in game.referees]
            self.list_game_options[game].append({"referees": refs, "cost": game.cost})
            return True

        for referee in referees_list:
            if referee.is_valid(game):
                referee.assign_game(game, "type not defined yet")
                self.all_options(game, referees_list)
                referee.undo_assign_game(game, "type not defined yet")

        return False

    def game_options(self, from_day, to_day, limit=None):
        # returns all the combinations of referees on a range of days with it's total cost

        if not (to_day >= from_day):
            raise Exception("to_day ({}) must be equal or higher than from_day ({})".format(to_day, from_day))

        games = [game for sublist in [nba.games[i] for i in range(from_day, to_day + 1)] for game in sublist]
        city_games = list(set([game.home.city for game in games]))

        for game in games:
            self.list_game_options[game] = []

            referee_list = self.nba.order_costs(game)[:limit]  # limitado a 'limit' arbitrariamente
            self.all_options(game, referee_list)

            self.list_game_options[game].sort(key=lambda x: x["cost"], reverse=False)

    def old_run(self, day, num_game):
        print("Day: {} Num_Game: {}".format(day, num_game))

        if day >= 178:  # END CONDITION
            return True

        if day not in self.nba.games or num_game > len(nba.games[day]):  # SOME DAYS DON'T HAVE GAMES
            print("Day don't have games or limit reached")
            # update refs
            self.nba.update_all_refs()
            if self.run(day + 1, 1):
                return True
            else:
                self.nba.revert_all_refs()
                return False
        else:
            game = nba.games[day][num_game - 1]
            self.set_referees(game)
            return True

            if game not in self.list_game_options:
                self.game_options(day, day, limit=50)

            for option in self.list_game_options[game]:
                print(option)

                all_valid = True
                for ref_id in option["referees"]:
                    ref = self.nba.referees[ref_id]
                    if not ref.is_valid(game):
                        all_valid = False
                        break

                if all_valid:
                    print("Asigned: {}".format(option))

                    for ref_id in option["referees"]:
                        ref = self.nba.referees[ref_id]
                        ref.assign_game(game, "type not used yet")  # IF VALID: ASSIGN

                    if self.run(day, num_game + 1):
                        return True
                    else:
                        print("Back")
                        for ref_id in option["referees"]:
                            ref = self.nba.referees[ref_id]
                            ref.undo_assign_game(game, "type not defined yet")

            return False
            print("No more options")
        return False

    def run(self, day, num_game):
        #print("day {}, numgame {}".format(day, num_game))
        if day >= 178:  # 178: END CONDITION
            print(self.reused)
            print(self.assigned)
            return True

        if day not in nba.games:  # SOME DAYS DON'T HAVE GAMES
            self.nba.update_all_refs(day)
            return self.run(day + 1, 1)

        game = self.nba.games[day][num_game - 1]
        refs = self.nba.order_costs(game)

        for ref in refs:
            if ref.is_valid(game):
                if ref.refgames and ref.current_city != ref.home:
                    self.reused += 1
                    #print(game.day - ref.refgames[-1].day)

                better_before = ref.better_before(game)
                if better_before:
                    pass
                    #print("mejor mandarlo antes")

                ref.assign_game(game, "type")  # IF VALID: ASSIGN
                self.assigned += 1

                if not game.has_all_refs():
                    if self.run(day, num_game):  # STAY ON THIS DAY and GAME
                        return True
                else:
                    if num_game >= len(nba.games[day]):  # IF LAST GAME
                        self.nba.update_all_refs(day)
                        if self.run(day + 1, 1):  # GO TO NEXT DAY
                            return True
                        print("revert refs")
                        # revert_all_refs()
                        #return False
                    else:
                        if self.run(day, num_game + 1):  # GO TO NEXT GAME
                            return True

                self.assigned -= 1
                print("undo")
                ref.undo_assign_game(game, "type")
        return False

def export_game_days(nba):
    with open("games-days.txt", "w") as day_games:
        for i in range(1, 178):
            if i in nba.games:
                day_str = "{0} DAY {1} {0}\n".format("-"*15, i)
                print(day_str, end="")
                day_games.write(day_str)

                for g, game in enumerate(nba.games[i]):
                    if not game.referees:
                        return

                    refs = [r.id for r in game.referees]

                    string = "Game {}: {}; Channel: {}\n".format(g + 1, refs, game.channel and game.channel.name)
                    print(string, end="")
                    day_games.write(string)

def export_refs_info(nba):
    refs = [r for r in nba.referees.values()]
    refs.sort(key=lambda x: len(set(x.timeline)), reverse=False)
    with open("refs-info.txt", "w") as refs_info:
        for ref in refs:
            string = "ID: {0.id}\n" \
                     "Home: {0.home.city_name}\n" \
                     "Dif Cities: {1}\n" \
                     "Cities: {2}\n\n".format(ref, len(set(ref.timeline)), set(map(lambda x: x.city, ref.timeline)))
            print(string, end="")
            refs_info.write(string)

def create_history(nba):
    with open("history.csv", "w") as csvfile:

        fieldnames = ['Ref ID'] + [i for i in range(1, 178)]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for id, ref in nba.referees.items():
            write = {"Ref ID": id}

            i_game = 0
            for day in range(1, 178):
                value = ""
                if i_game < len(ref.refgames) and day == ref.refgames[i_game].day:
                    value = "game"
                    i_game += 1

                if i_game + 1 < len(ref.refgames):
                    dif = ref.refgames[i_game + 1].day - ref.refgames[i_game].day
                    if 2 <= dif <= 3 and day > ref.refgames[i_game].day:
                        value = "waiting"

                write[day] = value

            writer.writerow(write)


if __name__ == "__main__":
    nba = NBA()

    print("Cargando seeds")
    nba.seed_locations("datos/locations.csv")
    nba.seed_games("datos/games.csv")
    nba.seed_distances("datos/distances (mi & km).csv")
    nba.seed_flight_costs("datos/flight costs.csv")
    nba.seed_referees("datos/referees.csv")
    print("Seeds terminado")

    bk = Backtrack(nba)
    #bk.game_options(1, 1, limit=30)
    bk.run(1, 1)

    #export_game_days(nba)
    #export_refs_info(nba)
    create_history(nba)
