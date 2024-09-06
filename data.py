
rooms = (836311367694286849, 848907097671729152, 848908077519470643, 848908091902132234, 848908104191967263,
         848908117696970753, 848908134918914060, 848908150114746378, 848908164074438666, 848908182901882930,
         848908202472374272, 848908230435536916, 848908251012923422, 852159667908247582, 852159761218404402)

maps = [("SZ","Humpback Pumptrack"), ("SZ", "Wahoo World"), ("SZ", "Mako Mart"), ("SZ", "Skipper Pavillion"),
        ("SZ", "Hotel Albacore"), ("TC", "Inkblot Art Academy"), ("TC", "Sturgeon Shipyard"),
        ("TC", "Startfish Mainstage"), ("TC", "Manta Maria"), ("TC", "Shellendorf Institute"),
        ("CB", "The Reef"), ("CB", "Piranha Pit"), ("CB", "Snapper Canal"), ("RM", "Musselforge Fitness"),
        ("RM", "Ancho-V Games"), ("RM", "Blackbelly Skatepark")]

valid_scores = ['0-2', '0-3', '1-2', '1-3', '2-0', '2-1', '2-3', '3-0', '3-1', '3-2']

small_seed = ["s1", "s5", "s9", "s13", "s17", "s21", "s2", "s6", "s10", "s14", "s18", "s22",
              "s3", "s7", "s11", "s15", "s19", "s23", "s4", "s8", "s12", "s16", "s20", "24"]

big_seed = ["s1", "s9", "s17", "s25", "s33", "s41", "s2", "s10", "s18", "s26", "s34", "s42",
            "s3", "s11", "s19", "s27", "s35", "s43", "s4", "s12", "s20", "s28", "s36", "s44",
            "s5", "s13", "s21", "s29", "s37", "s45", "s6", "s14", "s22", "s30", "s38", "s46",
            "s7", "s15", "s23", "s31", "s39", "s47", "s8", "s16", "s24", "s32", "s40", "s48"]


def set_roles(discord, guild):
    roles = (discord.utils.get(guild.roles, name="room1"), discord.utils.get(guild.roles, name="room2"),
             discord.utils.get(guild.roles, name="room3"), discord.utils.get(guild.roles, name="room4"),
             discord.utils.get(guild.roles, name="room5"), discord.utils.get(guild.roles, name="room6"),
             discord.utils.get(guild.roles, name="room7"), discord.utils.get(guild.roles, name="room8"),
             discord.utils.get(guild.roles, name="room9"))
    return roles


def match_finder(c, guild, rounds):
    assign_list = []
    waiter_message = ""
    for i in rounds:
        c.execute("SELECT captain FROM participants WHERE round = :path", {"path": i})
        fetch = c.fetchall()
        if len(fetch) == 2:
            (player1,) = fetch[0]
            (player2,) = fetch[1]
            assign_list.append((player1, player2))
        else:
            (user,) = fetch[0]
            player = guild.get_member(user)
            waiter_message += "\nMeew! You don't have an opponent yet, " + str(player)[:-5] + "."

    return assign_list, waiter_message


'''def map_creator(maps, tourney_format, pool_phase):
    if tourney_format == "z_smallstart" or tourney_format == "z_bigstart" and
'''

async def role_assign(assign_list, discord, guild, tourney_format, pool_phase, message):
    roles = set_roles(discord, guild)
    for i in assign_list:
        (p1, p2) = i
        for c, i2 in enumerate(roles):
            if not i2.members:
                user1 = guild.get_member(p1)
                user2 = guild.get_member(p2)
                await user1.add_roles(i2)
                await user2.add_roles(i2)
                room_id = rooms[c]
                room = guild.get_channel(room_id)
                await room.send("Meew! You can now play, <@" + str(p1) + "> and <@" + str(p2) + ">!".format(message))
                '''random_maps = map_creator(maps, tourney_format, pool_phase)
                if random_maps is not None:
                    await room.send(random_maps.format(message))'''
                break


async def role_remove(remove_list, guild):
    for i in remove_list:
        user = guild.get_member(i)
        roles = user.roles
        for i2 in roles:
            if i2.name.startswith("room"):
                await user.remove_roles(i2)





def rank_tier(rank):
    tier_number = 0
    if 90 < rank <= 100:
        tier_number = 0
    elif 80 < rank <= 90:
        tier_number = 1
    elif 70 < rank <= 80:
        tier_number = 2
    elif 60 < rank <= 70:
        tier_number = 3
    elif 40 < rank <= 60:
        tier_number = 4
    elif 20 < rank <= 40:
        tier_number = 5
    elif 0 <= rank <= 20:
        tier_number = 6

    tiers = ("Ocean", "Lagoon", "Lake", "River", "Brook", "Pond", "Puddle")
    tier = tiers[tier_number]
    return tier


async def tier_assign(discord, guild, tier_list):

    tiers = ("Ocean", "Lagoon", "Lake", "River", "Brook", "Pond", "Puddle")
    for i in tier_list:
        (user_id, tier) = i
        user = guild.get_member(user_id)
        if user:
            roles = user.roles
            for i2 in roles:
                if i2.name in tiers:
                    await user.remove_roles(i2)
            new_tier = discord.utils.get(guild.roles, name=tier)
            await user.add_roles(new_tier)
