import discord
import sqlite3
from discord_components import  Select
import re
from account_commands import info, team, create, join, leave, confirm, kick, checkin
from tournament_commands import sortseed, poolstart, poolseed, papstart, result, rps, random_starter, score_c, wrong, correct
from data import role_assign, role_remove, tier_assign

queue = []
ciopen = False
tournament_running = True
pool_phase = False
tourney_format = ""
confirm_here = 858840711302742046
guild_id = 744170541040140298
admin_id = 143345734530498560
lfteam_id = 863490215658258472



class MyClient(discord.Client):

    async def on_ready(self):

        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_raw_reaction_add(self, reaction):
        if reaction.message_id == lfteam_id:
            guild = client.get_guild(guild_id)
            reactor_id = reaction.user_id
            lfg_role = discord.utils.get(guild.roles, name="Looking for Team")
            user = guild.get_member(reactor_id)
            await user.add_roles(lfg_role)
            print(str(user) + " has reacted to Looking for Team")

    async def on_raw_reaction_remove(self, reaction):
        if reaction.message_id == lfteam_id:
            guild = client.get_guild(guild_id)
            reactor_id = reaction.user_id
            lfg_role = discord.utils.get(guild.roles, name="Looking for Team")
            user = guild.get_member(reactor_id)
            await user.remove_roles(lfg_role)
            print(str(user) + " has un-reacted to Looking for Team")

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        global ciopen
        global confirm_here
        global pool_phase
        global tourney_format
        global tournament_running

        if message.content.startswith('!'):

            queue.append([message.content, message.author.id, True])
            print(queue)

            while queue[0][2]:
                queue[0][2] = False
                user_message = queue[0][0]
                user_id = queue[0][1]
                conn = sqlite3.connect("Minimiez.db")
                c = conn.cursor()

                if message.content.startswith("!hi"):
                    print("hi")
                    await message.channel.send(
                        'Meew! HI!'.format(message))

                if user_id == admin_id:
                    if message.content.startswith("!Confirm here!"):
                        confirm_here = message.id
                        print(message.id)
                    elif message.content.startswith("!rank"):
                        try:
                            admin_message = message.content.replace("!rank", "")
                            rank = admin_message[:4]
                            uid = admin_message[4:]
                            print(rank, uid)
                            c.execute("UPDATE users SET rank = ? WHERE user_id = ?", (int(rank), int(uid)))
                            conn.commit()
                            await message.channel.send("Meew! New Rank for " + uid + " set: " + rank.format(message))
                        except (ValueError, OverflowError):
                            await message.channel.send("Meew! What are you trying to enter here my man?".format(message))
                    elif message.content.startswith("!ciopen"):
                        await message.channel.send("Meew! You can now check in, everyone!".format(message))
                        ciopen = True
                    elif message.content.startswith("!ciclose"):
                        await message.channel.send("Meew! Check-ins are now closed!".format(message))
                        ciopen = False
                    elif message.content.startswith("!cireset"):
                        c.execute("UPDATE teams SET checked_in = 0")
                        c.execute("UPDATE teams SET confirmed = 0 WHERE member_number != 1")
                        conn.commit()
                        await message.channel.send("Meew! Check-ins and confirmations have been reset!".format(message))
                    elif message.content.startswith("!sortseed"):
                        ciopen = False
                        (seed_message, t_format) = sortseed(c, conn)
                        tourney_format = t_format
                        await message.channel.send(seed_message.format(message))
                    elif message.content.startswith("!tourneystart"):
                        guild = client.get_guild(guild_id)
                        if tourney_format is not None:
                            (pool_message, assign_list) = poolstart(c, conn, guild, tourney_format)
                            if pool_message:
                                await message.channel.send(pool_message.format(message))
                            await role_assign(assign_list, discord, guild, message)
                            tournament_running = True
                            if tourney_format != "z_sevenstart":
                                pool_phase = True
                        else:
                            await message.channel.send("Meew! We don't have a valid amount of participants!".format(message))

                    elif message.content.startswith("!poolseed"):
                        tournament_running = False
                        pool_phase = False
                        await message.channel.send(poolseed(c, conn, tourney_format).format(message))
                    elif message.content.startswith("!papstart"):
                        guild = client.get_guild(guild_id)
                        (assign_list, status_message) = papstart(c, conn, guild)
                        if status_message:
                            await message.channel.send(status_message.format(message))
                        await role_assign(assign_list, discord, guild, message)
                        tournament_running = True
                        pool_phase = False
                    elif message.content.startswith("!result"):
                        guild = client.get_guild(guild_id)
                        if tourney_format == "z_fourstart" or tourney_format == "z_sevenstart":
                            await message.channel.send(poolseed(c, conn, tourney_format).format(message))
                        (result_message, tier_list) = result(c, conn, tourney_format)
                        await tier_assign(discord, guild, tier_list)
                        await message.channel.send(result_message.format(message))
                        tournament_running = False

                c.execute("SELECT user_id FROM users WHERE user_id = :uid", {"uid": user_id})
                fetch = c.fetchone()

                if fetch is None:
                    if message.content.startswith("!register"):
                        user_message = user_message.replace("!register", "")
                        is_fc = re.match("\d{4}-\d{4}-\d{4}", user_message[1:])
                        if is_fc:
                            c.execute("INSERT INTO users VALUES (?, ?, 0, 1, 60.0)",(user_id, user_message))
                            conn.commit()
                            '''
                            guild = client.get_guild(guild_id)
                            user = guild.get_member(user_id)
                            role = guild.get_role(861332825450217512)
                            await user.add_roles(role)
                            '''
                            await message.channel.send(
                                "Meew! You have successfully registered, {0.author.mention}!".format(message))
                        else:
                            await message.channel.send(
                                "Meew! You did not enter your FC correctly, {0.author.mention}! The pattern is 'xxxx-xxxx-xxxx'.".format(message))
                    else:
                        await message.channel.send("Meew! You'll have to register first, {0.author.mention}".format(message))

                else:
                    if message.content.startswith("!register"):
                        await message.channel.send(
                            'Meew! are already registered, {0.author.mention}!'.format(message))
                    elif message.content.startswith("!hello"):
                        await message.channel.send('Meew! Hello from the tower, {0.author.mention}!'.format(message))

                    elif message.content.startswith("!info"):
                        if user_id == admin_id and user_message != "!info":
                            try:
                                user_id = int(user_message.replace("!info ", ""))
                            except ValueError:
                                await message.channel.send("Meew! What are you trying to enter here my man?".format(message))
                        await message.channel.send(info(c, user_id, client).format(message))
                    elif message.content.startswith("!team"):
                        if user_id == admin_id and user_message != "!team":
                            try:
                                user_id = int(user_message.replace("!team ", ""))
                            except ValueError:
                                await message.channel.send("Meew! What are you trying to enter here my man?".format(message))
                        await message.channel.send(team(c, client, user_id).format(message))
                    elif message.content.startswith("!create"):
                        await message.channel.send(create(c, conn, user_id, user_message).format(message))
                    elif message.content.startswith("!join"):
                        await message.channel.send(join(c, conn, user_id, user_message).format(message))
                    elif message.content.startswith("!leave"):
                        await message.channel.send(leave(c, conn, user_id).format(message))
                    elif message.content.startswith("!confirm"):
                        await message.channel.send(confirm(c, conn, user_id, user_message).format(message))
                    elif message.content.startswith("!kick"):
                        await message.channel.send(kick(c, conn, user_id, user_message).format(message))
                    elif message.content.startswith("!checkin"):
                        if ciopen:
                            await message.channel.send(checkin(c, conn, user_id).format(message))
                        else:
                            await message.channel.send("Meew! The tournament can't be checked into right now!".format(message))

                    if tournament_running and message.channel.id != 853265228057542716:

                        if message.content.startswith("!rps"):
                            guild = client.get_guild(guild_id)
                            await message.channel.send(rps(guild, user_id).format(message))

                        elif message.content.startswith("!random"):
                            await message.channel.send(random_starter().format(message))

                        elif message.content.startswith("!score"):
                            await message.channel.send(score_c(c, conn, user_id, user_message).format(message))

                        elif message.content.startswith("!wrong"):
                            await message.channel.send(wrong(c, conn, user_id).format(message))

                        elif message.content.startswith("!correct"):
                            guild = client.get_guild(guild_id)
                            status_id = 852305501714513950
                            status_room = guild.get_channel(status_id)

                            (correct_message, status_message, assign_list, remove_list) = \
                                correct(c, conn, user_id, guild, pool_phase, tourney_format)
                            if correct_message:
                                await message.channel.send(correct_message.format(message))
                            if status_message:
                                await status_room.send(status_message.format(message))
                            if remove_list:
                                await role_remove(remove_list, guild)
                            if assign_list:
                                await role_assign(assign_list, discord, guild, tourney_format, pool_phase, message)

                queue.pop(0)
                if not queue:
                    break
                conn.close()


intents = discord.Intents.default()
intents.members = True
intents.presences = False
intents.typing = True
client = MyClient(intents=intents)
client.run('Not included for obvious reasons')

