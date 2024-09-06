import random, time
from data import valid_scores, small_seed, big_seed, match_finder, rank_tier


def sortseed(c, conn):
    seed_message = "hi"
    t_format = None

    c.execute("DROP TABLE participants")
    c.execute("CREATE TABLE participants (seed INT PRIMARY KEY, team_id INT, captain INT, score TEXT, round TEXT, pool INT, "
              "placement INT, bracket TEXT)")
    conn.commit()

    c.execute("SELECT user_id, team_name, captain, rank FROM teams WHERE checked_in = 1")
    fetch = c.fetchall()
    entrants = []
    for i in fetch:
        (user_id, team_name, captain, rank) = i
        entered = False
        for i2 in entrants:
            if i2[0] == team_name:
                i2[2] += rank
                i2[3] += 1
                entered = True
        if entered is False:
            entrants.append([team_name, captain, rank, 1])

    remover = []
    for i in entrants:
        if i[3] != 4:
            remover.append(i)
    for i in remover:
        entrants.remove(i)
    participants = sorted(entrants, key=lambda l: l[1])
    print(participants)

    if len(participants) <= 3:
        seed_message = "Meew! Looks like we only have " + str(len(participants)) + " participants. Shame."

    elif 3 < len(participants) <= 11:
        bye_entrants = 6
        t_format = "z_fourstart"
        seed_message = "Meew! We have " + str(len(participants)) + " entrants. We're going to play a Round Robin Pool!"
        if 6 < len(participants) <= 11:
            seed_message = "Meew! We have " + str(len(participants)) + " entrants. We're going to play a PaP DE bracket!"
            bye_entrants = 11
            t_format = "z_sevenstart"

        pool_value = 1
        for i in participants:
            c.execute("INSERT INTO participants VALUES (?, ?, ?, NULL, NULL, 1, 0, NULL)", (pool_value, i[0], i[1]))
            conn.commit()
            pool_value += 1
        while pool_value <= bye_entrants:
            c.execute("INSERT INTO participants VALUES (:pv, 'bye', NULL, NULL, 'bye', 1, -1, NULL)", {"pv": pool_value})
            conn.commit()
            pool_value += 1

    elif 11 < len(participants) < 25:

        pool_numbers = [1, 2, 3, 4, 4, 3, 2, 1]
        pool_value = 1
        for i in participants:
            this_pool = pool_numbers[((pool_value % 8) - 1)]
            c.execute("INSERT INTO participants VALUES (?, ?, ?, NULL, NULL, ?, 0, NULL)", (pool_value, i[0], i[1], this_pool))
            conn.commit()
            pool_value += 1

        while pool_value < 25:
            this_pool = pool_numbers[((pool_value % 8) - 1)]
            c.execute("INSERT INTO participants VALUES (?, 'bye', NULL, NULL, 'bye', ?, -1, NULL)", (pool_value, this_pool))
            conn.commit()
            pool_value += 1
        seed_message = "Meew! The players have been seeded! We have " + str(len(participants)) + " entrants!"
        t_format = "z_smalltart"

    else:
        pool_numbers = [1, 2, 3, 4, 5, 6, 7, 8, 8, 7, 6, 5, 4, 3, 2, 1]
        pool_value = 1
        for i in participants:
            this_pool = pool_numbers[((pool_value % 16) - 1)]
            c.execute("INSERT INTO participants VALUES (?, ?, ?, NULL, NULL, ?, 0, NULL)", (pool_value, i[0], i[1], this_pool))
            conn.commit()
            pool_value += 1

        while pool_value < 49:
            this_pool = pool_numbers[((pool_value % 16) - 1)]
            c.execute("INSERT INTO participants VALUES (?, 'bye', NULL, 'bye', ?, -1, NULL)",
                      (pool_value, this_pool))
            conn.commit()
            pool_value += 1
            seed_message = "Meew! The players have been seeded! We have " + str(len(participants)) + " entrants!"
        t_format = "z_bigstart"

    return seed_message, t_format


