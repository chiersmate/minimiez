from data import rank_tier


def info(c, user_id, client):
    c.execute("SELECT switch_fc, last_played, rank FROM users WHERE user_id = :uid", {"uid": user_id})
    fetch = c.fetchone()
    (fc, last_played, rank) = fetch
    info_message = "Meew! Here are your stats!\nPlayer: " + str(client.get_user(user_id))[
                                                            :-5] + "\nFriend-Code:" + fc + "\nMM-Rank: "

    c.execute("SELECT * FROM tourney_played WHERE user_id = :uid", {"uid": user_id})
    fetch = c.fetchall()
    if not fetch:
        info_message += str("{:2.2f}".format(rank)) + "\nTournaments played: 0"
    else:
        tournaments = len(fetch)
        fetch.sort(key=lambda tup: tup[4], reverse=True)
        fetch = fetch[:5]

        last_placements = ""
        for i in fetch:
            (user_id, tourney_id, entrants, placement, tourney_date) = i
            last_placements += "\n#" + str(placement) + " on Tournament No." + str(tourney_id) + " (" + str(
                tourney_date)[:10] + ")"
        tier = rank_tier(rank)

        info_message += str("{:2.2f}".format(rank)) + " (" + tier + ")\nTournaments played: " + str(
            tournaments) + "\nLast played: " \
                        + str(last_played) + " Tournament(s) ago.\nLast 5 placements:\n" + str(last_placements)

    return info_message


def team(c, client, user_id):
    team_message = "Meew! You are not in a team!"

    c.execute("SELECT captain, team_name FROM teams WHERE user_id = :uid", {"uid": user_id})
    fetch = c.fetchone()
    if fetch:
        (captain, team_name) = fetch
        team_message = "Meew! Your team is: " + team_name
        team_message += "\nTeam Captain: " + str(client.get_user(captain))[:-5] + " \nTeam Members:"
        c.execute("SELECT user_id, member_number, confirmed, checked_in FROM teams WHERE team_name = :t_name",
                  {"t_name": team_name})
        no_yes = ["No.", "Yes."]
        fetch = c.fetchall()
        fetch.sort(key=lambda tup: tup[1])
        for i in fetch:
            (m_id, m_number, m_confirmed, m_checked) = i
            team_message += "\n" + str(m_number) + ": " + str(client.get_user(m_id))[:-5] + " | Confirmed: " + no_yes[
                m_confirmed] + " | Checked in: " + no_yes[m_checked]

    return team_message


def create(c, conn, user_id, user_message):
    create_message = ""

    new_team_name = user_message.replace("!create", "")
    c.execute("SELECT rank FROM users WHERE user_id = :uid", {"uid": user_id})
    fetch = c.fetchone()
    (rank,) = fetch
    c.execute("SELECT * FROM teams WHERE team_name = :ntn", {"ntn": new_team_name})
    tn_taken = c.fetchone()

    if tn_taken:
        create_message = "Meew! That Team name is already taken!"
    elif new_team_name == "" or len(new_team_name) > 20:
        create_message = "Meew! Team name must have between 1 and 20 characters"
    elif "@" in new_team_name:
        create_message = "Meew! You're not allowed to use '@' in your Team name, sorry!"
    elif new_team_name == "bye":
        create_message = "Meew! You're not allowed to name your team 'bye', sorry!"
    else:
        c.execute("INSERT INTO teams VALUES (?, ?, ?, '1', ?, 1, 0)", (user_id, rank, new_team_name, user_id))
        conn.commit()
        create_message = "Meew! You created the new Team: " + new_team_name[1:] + "!"
    return create_message


def join(c, conn, user_id, user_message):
    join_message = "Meew! You are already in a Team! You must !leave you old one first!"
    team_to_join = user_message.replace("!join", "")
    c.execute("SELECT user_id FROM teams WHERE user_id = :uid", {"uid": user_id})
    fetch = c.fetchone()
    if fetch is None:
        c.execute("SELECT member_number, captain FROM teams WHERE team_name = :ttj", {"ttj": team_to_join})
        fetch = c.fetchall()
        if fetch:
            (highest_number, captain) = max(fetch, key=lambda tup: tup[0])
            c.execute("SELECT rank FROM users WHERE user_id = :uid", {"uid": user_id})
            fetch = c.fetchone()
            (rank,) = fetch
            c.execute("INSERT INTO teams VALUES (?, ?, ?, ?, ?, 0, 0)",
                      (user_id, rank, team_to_join, highest_number + 1, captain))
            conn.commit()
            join_message = "Meew! You joined" + team_to_join

        else:
            join_message = "Meew! This team doesn't exist!"

    return join_message


