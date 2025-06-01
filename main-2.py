import requests
import time
from flask import Flask, jsonify, render_template_string, request
import threading
import datetime
import pickle
import os
import atexit
app = Flask(__name__)
#ttl 5 минут
CACHE_TTL = 300
last_update_time = 0
cache_lock = threading.Lock()
start_time = time.time()
url_base = "https://lksh-enter.ru"
token = "d5a7cbe4bc04dee2c75d468386bacc779642de644b98bf1726a1f45de76ba049"
h = {"Authorization": token}
mas_id_players = []
list_of_players = []
mas_id_teams = []
mas_of_match = []
sl_of_goals = {}
sl_of_id_players_teams = {}
pointer_to_id_team = {}
pointer_from_name_to_team_id = {}
CACHE_FILE = "cache_data.pkl"
def save_cache_to_disk():
    cache_data = {
        'mas_id_players': mas_id_players,
        'list_of_players': list_of_players,
        'mas_id_teams': mas_id_teams,
        'mas_of_match': mas_of_match,
        'sl_of_goals': sl_of_goals,
        'sl_of_id_players_teams': sl_of_id_players_teams,
        'pointer_to_id_team': pointer_to_id_team,
        'pointer_from_name_to_team_id': pointer_from_name_to_team_id,
        'last_update_time': last_update_time
    }
    try:
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(cache_data, f)
    except Exception as e:
        print(f"Ошибка(в течение сохранения кеша)!: {e}")

def load_cache_from_disk():
    global last_update_time, mas_id_players, list_of_players, mas_id_teams
    global mas_of_match, sl_of_goals, sl_of_id_players_teams
    global pointer_to_id_team, pointer_from_name_to_team_id
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'rb') as f:
                cache_data = pickle.load(f)
            mas_id_players = cache_data.get('mas_id_players', [])
            list_of_players = cache_data.get('list_of_players', [])
            mas_id_teams = cache_data.get('mas_id_teams', [])
            mas_of_match = cache_data.get('mas_of_match', [])
            sl_of_goals = cache_data.get('sl_of_goals', {})
            sl_of_id_players_teams = cache_data.get('sl_of_id_players_teams', {})
            pointer_to_id_team = cache_data.get('pointer_to_id_team', {})
            pointer_from_name_to_team_id = cache_data.get('pointer_from_name_to_team_id', {})
            last_update_time = cache_data.get('last_update_time', 0)
            return True
        except Exception as e:
            print(f"Ошибка(в течение загрузки кэша)!: {e}")
    return False


def login_to_api():
    login_url = url_base + "/login"
    response = requests.post(login_url, headers=h)
    return response.status_code == 200


def update_cache():
    global last_update_time, mas_id_players, list_of_players, mas_id_teams
    global mas_of_match, sl_of_goals, sl_of_id_players_teams
    global pointer_to_id_team, pointer_from_name_to_team_id
    old_data = {
        'mas_id_players': mas_id_players.copy(),
        'list_of_players': list_of_players.copy(),
        'mas_id_teams': mas_id_teams.copy(),
        'mas_of_match': [row[:] for row in mas_of_match] if mas_of_match else [],
        'sl_of_goals': sl_of_goals.copy(),
        'sl_of_id_players_teams': {k: v[:] for k, v in sl_of_id_players_teams.items()},
        'pointer_to_id_team': pointer_to_id_team.copy(),
        'pointer_from_name_to_team_id': pointer_from_name_to_team_id.copy()
    }

    try:
        mas_id_players = []
        list_of_players = []
        mas_id_teams = []
        mas_of_match = []
        sl_of_goals = {}
        sl_of_id_players_teams = {}
        pointer_to_id_team = {}
        pointer_from_name_to_team_id = {}
        get_an_teams()
        get_id_player()
        fill_goals()
        last_update_time = time.time()
        save_cache_to_disk()
        return True
    except Exception as e:
        print(f"Ошибка!: {e}.Попытка востановить")
        mas_id_players = old_data['mas_id_players']
        list_of_players = old_data['list_of_players']
        mas_id_teams = old_data['mas_id_teams']
        mas_of_match = old_data['mas_of_match']
        sl_of_goals = old_data['sl_of_goals']
        sl_of_id_players_teams = old_data['sl_of_id_players_teams']
        pointer_to_id_team = old_data['pointer_to_id_team']
        pointer_from_name_to_team_id = old_data['pointer_from_name_to_team_id']
        return False