def poolstart(c, conn, guild, tourney_format):
    c.execute("DROP TABLE IF EXISTS pools")
    c.execute("CREATE TABLE pools AS SELECT * FROM " + tourney_format)
    conn.commit()

    c.execute("SELECT seed FROM participants WHERE round = 'bye'")
    bye_teams = c.fetchall()

    for i in bye_teams:
        (byes,) = i
        c.execute("UPDATE pools SET score = -1, team1 = 'bye' WHERE team1 = :b", {"b": byes})
        c.execute("UPDATE pools SET score = -1, team2 = 'bye' WHERE team2 = :b", {"b": byes})
    conn.commit()

    if tourney_format == "z_sevenstart":
        c.execute("UPDATE pools SET score = 0")
        conn.commit()
        pap_bye = True
        while pap_bye:
            c.execute(
                "SELECT round, team1, team2, path1, path2 FROM pools WHERE (team1 = 'bye' OR team2 = 'bye') AND score = 0")
            fetch = c.fetchall()
            print(fetch)
            if fetch:
                for i in fetch:
                    (round, team1, team2, path1, path2) = i
                    c.execute("UPDATE pools SET score = -1 WHERE round = :r", {"r": round})
                    if team1 == "bye":
                        winner = team2
                    else:
                        winner = team1
                    c.execute("UPDATE pools SET team2 = team1, team1 = ? WHERE round = ?", (winner, path1))

                    if path2 == "pap1":
                        c.execute("UPDATE pools SET team1 = 'bye' WHERE round = 'pap1'")
                        c.execute("UPDATE pools SET team2 = 'bye' WHERE round = 'pap3'")
                    elif path2 == "pap2":
                        c.execute("UPDATE pools SET team2 = 'bye' WHERE round = 'pap1'")
                        c.execute("UPDATE pools SET team1 = 'bye' WHERE round = 'pap2'")
                        path = "pap1"
                    elif path2 == "pap3":
                        c.execute("UPDATE pools SET team2 = 'bye' WHERE round = 'pap2'")
                        c.execute("UPDATE pools SET team1 = 'bye' WHERE round = 'pap3'")
                        path = "pap2"
                    else:
                        c.execute("UPDATE pools SET team2 = team1, team1 = 'bye' WHERE round = :p2", {"p2": path2})
                conn.commit()
            else:
                pap_bye = False

    c.execute("SELECT seed FROM participants WHERE round IS NULL")
    fetch = c.fetchall()
    rounds = []
    for i in fetch:
        (seeds,) = i
        c.execute("SELECT round FROM pools WHERE (team1 = :s AND score = 0) OR (team2 = :s AND score = 0)", {"s": seeds})
        fetch2 = c.fetchone()
        (first_round,) = fetch2
        rounds.append(first_round)
        c.execute("UPDATE participants SET round = ? WHERE seed = ?", (first_round, seeds))
    conn.commit()
    rounds = list(dict.fromkeys(rounds))
    (assign_list, start_message) = match_finder(c, guild, rounds)

    return start_message, assign_list


