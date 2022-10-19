from time import time
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot
import sqlite3
import math
import asyncio
import pendulum
import os.path
from os import path
  
cachedMessage = ''

#Had to enable intents for members so I can access all member objects from a server. I also had to turn on the SERVER MEMBERS INTENT on the bot page in "bot" settings.
intents = discord.Intents.all()
intents.members = True
intents.guilds = True

client = commands.AutoShardedBot(intents=intents, command_prefix = '.') #Had to include intents to add members to the server.

client.remove_command('help') #Removes the default help command so we can freely use a custom one


@client.event
async def on_ready():
    print('Bot Is Ready!')

    for guild in client.guilds:
        print(guild.name)

    await client.change_presence(activity=discord.Game('Productivity Rocks!'))

@client.command(aliases=['CREATE'])
async def create(ctx):
    ID = ctx.message.author.id
    tableName = "user" + str(ctx.message.author.id)


    conn = sqlite3.connect('task_database.db')

    c = conn.cursor()

    c.execute(' SELECT * FROM sqlite_master WHERE type="table" AND name='+"'"+tableName+"'")

    if c.fetchall() == []: #If the table does not exist!
        c.execute("CREATE TABLE " +tableName+ " (task text)") #Create the table
    
    conn.commit()

    conn.close()

    for guild in client.guilds:
        server = client.get_guild(guild.id)
        user = server.get_member(ctx.message.author.id)

        if user != None:
            break
    

    def check(message):
        print(message.content)
        userID = message.author.id
        return str(message.channel.type) == "private" and userID == ID

    await user.send("Hi! Please type your first task here :D")

    message = await client.wait_for('message', check=check)

    conn = sqlite3.connect('task_database.db') # connect to the database

    c = conn.cursor() #Create a cursor to browse the database

    
    c.execute("insert into " +tableName+ " values(?)", ([message.content]))
                
    conn.commit()

    conn.close()

    while True:
    
        await user.send("Please enter the next task! :), or type **DONE** if your finished")

        message = await client.wait_for('message', check=check)

        if message.content.upper() == "DONE":
            await user.send("All your tasks have been created! Congrats! You can now use **.start** to activate your tasks!")
            break
        
        conn = sqlite3.connect('task_database.db') # connect to the database

        c = conn.cursor() #Create a cursor to browse the database

        
        c.execute("insert into " +tableName+ " values(?)",
                    ([message.content]))
                    
        conn.commit()

        conn.close()

@client.command(aliases=["CHANNEL"])
async def channel(ctx, channelID = None):

    user = 'user' + str(ctx.message.author.id)

    conn = sqlite3.connect('task_database.db')

    c = conn.cursor()

    c.execute(f'SELECT * FROM Channels WHERE user = "{user}"')

    rows = c.fetchall()

    print(len(rows))
    if len(rows) == 0:
        c.execute(f'insert into Channels(user) values(?)', ([user]))
        conn.commit()
    
    if channelID == None:
        
        def check(message):
            userID = message.author.id
            return userID == ctx.message.author.id and message.content.isdigit()
        
        await ctx.send("Please right click and copy the ID of the channel where you want the tasks to go. Then paste the ID here :D.")

        message = await client.wait_for('message', check=check)

        c.execute(f'UPDATE Channels SET channel = "{message.content}" where user="{user}"')

    else:
        c.execute(f'UPDATE Channels SET channel = "{channelID}" where user="{user}"')

    await ctx.send("Destination Updated!")

    conn.commit()
    conn.close()