def check_and_update_cache():
    if time.time() - last_update_time > CACHE_TTL:
        with cache_lock:
            if time.time() - last_update_time > CACHE_TTL:
                print("Обновление")
                if update_cache():
                    print("Кэш успешно обновлен")
                else:
                    print("Используется сохраненный кэш")
    else:
        try:
            requests.get(url_base + "/teams", headers=h, timeout=2)
        except:
            print("API недоступен, используется сохраненный кэш")
def get_an_teams():
    global mas_id_players, mas_id_teams, mas_of_match, pointer_to_id_team
    global sl_of_id_players_teams, pointer_from_name_to_team_id

    url = url_base + "/teams"
    r = requests.get(url, headers=h)
    if r.status_code == 200:
        r1 = r.json()
        for u in r1:
            pointer_from_name_to_team_id[u['name']] = u['id']
            mas_id_players.extend(u["players"])
            mas_id_teams.append(u["id"])
            for player in u["players"]:
                player_str = str(player)
                if player_str in sl_of_id_players_teams:
                    sl_of_id_players_teams[player_str].append(u["id"])
                else:
                    sl_of_id_players_teams[player_str] = [u["id"]]
    mas_of_match = [[0] * len(mas_id_teams) for _ in range(len(mas_id_teams))]
    pointer_to_id_team = {str(team_id): idx for idx, team_id in enumerate(mas_id_teams)}


def name_surname(r1):
    name = r1["name"]
    surname = r1['surname']
    return f"{name} {surname}".strip() if surname else name


def get_id_player():
    global list_of_players
    url = url_base + "/players/"

    for i in set(mas_id_players):
        try:
            r = requests.get(url + str(i), headers=h, timeout=5)

            if r.status_code == 429:
                time.sleep(60 - (time.time() - start_time) % 60)
                r = requests.get(url + str(i), headers=h, timeout=5)

            if r.status_code == 200:
                r1 = r.json()
                list_of_players.append(name_surname(r1))
        except:
            continue

    list_of_players.sort()


def fill_goals():
    global mas_of_match, sl_of_goals
    url = url_base + "/matches"
    r = requests.get(url, headers=h, timeout=5)

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

            if id_f_team in pointer_to_id_team and id_s_team in pointer_to_id_team:
                idx1 = pointer_to_id_team[id_f_team]
                idx2 = pointer_to_id_team[id_s_team]
                mas_of_match[idx1][idx2] += 1
                mas_of_match[idx2][idx1] += 1


@app.route('/stats')
def stats_endpoint():
    team_name = request.args.get('team_name', '').strip('"\'')
    check_and_update_cache()

    if team_name not in pointer_from_name_to_team_id:
        return jsonify({"wins": 0, "losses": 0, "goal_difference": 0})

    team_id = str(pointer_from_name_to_team_id[team_name])
    if team_id in sl_of_goals:
        stats = sl_of_goals[team_id]
        return jsonify({
            "wins": stats[0],
            "losses": stats[1],
            "goal_difference": stats[2]
        })
    return jsonify({"wins": 0, "losses": 0, "goal_difference": 0})


@app.route('/versus')
def versus_endpoint():
    try:
        player1_id = int(request.args.get('player1_id', 0))
        player2_id = int(request.args.get('player2_id', 0))
    except ValueError:
        return jsonify({"matches": 0})

    check_and_update_cache()

    p1_str = str(player1_id)
    p2_str = str(player2_id)

    if p1_str not in sl_of_id_players_teams or p2_str not in sl_of_id_players_teams:
        return jsonify({"matches": 0})

    q_of_plays = 0
    for team1 in sl_of_id_players_teams[p1_str]:
        t1_str = str(team1)
        if t1_str not in pointer_to_id_team:
            continue
        idx1 = pointer_to_id_team[t1_str]
        for team2 in sl_of_id_players_teams[p2_str]:
            t2_str = str(team2)
            if t2_str not in pointer_to_id_team:
                continue
            idx2 = pointer_to_id_team[t2_str]
            q_of_plays += mas_of_match[idx1][idx2]

    return jsonify({"matches": q_of_plays})


