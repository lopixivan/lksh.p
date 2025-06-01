import requests
import time

start_time = time.time()
url_base = "https://lksh-enter.ru"
token = "d5a7cbe4bc04dee2c75d468386bacc779642de644b98bf1726a1f45de76ba049"
h = {
    "Authorization": token
}
mas_id_players = []
list_of_players = []
mas_id_teams = []
mas_of_match = []
sl_of_goals = {}
sl_of_id_players_teams = {}
pointer_to_id_team = {}
pointer_from_name_to_team_id = {}


def get_an_teams():
    global mas_id_players, mas_id_teams, mas_of_match, pointer_to_id_team
    global sl_of_id_players_teams, pointer_from_name_to_team_id

    url = url_base + "/teams"
    r = requests.get(url, headers=h)
    if r.status_code == 200:
        r1 = r.json()

        for u in r1:
            pointer_from_name_to_team_id[u['name']] = u['id']
            mas_id_players += [i for i in u["players"]]
            mas_id_teams.append(u["id"])
            for player in u["players"]:
                if str(player) in sl_of_id_players_teams:
                    sl_of_id_players_teams[str(player)].append(u["id"])
                else:
                    sl_of_id_players_teams[str(player)] = [u["id"]]

    mas_of_match = [[0] * len(mas_id_teams) for _ in range(len(mas_id_teams))]
    pointer_to_id_team = {str(mas_id_teams[i]): i for i in range(len(mas_id_teams))}
    mas_id_players = set(mas_id_players)


def name_surname(r1):
    name = r1["name"]
    surname = r1['surname']
    return f"{name} {surname}".strip() if surname else name


def get_id_player():
    global list_of_players, start_time
    url = url_base + "/players/"

    for i in mas_id_players:
        r = requests.get(url + str(i), headers=h)

        if r.status_code == 429:
            
            time.sleep((60 - (time.time() - start_time))%60)
            start_time = time.time()
            r = requests.get(url + str(i), headers=h)

        if r.status_code == 200:
            r1 = r.json()
            list_of_players.append(name_surname(r1))

    list_of_players.sort()


def print_list_players():
    for i in list_of_players:
        print(i)


def fill_goals():
    global mas_of_match, sl_of_goals
    url = url_base + "/matches"
    r = requests.get(url, headers=h)

    if r.status_code == 200:
        matches = r.json()
        for match in matches:
            s_f_team = match['team1_score']
            s_s_team = match['team2_score']
            id_f_team = str(match['team1'])
            id_s_team = str(match['team2'])

            if id_f_team not in sl_of_goals:
                sl_of_goals[id_f_team] = [0, 0, 0]
            if id_s_team not in sl_of_goals:
                sl_of_goals[id_s_team] = [0, 0, 0]

            if s_f_team > s_s_team:
                sl_of_goals[id_f_team][0] += 1
                sl_of_goals[id_s_team][1] += 1
            elif s_f_team < s_s_team:
                sl_of_goals[id_f_team][1] += 1
                sl_of_goals[id_s_team][0] += 1

            sl_of_goals[id_f_team][2] += (s_f_team - s_s_team)
            sl_of_goals[id_s_team][2] += (s_s_team - s_f_team)

            idx1 = pointer_to_id_team[id_f_team]
            idx2 = pointer_to_id_team[id_s_team]
            mas_of_match[idx1][idx2] += 1
            mas_of_match[idx2][idx1] += 1


def ans_versus(id_player_1, id_player_2):
    if str(id_player_1) not in sl_of_id_players_teams or str(id_player_2) not in sl_of_id_players_teams:
        print(0)
    else:
        q_of_plays = 0
        for team1 in sl_of_id_players_teams[str(id_player_1)]:
            for team2 in sl_of_id_players_teams[str(id_player_2)]:
                idx1 = pointer_to_id_team[str(team1)]
                idx2 = pointer_to_id_team[str(team2)]
                q_of_plays += mas_of_match[idx1][idx2]
        print(q_of_plays)


def ans_stats(team_name):
    if team_name not in pointer_from_name_to_team_id:
        print(0, 0, 0)
    else:
        team_id = str(pointer_from_name_to_team_id[team_name])
        if team_id in sl_of_goals:
            stats = sl_of_goals[team_id]
            print(stats[0], stats[1], stats[2])
        else:
            print(0, 0, 0)


def main():
    get_an_teams()
    get_id_player()
    print_list_players()
    fill_goals()

    while True:
        try:
            input_line = input().strip()
            if not input_line:
                continue

            mas_of_request = input_line.split()
            if not mas_of_request:
                continue

            if mas_of_request[0] == "stats?" and len(mas_of_request) > 1:
                team_name = ' '.join(mas_of_request[1:]).strip('"\'')
                ans_stats(team_name)
            elif mas_of_request[0] == "versus?" and len(mas_of_request) == 3:
                try:
                    player1_id = int(mas_of_request[1])
                    player2_id = int(mas_of_request[2])
                    ans_versus(player1_id, player2_id)
                except ValueError:
                    print(0)
            else:
                print("Такой команды нет!")
        except EOFError:
            break
        except Exception as e:
            print(f"Ошибка: {e}")


if __name__ == '__main__':
    main()