@client.command(aliases=["START"])
async def start(ctx):

    user2 = 'user' + str(ctx.message.author.id)

    conn = sqlite3.connect('task_database.db')

    c = conn.cursor()

    c.execute(f'SELECT channel FROM Channels WHERE user = "{user2}"')

    rows = c.fetchall()

    conn.commit()
    conn.close()

    if len(rows) != 0:
        channel = client.get_channel(int(rows[0][0]))
    
    else:
        channel = client.get_channel(ctx.message.channel.id)

    server = client.get_guild(996453404199108768)

    user = server.get_member(ctx.message.author.id)

    tableName = "user" + str(ctx.message.author.id)

    conn = sqlite3.connect('task_database.db') # connect to the database

    c = conn.cursor() #Create a cursor to browse the database

    c.execute(' SELECT * FROM sqlite_master WHERE type="table" AND name='+"'"+tableName+"'")

    if c.fetchall() == []: #If the table does not exist!
        c.execute("CREATE TABLE " +tableName[0]+ " (task text)") #Create the table
        await ctx.send("OOPS! You don't exist in the database yet :o Try creating some tasks first!")
    
    else:

        c.execute(' SELECT * FROM ' + tableName)

        rows = c.fetchall()

        conn.commit()

        conn.close()
        if len(rows) == 0:
            await ctx.send('Oops! You do not have any tasks yet! Try creating some tasks first with **.create**')
        
        else:

            emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

            completetionTracker = []
            embed = discord.Embed(
                colour = discord.Colour.blue()
            )

            embed.set_author(name=ctx.message.author.name +"'s Goals!") #Player Name

            embed.set_thumbnail(url=ctx.author.avatar.url)

            index = 1

            for k in rows:
                embed.add_field(name = str(index) + '.  ⬜️ '+ k[0], value="----------------------------------------------", inline=False)
                index += 1

            message = await channel.send(embed=embed)

            index = 0

            while index < len(rows):

                await message.add_reaction(emojis[index])

                index += 1
            
            cachedMessage = await channel.fetch_message(message.id)
            
            conn = sqlite3.connect('task_database.db') # connect to the database

            c = conn.cursor() #Create a cursor to browse the database

            c.execute("DELETE from Embeds where user=?", (["user" + str(ctx.message.author.id)]))
            
            c.execute("insert into Embeds values(?,?)", (["user" + str(ctx.message.author.id), message.id]))
                        
            conn.commit()

            conn.close()
            
            def check(reaction, user):
                return (str(reaction.emoji) in emojis and user == ctx.author)

            while True:
                tasks = [asyncio.create_task(client.wait_for("reaction_add", check=check),name="task1"),
                asyncio.create_task(client.wait_for("reaction_remove", check=check), name="task2")]

                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                finished: asyncio.Task = list(done)[0]

                reaction,user = finished.result()

                cachedMessage = await channel.fetch_message(message.id) #Gets access to the ACTUAL message in the channel. Not just temporary.
                
                
                embed = discord.Embed(
                    colour = discord.Colour.blue()
                )

                embed.set_author(name=ctx.message.author.name +"'s Goals!") #Player Name

                embed.set_thumbnail(url=ctx.author.avatar.url)

                print(len(cachedMessage.reactions))

                if len(cachedMessage.reactions) == 0:
                    print("what?")
                    break


                if emojis.index(str(reaction.emoji)) + 1 in completetionTracker:
                    completetionTracker.remove(emojis.index(str(reaction.emoji)) + 1)
                
                else:
                    completetionTracker.append(emojis.index(str(reaction.emoji)) + 1)
                
                index = 1
                
                for k in rows:
                    if index in completetionTracker:
                        embed.add_field(name = str(index) + '.  ☑️ '+ '~~'+k[0]+'~~', value="----------------------------------------------", inline=False)
                        
                    else:
                        embed.add_field(name = str(index) + '.  ⬜️ '+ k[0], value="----------------------------------------------", inline=False)
                    
                    index += 1
                
                await message.delete()

                message = await channel.send(embed=embed)

                cachedMessage = await channel.fetch_message(message.id)

                index = 0

                while index < len(rows):

                    await message.add_reaction(emojis[index])

                    index += 1
                
                conn = sqlite3.connect('task_database.db') # connect to the database

                c = conn.cursor() #Create a cursor to browse the database

                c.execute("DELETE from Embeds where user=?", (["user" + str(ctx.message.author.id)]))
                
                c.execute("insert into Embeds values(?,?)", (["user" + str(ctx.message.author.id), message.id]))
                            
                conn.commit()

                conn.close()

@client.command(aliases=["CLEAR"])
async def clear(ctx):
    user2 = 'user' + str(ctx.message.author.id)

    conn = sqlite3.connect('task_database.db')

    c = conn.cursor()

    c.execute(f'SELECT channel FROM Channels WHERE user = "{user2}"')

    rows1 = c.fetchall()

    conn.commit()
    conn.close()
    tableName = "user" + str(ctx.message.author.id)
    conn = sqlite3.connect('task_database.db')
    c = conn.cursor()

    # delete all rows from table
    c.execute('DELETE FROM ' + tableName)

    conn.commit()

    print('We have deleted', c.rowcount, 'records from the table.')

    await ctx.send('All your tasks have been cleared!')

    channel = client.get_channel(int(rows1[0][0]))

    c.execute("SELECT * from Embeds where user=?",(["user" + str(ctx.message.author.id)]))

    rows = c.fetchall()

    if len(rows) == 0:
        pass
    else:
        message = await channel.fetch_message(rows[0][1])
        await message.clear_reactions()
    
        c.execute("DELETE from Embeds where user=?",(["user" + str(ctx.message.author.id)]))

    #commit the changes to db			
    conn.commit()
    #close the connection
    conn.close()