def poolseed(c, conn, tourney_format):
    poolseed_message = "Meew! The seeds have successfully been planted!"
    seed_counter = 0
    pool_counter = []
    three_tie = False
    if tourney_format == "z_bigstart":
        pool_counter = [1, 2, 3, 4, 5, 6, 7, 8]
        seeds = big_seed
    elif tourney_format == "z_smallstart":
        pool_counter = [1, 2, 3, 4]
        seeds = small_seed
    elif tourney_format == "z_fourstart":
        poolseed_message = "Meew! 4-6 RR done!"
        pool_counter = [1]
    elif tourney_format == "z_sevenstart":
        c.execute("UPDATE participants SET pool = 2 WHERE round = '#pap'")
        conn.commit()
        poolseed_message = "Meew! 7-11 Pool sorted!"
        pool_counter = [2]

    for i in pool_counter:
        score_points = 0
        while score_points < 16:
            c.execute("SELECT seed, placement FROM participants WHERE pool = ? AND placement = ?", (i, score_points))
            fetch = c.fetchall()
            if len(fetch) == 2:
                (tie1, place1) = fetch[0]
                (tie2, place2) = fetch[1]

                place1 += 1
                c.execute("SELECT team1, team2, score FROM pools WHERE (team1 = ? AND team2 = ?) "
                          "OR (team2 = ? AND team1 = ?)", (tie1, tie2, tie1, tie2))
                tie = c.fetchone()
                (team1, team2, score) = tie
                score_r = score[::-1]
                if int(score) > int(score_r):
                    c.execute("UPDATE participants SET placement = ? WHERE seed = ?", (place1, team1))
                else:
                    c.execute("UPDATE participants SET placement = ? WHERE seed = ?", (place1, team2))

            elif len(fetch) == 3:
                (tie1, place1) = fetch[0]
                (tie2, place2) = fetch[1]
                (tie3, place3) = fetch[2]
                poolseed_message = "Meew! There is a 3-way tie between Team " + str(tie1) + ", " + str(tie2) + ", " \
                                   + str(tie3) + " - Pool " + str(i) + ". Fix it!"
                three_tie = True
                break
            conn.commit()
            score_points += 3

        if three_tie is False:
            if tourney_format == "z_fourstart":
                c.execute("SELECT captain, placement FROM participants WHERE placement != -1")
                fetch = c.fetchall()
                fetch.sort(key=lambda tup: tup[1], reverse=True)
                placed = 1
                for i2 in fetch:
                    (captain, poolp) = i2
                    c.execute("UPDATE participants SET round = '#" + str(placed) + "' WHERE captain = :cpt", {"cpt": captain})
                    placed += 1
            elif tourney_format == "z_sevenstart":
                c.execute("SELECT captain, placement FROM participants WHERE placement != -1 AND round = '#pap'")
                fetch = c.fetchall()
                fetch.sort(key=lambda tup: tup[1], reverse=True)
                placed = 9
                for i2 in fetch:
                    (captain, poolp) = i2
                    c.execute("UPDATE participants SET round = '#" + str(placed) + "' WHERE captain = :cpt",
                              {"cpt": captain})
                    placed += 1
            else:
                c.execute("SELECT seed, placement FROM participants WHERE pool = :pc",  {"pc": i})
                pool = c.fetchall()
                pool.sort(key=lambda tup: tup[1], reverse=True)
                for i2 in pool:
                    (team, place) = i2
                    c.execute("UPDATE participants SET bracket = ? WHERE seed = ?", (seeds[seed_counter], team))
                    seed_counter += 1
            conn.commit()

    return poolseed_message


def papstart(c, conn, guild):
    papstart_message = "Meew! The brackets are set!"
    c.execute("DROP TABLE IF EXISTS pap")
    c.execute("CREATE TABLE pap AS SELECT * FROM z_papstart")
    conn.commit()

    c.execute("SELECT seed, round, bracket FROM participants")
    fetch = c.fetchall()
    for i in fetch:
        (seed, round, seeding) = i
        if round != "bye":
            c.execute("UPDATE pap SET team1 = ? WHERE team1 = ?", (seed, seeding))
            c.execute("UPDATE pap SET team2 = ? WHERE team2 = ?", (seed, seeding))
    c.execute("UPDATE pap SET team1 = 'bye' WHERE team1 LIKE 's%'")
    c.execute("UPDATE pap SET team2 = 'bye' WHERE team2 LIKE 's%'")
    conn.commit()

    pap_bye = True
    while pap_bye:
        c.execute(
            "SELECT round, team1, team2, path1, path2 FROM pap WHERE (team1 = 'bye' OR team2 = 'bye') AND score = 0")
        fetch = c.fetchall()
        if fetch:
            for i in fetch:
                (round, team1, team2, path1, path2) = i
                c.execute("UPDATE pap SET score = -1 WHERE round = :r", {"r": round})

                if path1.startswith("#") is False:
                    if team1 == "bye":
                        winner = team2
                    else:
                        winner = team1

                    c.execute("UPDATE pap SET team2 = team1, team1 = ? WHERE round = ?", (winner, path1))
                    c.execute("UPDATE pap SET team2 = team1, team1 = 'bye' WHERE round = :p2", {"p2": path2})
            conn.commit()
        else:
            pap_bye = False

    c.execute("SELECT round, team1, team2 FROM pap WHERE score != '-1'")
    fetch = c.fetchall()
    for i in fetch:
        (round, team1, team2) = i
        if team1 != "bye" or team1 is not None:
            c.execute("UPDATE participants SET round = ? WHERE seed = ?", (round, team1))
        if team2 != "bye" or team2 is not None:
            c.execute("UPDATE participants SET round = ? WHERE seed = ?", (round, team2))
    conn.commit()

    rounds = []
    c.execute("SELECT round FROM participants WHERE round != 'bye'")
    fetch = c.fetchall()
    for i in fetch:
        (round,) = i
        rounds.append(round)
    rounds = list(dict.fromkeys(rounds))
    (assign_list, status_message) = match_finder(c, guild, rounds)
    papstart_message += status_message

    return assign_list, papstart_message


