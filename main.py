import clases

if __name__ == "__main__":
    nba = clases.NBA()

    print("Cargando seeds")
    nba.seed_locations("datos/locations.csv")
    nba.seed_games("datos/games.csv")
    nba.seed_distances("datos/distances (mi & km).csv")
    nba.seed_flight_costs("datos/flight costs.csv")
    nba.seed_referees("datos/referees.csv")
    print("Seeds terminado")

    for key in nba.teams:
        print(key)
    print("-------------")
    for game in nba.games:
        print(game)
    print("-------------")
    for id, referee in nba.referees.items():
        print(vars(referee))