@app.route('/goals')
def goals_endpoint():
    try:
        player_id = int(request.args.get('player_id', 0))
    except ValueError:
        return jsonify([])

    check_and_update_cache()

    goals = []
    url = url_base + "/matches"

    try:
        r = requests.get(url, headers=h, timeout=5)
        if r.status_code == 200:
            matches = r.json()
            for match in matches:
                try:
                    goals_url = f"{url_base}/goals?match_id={match['id']}"
                    goals_r = requests.get(goals_url, headers=h, timeout=3)
                    if goals_r.status_code == 200:
                        match_goals = goals_r.json()
                        for goal in match_goals:
                            if goal['player'] == player_id:
                                goals.append({
                                    "match": match['id'],
                                    "time": goal['minute']
                                })
                except:
                    continue
    except:
        pass

    return jsonify(goals)


@app.route('/front/stats')
def front_stats():
    check_and_update_cache()
    teams = list(pointer_from_name_to_team_id.keys())
    team_stats = {}

    for team_name in teams:
        team_id = pointer_from_name_to_team_id.get(team_name)
        if team_id and str(team_id) in sl_of_goals:
            stats = sl_of_goals[str(team_id)]
            team_stats[team_name] = {
                'wins': stats[0],
                'losses': stats[1],
                'diff': stats[2]
            }
        else:
            team_stats[team_name] = {'wins': 0, 'losses': 0, 'diff': 0}

    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Stats</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>Статистика команд</h1>
            <table>
                <tr>
                    <th>Название команды</th>
                    <th>Победы</th>
                    <th>Поражения</th>
                    <th>Разница забитых и пропущенных голов</th>
                </tr>
                {% for team in teams %}
                <tr>
                    <td>{{ team }}</td>
                    <td>{{ team_stats[team]['wins'] }}</td>
                    <td>{{ team_stats[team]['losses'] }}</td>
                    <td>{{ team_stats[team]['diff'] }}</td>
                </tr>
                {% endfor %}
            </table>
        </body>
        </html>
    ''', teams=teams, team_stats=team_stats)


@app.route('/front/versus')
def front_versus():
    check_and_update_cache()
    return render_template_string('''
        <!DOCTYPE html>
<html>
<head>
    <title>Versus</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        form { margin-bottom: 20px; }
        .result { font-weight: bold; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>Статистика игроков</h1>
    <form onsubmit="getVersus(); return false;">
        ID первого игрока: <input type="number" id="player1" required><br>
        ID второго игрока: <input type="number" id="player2" required><br>
        <button type="submit">Получить статистику</button>
    </form>
    <div id="result" class="result"></div>

    <script>
        async function getVersus() {
            const player1Id = document.getElementById('player1').value;
            const player2Id = document.getElementById('player2').value;
            
            try {
                const response = await fetch(`/versus?player1_id=${player1Id}&player2_id=${player2Id}`);
                
                if (!response.ok) {
                    throw new Error(`Ошибка сервера: ${response.status}`);
                }
                
                const data = await response.json();
                document.getElementById('result').innerText = 
                    `Игроки ${player1Id} и ${player2Id} сразились друг против друга в ${data.matches} матчах`;
            } catch (error) {
                console.error("Ошибка запроса:", error);
                document.getElementById('result').innerText = "Ошибка при получении данных!";
            }
        }
    </script>
</body>
</html>
    ''')



atexit.register(save_cache_to_disk)

if __name__ == '__main__':
    if os.path.exists(CACHE_FILE):
        print("Загрузка кэша с диска...")
        load_cache_from_disk()
    if login_to_api():
        print("Успешный вход в API, сохраненный кэш не используется")
        update_cache()
    else:
        print("Ошибка входа в API, используется сохраненный кэш")
    app.run(host='0.0.0.0', port=5000)