def result(c, conn, tourney_format):
    result_message = "Meew! Thus concludes our tournament! The results are in:"
    tier_list = []
    c.execute("SELECT MAX(tourney_id) FROM tournaments")
    fetch = c.fetchone()
    (tourney_id,) = fetch
    tourney_id += 1
    today = time.strftime('%Y-%m-%d %H:%M:%S')
    c.execute("SELECT team_id, captain, round FROM participants WHERE round != 'bye'")
    fetch = c.fetchall()
    entrants = len(fetch)
    c.execute("INSERT INTO tournaments VALUES(?, ?, ?)", (tourney_id, entrants, today))
    today_short = today.replace("-", "")[:8]
    c.execute("CREATE TABLE a_participants_" + today_short + " AS SELECT * FROM participants")
    c.execute("CREATE TABLE a_pools_" + today_short + " AS SELECT * FROM pools")
    if tourney_format == "z_smallstart" or tourney_format == "z_bigstart":
        c.execute("CREATE TABLE a_pap_" + today_short + " AS SELECT * FROM pap")

    fetch = sorted(fetch, key=lambda tup: int(tup[2][1:]))
    for i in fetch:
        (team_id, captain, round) = i
        result_message += "\nTeam " + team_id + " placed: " + round + "!"

        c.execute ("SELECT user_id FROM teams WHERE captain = :cpt AND checked_in = 1", {"cpt": captain})
        fetch2 = c.fetchall()
        for i2 in fetch2:
            (user_id,) = i2
            c.execute("INSERT INTO tourney_played VALUES (?, ?, ?, ?, ?)", (user_id, tourney_id, entrants, int(round[1:]), today))
            c.execute("SELECT * FROM tourney_played WHERE user_id = :uid", {"uid": user_id})
            fetch3 = c.fetchall()
            fetch3.sort(key=lambda tup: tup[1], reverse=True)
            fetch3 = fetch3[:5]
            add_rank = 0
            divisor = 0
            for i3 in fetch3:
                (user_id, tourney_id, entrants, placement, date) = i3
                inverse = entrants - placement + 1
                inverse = inverse / entrants * 100
                add_rank += inverse
                divisor += 1
            rank = add_rank / divisor
            c.execute("UPDATE users SET tournaments = tournaments + 1, last_played = 0, rank = ? WHERE user_id = ?", (rank, user_id))
            print(rank)
            tier = rank_tier(rank)
            tier_list.append((user_id, tier))

    result_message += "\nMeew! The results have now been updated! Thanks for playing and enjoy your new tiers, everyone!"

    c.execute("UPDATE users SET last_played = last_played + 1")
    c.execute("DELETE FROM users WHERE last_played = 6")
    conn.commit()

    return result_message, tier_list


def rps(guild, user_id):
    rps_message = "Meew! You have no opponent at the moment!"
    user = guild.get_member(user_id)
    user_roles = user.roles
    for i in user_roles:
        if i.name.startswith("room"):
            role = i
            players = role.members
            rps_winner = random.choice(players)
            rps_message = "Plu! " + str(rps_winner)[:-5] + " gets to strike first!"
            break

    return rps_message


def random_starter():
    maps = [("SZ", "Humpback Pumptrack"), ("SZ", "Wahoo World"), ("SZ", "Mako Mart"), ("SZ", "Skipper Pavillion"),
            ("SZ", "Hotel Albacore"), ("TC", "Inkblot Art Academy"), ("TC", "Sturgeon Shipyard"),
            ("TC", "Startfish Mainstage"), ("TC", "Manta Maria"), ("TC", "Shellendorf Institute"),
            ("CB", "The Reef"), ("CB", "Piranha Pit"), ("CB", "Snapper Canal"), ("RM", "Musselforge Fitness"),
            ("RM", "Ancho-V Games"), ("RM", "Blackbelly Skatepark")]
    first_map = random.choice(maps)
    (mode, map) = first_map
    random_message = "Meew! You're starting on: " + mode + ", " + map + "!"
    return random_message