def leave(c, conn, user_id):
    leave_message = "Meew, you weren't part of a team to begin with!"
    c.execute("SELECT member_number, captain, team_name FROM teams WHERE user_id = :uid", {"uid": user_id})
    fetch = c.fetchone()
    if fetch:
        (leave_number, captain, team_name) = fetch
        if captain == user_id:
            c.execute("DELETE FROM teams WHERE captain = :uid", {"uid": user_id})
            leave_message = "Meew! You disbanded " + team_name + "!"
        else:
            c.execute("DELETE FROM teams WHERE user_id = :uid", {"uid": user_id})
            c.execute("UPDATE teams SET member_number = member_number - 1 WHERE member_number > ? AND team_name = ?",
                      (leave_number, team_name))
            leave_message = "Meew! You left Team " + team_name + ", <@" + str(user_id) + ">!"
        conn.commit()

    return leave_message


def confirm(c, conn, user_id, user_message):
    confirm_message = "Meew! You are not the captain of your team!"
    c.execute("SELECT confirmed FROM teams WHERE captain = :uid AND confirmed = 1", {"uid": user_id})
    fetch = c.fetchall()
    print(fetch)
    if len(fetch) < 4:
        c.execute("SELECT member_number, captain FROM teams WHERE captain = :uid", {"uid": user_id})
        fetch = c.fetchall()
        if fetch:
            try:
                user_message = int(user_message.replace("!confirm", ""))
                (highest_member, cap) = max(fetch, key=lambda tup: tup[0])
                if 1 < user_message <= highest_member:
                    c.execute("UPDATE teams SET confirmed = 1 WHERE member_number = ? AND captain = ?",
                              (user_message, user_id))
                    conn.commit()
                    confirm_message = "Meew! Member Number " + str(
                        user_message) + " has been confirmed to play in the tournament!"
                elif user_message == 1:
                    confirm_message = "Meew! No need to confirm yourself!"
                else:
                    confirm_message = "Meew! You entered an incorrect Member Number!"

            except ValueError:
                confirm_message = "Meew! You entered an incorrect Member Number!"
    else:
        confirm_message = "Meew! There are already four confirmed members in your team! You'll have to !kick a member first."

    return confirm_message


def kick(c, conn, user_id, user_message):
    kick_message = "Meew! You are not the captain of your team!"

    c.execute("SELECT member_number, captain FROM teams WHERE captain = :uid", {"uid": user_id})
    fetch = c.fetchall()
    if fetch:
        try:
            user_message = int(user_message.replace("!kick", ""))
            (highest_member, cap) = max(fetch, key=lambda tup: tup[0])
            if 1 < user_message <= highest_member:
                c.execute("DELETE FROM teams WHERE member_number = :um", {"um": user_message})
                c.execute("UPDATE teams SET member_number = member_number - 1 WHERE member_number > ? AND captain = ?",
                          (user_message, user_id))
                conn.commit()
                conn.commit()
                kick_message = "Meew! Member Number " + str(
                    user_message) + " has been kicked from your team!"
            elif user_message == 1:
                kick_message = "Meew! You can't kick yourself! Use !leave instead."
            else:
                kick_message = "Meew! You entered an incorrect Member Number!"

        except ValueError:
            kick_message = "Meew! You entered an incorrect Member Number!"

    return kick_message


def checkin(c, conn, user_id):
    checkin_message = "Meew! You're not in a team!"

    c.execute("SELECT confirmed FROM teams WHERE user_id = :uid", {"uid": user_id})
    fetch = c.fetchone()
    if fetch:
        (confirmed,) = fetch
        if confirmed:
            c.execute("UPDATE teams SET checked_in = 1 WHERE user_id = :uid", {"uid": user_id})
            conn.commit()
            checkin_message = "Meew! You are now checked in! See for yourself by using !team."
        else:
            checkin_message = "Meew! You're not confirmed for your team!"

    return checkin_message