@client.command(aliases=["VIEW"])
async def view(ctx):
    tableName = "user" + str(ctx.message.author.id)

    print(tableName)

    conn = sqlite3.connect('task_database.db')

    c = conn.cursor()

    c.execute(f'SELECT * FROM {tableName}')

    rows = c.fetchall()

    conn.commit()
    conn.close()

    embed = discord.Embed(
                colour = discord.Colour.blue()
            )

    embed.set_author(name=ctx.message.author.name +"'s Goals!") #Player Name

    embed.set_thumbnail(url=ctx.author.avatar.url)

    index = 1

    for k in rows:
        embed.add_field(name = str(index) + '.  ⬜️ '+ k[0], value="----------------------------------------------", inline=False)
        index += 1
    

    await ctx.send(embed=embed)


@client.command(aliases=["DELETE"])
async def delete(ctx):
    tableName = "user" + str(ctx.message.author.id)

    ID = ctx.message.author.id

    print(tableName)

    conn = sqlite3.connect('task_database.db')

    c = conn.cursor()

    c.execute(f'SELECT * FROM {tableName}')

    rows = c.fetchall()

    conn.commit()
    conn.close()

    embed = discord.Embed(
                colour = discord.Colour.blue()
            )

    embed.set_author(name=ctx.message.author.name +"'s Goals!") #Player Name

    embed.set_thumbnail(url=ctx.author.avatar.url)

    index = 1

    for k in rows:
        embed.add_field(name = str(index) + '.  ⬜️ '+ k[0], value="----------------------------------------------", inline=False)
        index += 1
    
    def check(message):
        print(message.content)
        userID = message.author.id
        return userID == ID

    embedMessage = await ctx.send(embed=embed)

    await ctx.send("Please enter in the number associated with the task you want to delete")

    message = await client.wait_for("message", check=check)

    conn = sqlite3.connect('task_database.db')

    c = conn.cursor()
    count = 1
    number = int(message.content)
    for k in rows:
        if count == number:
            c.execute(f"DELETE From {tableName} WHERE task='{k[0]}'")
            break
        else:
            count += 1
            continue


    conn.commit()
    conn.close()
    await embedMessage.delete()

    await ctx.send("Task Deleted! :)")



@client.command(aliases=["REMIND"])
async def remind(ctx, *, reminder):
    now = pendulum.now()

    later =''

    ID = ctx.message.author.id

    for guild in client.guilds:
        server = client.get_guild(guild.id)
        user = server.get_member(ctx.message.author.id)

        if user != None:
            break
    
    emojis = ['✅', '🔁']
 

    def check(message):

        userID = message.author.id

        return userID == ctx.message.author.id and str(message.channel.type) == "private"
    
    def check2(reaction, user):
                return (str(reaction.emoji) in emojis and user == ctx.author)
    
    await user.send("Enter the amount of time the bot should wait before reminding you. Examples: (**5m**, **30m**, **1h**, **7h**)")
    
    message = await client.wait_for("message", check=check)

    timeFrame = message.content

    if "m" in timeFrame or "M" in timeFrame:
            timeFrame = timeFrame.strip("m")
            timeFrame = timeFrame.strip("M")

            timeFrame = int(timeFrame)

            later = now.add(minutes=timeFrame)
        
    elif "h" in timeFrame or "H" in timeFrame:
        timeFrame = timeFrame.strip("h")
        timeFrame = timeFrame.strip("H")
        
        timeFrame = int(timeFrame)

        later = now.add(hours=timeFrame)
    
    elif "d" in timeFrame or "D" in timeFrame:
        timeFrame = timeFrame.strip("d")
        timeFrame = timeFrame.strip("D")

        timeFrame = int(timeFrame)

        later = now.add(days=timeFrame)
    
    remindTime = now.diff(later).in_seconds()

    while True:

        await asyncio.sleep(remindTime)

        embed = discord.Embed(
                    colour = discord.Colour.blue()
                )

        embed.set_author(name= f"{reminder}") #Reminder

        embed.set_thumbnail(url=ctx.author.avatar.url)

        embed.add_field(name= f"{emojis[0]} = Completed", value='--------------------', inline=False)
        embed.add_field(name= f"{emojis[1]} = Repeat Reminder", value='--------------------', inline=False)

        embedMsg = await user.send(embed=embed)

        await embedMsg.add_reaction("✅")
        await embedMsg.add_reaction("🔁")

        reaction, user2 = await client.wait_for("reaction_add", check=check2)

        if reaction.emoji == "✅":
            await embedMsg.delete()
            await user.send("Reminder Deactivated")
            break

        else:
            await user.send("Reminder Reactivated")
            await embedMsg.delete()
    


client.run('OTk3Mjc4NTE3OTU4MDI5NDIz.GUFie-.aEyzOHMSv9AbMyJVMsnR__i08XBM4s5PwFOKko')