def score_c(c, conn, user_id, user_message):
    score_message = "hi"
    c.execute("SELECT score, round FROM participants WHERE captain = :uid", {"uid": user_id})
    fetch = c.fetchone()
    (scores, round) = fetch
    if scores is None:
        user_message = user_message.replace("!score ", "")
        if user_message == "!score":
            score_message = "Meew! You forgot to enter a score!"
        else:
            valid_score = False
            for i in valid_scores:
                if i == user_message:
                    valid_score = True
            if valid_score is False:
                score_message = "Meew! You did not enter a valid score!"
            else:
                c.execute("SELECT captain FROM participants WHERE round = :r", {"r": round})
                fetch = c.fetchall()
                for i in fetch:
                    (player_id,) = i
                    if player_id == user_id:
                        c.execute("UPDATE participants SET score = 'reported' WHERE captain = :pid",
                                  {"pid": player_id})
                    else:
                        c.execute("UPDATE participants SET score = ? WHERE captain = ?", (user_message, player_id))
                        score_message = "Meew! Is this score !correct or !wrong, <@" + str(player_id) + ">?"
                conn.commit()
    elif scores == "reported":
        score_message = "Meew! You already reported a score! Your opponent has to confirm or refute it."
    else:
        score_message = "Meew! You still have a score to confirm or refute!"

    return score_message


def wrong(c, conn, user_id):
    wrong_message = "hi"
    c.execute("SELECT score, round FROM participants WHERE captain = :uid", {"uid": user_id})
    fetch = c.fetchone()
    (score, round) = fetch
    if score is None:
        wrong_message = "Meew! You have no score to refute!"
    else:
        c.execute("UPDATE participants SET score = NULL WHERE round = :r", {"r": round})
        conn.commit()
        wrong_message = "Meew! You refuted the score. Please enter the correct one this time!"
    return wrong_message


def correct(c, conn, user_id, guild, pool_phase, tourney_format):
    correct_message = ""
    status_message = ""
    assign_list = []
    remove_list = []
    rounds = []
    done = False

    c.execute("SELECT seed, score, round FROM participants WHERE captain = :uid", {"uid": user_id})
    fetch = c.fetchone()
    (seed, score, round) = fetch
    if score is None:
        correct_message = "Meew! You have no score to confirm!"
    elif score == "reported":
        correct_message = "Meew! You are the one who reported the score, your opponent needs to either confirm or refute it!"
    else:
        score = score.replace("-", "")
        score_r = score[::-1]
        c.execute("SELECT captain FROM participants WHERE round = :r", {"r": round})
        fetch = c.fetchall()
        (remove1,) = fetch[0]
        (remove2,) = fetch[1]
        remove_list = [remove1, remove2]

        c.execute("SELECT team1, team2, path1, path2 FROM pools WHERE round = :r", {"r": round})
        fetch = c.fetchone()
        (t1, t2, p1, p2) = fetch
        if t1 == seed:
            c.execute("UPDATE pools SET score = ? WHERE round = ?", (score_r, round))
            correct_score = score_r
        else:
            c.execute("UPDATE pools SET score = ? WHERE round = ?", (score, round))
            correct_score = score

        if pool_phase or round.startswith("pap"):
            points1 = 0
            points2 = 0
            if int(correct_score) > int(correct_score[::-1]):
                points1 = 3
            else:
                points2 = 3

            teams = [(t1, points1, p1), (t2, points2, p2)]
            (status_message, rounds) = pool_correct(c, conn, teams)

        else:
                if int(correct_score) > int(correct_score[::-1]):
                    winner = t1
                    loser = t2
                else:
                    winner = t2
                    loser = t1

                if p2 == "reset":
                    if winner == t2:
                        c.execute("UPDATE participants SET score = Null, round = '#2' WHERE seed = :l", {"l": loser})
                        c.execute("UPDATE participants SET score = Null, round = '#1' WHERE seed = :w", {"w": winner})
                        conn.commit()
                        status_message = "Meew! The DE bracket is done, <@143345734530498560>!"
                        done = True

                    else:
                        p2 = '22'
                teams = [(winner, p1), (loser, p2)]
                if done is False:
                    (status_message, rounds) = bracket_correct(c, conn, teams, tourney_format)
        if rounds is not None:
            (assign_list, waiter_message) = match_finder(c, guild, rounds)
            status_message += waiter_message

    return correct_message, status_message, assign_list, remove_list


def pool_correct(c, conn, teams):
    status_message = ""
    rounds = []
    for i in teams:
        (team, points, path) = i
        if not path.startswith("#"):
            c.execute("SELECT * FROM pools WHERE round = :p", {"p": path})
            fetch = c.fetchone()
            (round, team1, team2, score, path1, path2) = fetch
            while score == "-1":
                if team1 == team:
                    path = path1
                else:
                    path = path2

                if path.startswith("#"):
                    break
                c.execute("SELECT * FROM pools WHERE round = :p", {"p": path})
                fetch = c.fetchone()
                (round, team1, team2, score, path1, path2) = fetch

        c.execute("UPDATE participants SET score = NULL, round = ?, placement = placement + ? WHERE seed = ?",
                  (path, points, team))
        conn.commit()

        if path.startswith("#"):
            c.execute("SELECT captain FROM participants WHERE seed = :t", {"t": team})
            fetch = c.fetchone()
            (team_id,) = fetch
            status_message += "\nMeew! You're done with your pool phase, <@" + str(team_id) + ">!"
            c.execute("SELECT round FROM pools WHERE score = 0")
            done = c.fetchone()
            if done is None:
                status_message += "\nMeew! Pools are done, <@143345734530498560>!"
        else:
            rounds.append(path)
    return status_message, rounds


def bracket_correct(c, conn, teams, tourney_format):
    if tourney_format == "z_sevenstart":
        tourney_table = "pools"
    else:
        tourney_format = "pap"
    status_message = ""
    rounds = []
    for i in teams:
        (team, path) = i
        if path.startswith("pap"):
            if path == "pap1":
                c.execute("UPDATE pools SET team1 = :t WHERE round = 'pap1'", {"t": team})
                c.execute("UPDATE pools SET team2 = :t WHERE round = 'pap3'", {"t": team})
                c.execute("SELECT score FROM pools WHERE round = 'pap1'")
                fetch = c.fetchone()
                (pap_score,) = fetch
                if pap_score == "-1":
                    path = '#pap'
                else:
                    rounds.append(path)
            elif path == "pap2":
                c.execute("UPDATE pools SET team2 = :t WHERE round = 'pap1'", {"t": team})
                c.execute("UPDATE pools SET team1 = :t WHERE round = 'pap2'", {"t": team})
                path = "pap1"
                rounds.append(path)
            elif path == "pap3":
                c.execute("UPDATE pools SET team2 = :t WHERE round = 'pap2'", {"t": team})
                c.execute("UPDATE pools SET team1 = :t WHERE round = 'pap3'", {"t": team})
                path = "pap2"
            conn.commit()

        else:
            if not path.startswith("#"):
                c.execute("SELECT * FROM " + tourney_table + " WHERE round = :p", {"p": path})
                fetch = c.fetchone()
                (round, team1, team2, score, path1, path2) = fetch

                while score == "-1":
                    c.execute("UPDATE " + tourney_table + " SET team2 = team1, team1 = ? WHERE round = ?", (team, path))
                    c.execute("UPDATE " + tourney_table + " SET team2 = team1, team1 = 'bye' WHERE round = :p2", {"p2": path2})
                    conn.commit()
                    path = path1
                    if path.startswith("#"):
                        break
                    c.execute("SELECT * FROM " + tourney_table + " WHERE round = :p", {"p": path})
                    fetch = c.fetchone()
                    (round, team1, team2, score, path1, path2) = fetch

            c.execute("UPDATE " + tourney_table + " SET team2 = team1, team1 = ? WHERE round = ?", (team, path))
        c.execute("UPDATE participants SET score = NULL, round = ? WHERE seed = ?", (path, team))
        conn.commit()

        if path.startswith("#"):
            c.execute("SELECT captain FROM participants WHERE seed = :t", {"t": team})
            fetch = c.fetchone()
            (team_id,) = fetch
            status_message += "\nMeew! You're done with the bracket phase, <@" + str(team_id) + ">!"
            c.execute("SELECT round FROM " + tourney_table + " WHERE score = 0")
            done = c.fetchone()
            if done is None:
                status_message += "\nMeew! Tournament's over, <@143345734530498560>!"
        else:
            rounds.append(path)

    return status_message, rounds