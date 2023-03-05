from dotenv import load_dotenv
import os
import discord
from discord import option, Embed
from typing import Union, List
import time
import asyncio
import datetime


# Load dotenv variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.all()
intents.message_content = True
intents.members = True

# bot = commands.Bot(command_prefix='/')
bot = discord.Bot(intents=intents)


# --------------------------------------------------------------------------------------------------------------------------------------------


@bot.event
async def on_ready():
    print(f'Bot ready! Running {bot.user}')

@bot.event
async def on_message(message):
    # Make sure we won't be replying to ourselves.
    if message.author.id == bot.user.id:
        return
    print(f'Message from {message.author}: {message.content}')



# --------------------------------------------------------------------------------------------------------------------------------------------

# Sleep for duration specified by user, used in remind functions
def calc_delay(time, duration):
    if(duration == "seconds"):
        delay = time
    elif(duration == "minutes"):
        delay = time * 60
    elif(duration == "hours"):
        delay = time * 60 * 60
    elif(duration == "days"):
        delay = time * 60 * 60 * 24
    return delay


# /remindme
@bot.slash_command(guild_ids=[1077368721556901988], name="remindme", description="Set a reminder for a certain time period with a message.")
@option("when", description="When should I remind you? (A number)", min_value=1)
@option("unit", description="Select days/hours/mins/seconds", choices=["seconds", "minutes", "hours","days"])
@option("message", description="Enter the message")
async def remindme(
    ctx: discord.ApplicationContext,
    when: int,
    unit: str,
    message: str,
):

    body = f"I will remind you in {when} {unit}"
    embed=discord.Embed(title=":alarm_clock: Reminder created!", description=body, color=0x3598DB, timestamp=datetime.datetime.now())
    await ctx.send_response(embed=embed,ephemeral=True)

    # Reminder message, delays for specified time by user then sends a reminder
    await asyncio.sleep(calc_delay(when,unit))
    reminderEmbed = discord.Embed(title=":white_check_mark: Reminder!", description=message, color=0x3598DB, timestamp=datetime.datetime.now())
    await ctx.send_followup(embed=reminderEmbed,ephemeral=True)


# --------------------------------------------------------------------------------------------------------------------------------------------


# /remind @user
@bot.slash_command(guild_ids=[1077368721556901988], name="remind", description="Set a reminder for other users.")
@option("user", discord.Member, description="Select the user you'd like to remind")
@option("when", description="When should I remind this user? (A number)", min_value=1)
@option("unit", description="Select days/hours/mins/seconds", choices=["seconds", "minutes", "hours","days"])
@option("message", description="Enter the message")
async def remind(
    ctx: discord.ApplicationContext,
    user: discord.Member,
    when: int,
    unit: str,
    message: str,
):
    # Notifies the user they've successfully created a reminder
    body = f"I will remind {user.mention} in {when} {unit}"
    embed = discord.Embed(title=":alarm_clock: Reminder created!", description=body, color=0x3598DB, timestamp=datetime.datetime.now())
    await ctx.send_response(embed=embed)

    # Reminder message, delays for specified time by user then sends a reminder
    await asyncio.sleep(calc_delay(when,unit))
    reminderEmbed = discord.Embed(title=":white_check_mark: Reminder!", description=message, color=0x3598DB, timestamp=datetime.datetime.now())
    reminderEmbed.set_footer(text=f"Set by {ctx.author}")
    await ctx.send_followup(content=user.mention,username=user.name,embed=reminderEmbed)


# --------------------------------------------------------------------------------------------------------------------------------------------
# New study rooms


# /newroom <name> <text_channel/voice_channel> 
@bot.slash_command(guild_ids=[1077368721556901988], name="newroom", description="Create a private study (text/voice) channel.")
@option("name", description="Enter the name of the study room")
@option("channel", description="Select a channel", choices=["Text Channel", "Voice Channel"])
async def newroom(
    ctx: discord.ApplicationContext,
    name: str,
    channel: str,
):
    # Get the current guild/server
    guild = ctx.guild
    embed = discord.Embed(title="Private Study Room", description="", color=0x80ffdb)
    if(channel == "Text Channel"):
        # Add the bot to the private study room
        bot = await guild.fetch_member(1077361827844980796)
        author = ctx.author
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            bot: discord.PermissionOverwrite(read_messages=True,send_messages=True),
            author: discord.PermissionOverwrite(read_messages=True)
        }
        # Create a private study room
        await guild.create_text_channel(name="Study: " + name,overwrites=overwrites)
    # Voice channel
    else:
        author = ctx.author
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=False),
            author: discord.PermissionOverwrite(connect=True)
        }
        await guild.create_voice_channel(name="Study: " + name,overwrites=overwrites)

    body = f"Created a new study room: {name}" 
    embed = discord.Embed(title=":notebook_with_decorative_cover: Study room created!", description=body, color=0x3598DB, timestamp=datetime.datetime.now())
    await ctx.send_response(embed=embed,ephemeral=True)



# --------------------------------------------------------------------------------------------------------------------------------------------
# TODO List

# Array containing the description of each task set by the user
todo_list = []
# Embed which displays the todo list
todo_embed = discord.Embed(title="", description="", color=0x06d6a0)

# Keep track of previous todo list message (used to delete/declutter channel when new tasks are added/finished)
prev_message = None


# Class for "Finish all tasks" and "Delete all tasks" buttons
class TodoView(discord.ui.View):

    # Finish all tasks in todo list
    @discord.ui.button(label="Finish all tasks", row=0, style=discord.ButtonStyle.primary)
    async def button_callback(self, button, interaction):
        if(len(todo_list) > 0):
            # For each task, update the icon to a check and edit the existing field in the embed
            for ind,task in enumerate(todo_list):
                field_ind = ind+1
                field_body = f"**[:white_check_mark:]** **{field_ind}.**" + "~~" + task + "~~"
                todo_embed.set_field_at(index=field_ind,name="",value=field_body, inline=False)

            todo_embed.timestamp = datetime.datetime.now()
            await interaction.response.edit_message(view=self,embed=todo_embed)
        else:
            await interaction.response.send_message("Your TODO list is empty!")

    # Delete all tasks from TODO list
    @discord.ui.button(label="Delete all tasks", row=0, style=discord.ButtonStyle.danger)
    async def second_button_callback(self, button, interaction):
        # Delete all tasks from list and embed
        if(len(todo_list) > 0):
            todo_embed.clear_fields()
            todo_list.clear()
            # Update embed to have 0 tasks, and add removed field for specifiying 'Your Tasks'
            todo_embed.description = f"You have {len(todo_list)} tasks!"
            todo_embed.add_field(name="Your Tasks", value=":white_small_square: Create a new task by typing: `/newtask <description>`\n:white_small_square: Finish a task by typing: `/finishtask <tasknum>`", inline=False)
            await interaction.response.edit_message(view=self,embed=todo_embed)
        else:
            await interaction.response.send_message("Your TODO list is already empty!")



# /newtask <description>
@bot.slash_command(guilds_ids=[1077368721556901988], name="newtask", description="Add a task to your todo list.")
@option("description", description="Enter the description of the task")
async def newtask(ctx: discord.ApplicationContext, description: str):
    global prev_message
    # Create a new todo list
    if(todo_embed.title == ""):
        # Notifies the user they've successfully created a new todo list
        todo_embed.title = f":white_check_mark: TODO List"
        todo_embed.description = f"You have {len(todo_list)} task(s)!"
        todo_embed.timestamp = datetime.datetime.now()
        todo_embed.add_field(name="Your Tasks", value=":white_small_square: Create a new task by typing: `/newtask <description>`\n:white_small_square: Finish a task by typing: `/finishtask <# of task>`", inline=False)

    # Delete previous /newtask message to avoid spamming channel
    if(prev_message is not None):
        await prev_message.delete_original_response()

    # Append new task to existing todo list
    todo_list.append(description)
    todo_embed.description = f"You have {len(todo_list)} task(s)!"
    field_body = f"**[:red_circle:]** **{len(todo_list)}.** {description}"
    todo_embed.add_field(name="",value=field_body, inline=False)
    # Set the prev message, so that when /newtask is called again the previous message will be deleted
    prev_message = await ctx.send_response(embed=todo_embed, view=TodoView())



# /finishtask <task_num>
@bot.slash_command(guilds_ids=[1077368721556901988], name="finishtask", description="Complete a task in your todo list.")
@option("task_num", description="Select the task you completed")
# @option("task_num", description="Select the task you completed", choices=task_choices())
async def finishtask(ctx: discord.ApplicationContext, task_num: int):
    global prev_message

    # Check if there is a TODO list 
    if(todo_embed.title == ""):
        await ctx.respond("You must add a task to your todo list before completing it. Use /newtask")
        return

    # Check the users task number is valid 
    ind = task_num-1
    if(ind < 0 or ind >= len(todo_list)):
        await ctx.respond("Please enter a valid task number.")
    else:
        # Delete previous /newtask message to avoid spamming channel
        if(prev_message is not None):
            await prev_message.delete_original_response()

        todo_embed.timestamp = datetime.datetime.now()
        # Finish a selected task by updating the icon to a check
        field_body = f"**[:white_check_mark:]** **{task_num}.**" + "~~" + todo_list[ind] + "~~"
        todo_embed.set_field_at(index=task_num,name="",value=field_body, inline=False)
        prev_message = await ctx.respond(embed=todo_embed, view=TodoView())


# --------------------------------------------------------------------------------------------------------------------------------------------
# POLL 


# Class for voting for option 1 and option 2 buttonss
class PollView(discord.ui.View):
    # Keep track of which users clicked the button
    users = {}

    # Update the count on the poll embed
    def update_count(self,interaction,option):
        # Get embed from original poll message to edit
        embed = interaction.message.embeds[0]
        # Extract the current option and value = :one: <option> (<currentVotes>)
        option1 = embed.fields[option].value[:-3]
        value = embed.fields[option].value[-2]
        # Increment it by 1 and edit the embed poll
        value = str(int(value)+1)
        embed.set_field_at(index=option,name="",value=f"{option1} ({value})", inline=False)
        return embed


    # Button for voting for the first option
    @discord.ui.button(label="Vote", row=0, style=discord.ButtonStyle.primary,emoji="1️⃣")
    async def option1_callback(self, button, interaction):
        # Check if the user has already voted
        if(interaction.user.id in self.users):
            await interaction.response.send_message(content="You can only vote once",ephemeral=True,delete_after=15)
            return
        
        # Increment the count for option 1
        embed = self.update_count(interaction,1)
        # Only allow user to vote once
        self.users[interaction.user.id] = 1
        await interaction.response.edit_message(view=self,embed=embed)

    # Button for voting for the second option
    @discord.ui.button(label="Vote", row=0, style=discord.ButtonStyle.primary,emoji="2️⃣")
    async def option2_callback(self, button, interaction):
        # Check if the user has already voted (only sends to user who voted)
        if(interaction.user.id in self.users):
            await interaction.response.send_message(content="You can only vote once",ephemeral=True,delete_after=15)
            return

        # Increment the count for option 2
        embed = self.update_count(interaction,2)
        # Only allow user to vote once
        self.users[interaction.user.id] = 2
        await interaction.response.edit_message(view=self,embed=embed)


# /poll <question> <option1> <option2>
@bot.slash_command(guild_ids=[1077368721556901988], name="poll", description="Create a poll.")
@option("question", description="What question do you want to ask")
@option("option1", description="Enter the first option")
@option("option2", description="Enter the second option")
async def poll(
    ctx: discord.ApplicationContext,
    question: str,
    option1: str,
    option2: str,
):
    # Notifies the user they've successfully created a reminder
    embed = discord.Embed(title=":ballot_box: Poll", color=0x3598DB, timestamp=datetime.datetime.now())
    embed.add_field(name=question, value="", inline=False)
    embed.add_field(name="",value=f":one: {option1} (0)", inline=False)
    embed.add_field(name="",value=f":two: {option2} (0)", inline=False)
    embed.set_footer(text=f"Asked by {ctx.author}")
    await ctx.respond(embed=embed,view=PollView())



# --------------------------------------------------------------------------------------------------------------------------------------------
# Study session

# Class for "Stop timer" and "Restart timer" buttons
class StudyView(discord.ui.View):
    start_time = None

    def set_time(self,time):
        self.start_time = time

    def get_elapsed_time(self):
        # Calculate elapsed time
        curr_time = datetime.datetime.now()
        elapsed_time = curr_time - self.start_time
        # Get format in to hh:mm:ss (strip the ms)
        elapsed_time = str(elapsed_time)[:-7]
        return elapsed_time


    # Refresh "time studied"
    @discord.ui.button(label="Refresh", row=0, style=discord.ButtonStyle.primary)
    async def refresh_callback(self, button, interaction):
        # Get elapsed time
        elapsed_time = self.get_elapsed_time()
        # Get embed from original poll message to edit
        embed = interaction.message.embeds[0]
        # Update the elapsed time
        embed.set_field_at(index=1,name=":clock3: Time Studied",value=f"```{elapsed_time}```", inline=True)
        await interaction.response.edit_message(view=self,embed=embed)


    # End study session
    @discord.ui.button(label="End Session", row=0, style=discord.ButtonStyle.danger)
    async def finish_callback(self, button, interaction):
        # Get embed from original message to edit
        embed = interaction.message.embeds[0]
        elapsed_time = self.get_elapsed_time()
        embed.set_field_at(index=1,name=":clock3: You studied for",value=f"```{elapsed_time}```", inline=True)
        # Remove refresh/finish buttons
        await interaction.response.edit_message(view=None,embed=embed)




# /study <name> 
@bot.slash_command(guild_ids=[1077368721556901988], name="study", description="Start a study session.")
@option("topic", description="What are you studying?")
async def study(ctx: discord.ApplicationContext, topic: str):
    # Create new Study object, used to track the amount of time studied, and refresh/complete buttons
    study_obj = StudyView()
    title = f"{ctx.author.name}'s Study Session"
    picture = ctx.author.avatar.url

    # Get the starting time and set it
    curr_time = datetime.datetime.now()
    study_obj.set_time(curr_time)
    time_format = curr_time.strftime("%H:%M:%S")

    embed = discord.Embed(title="", description="", color=0xffcb69)
    embed.set_author(name=title,icon_url=picture)
    embed.set_footer(text=f"Started at {time_format}")
    embed.add_field(name="Studying",value=f"```{topic}```",inline=True)
    embed.add_field(name=":clock3: Time Studied",value=f"```00:00:00```",inline=True)
    await ctx.respond(embed=embed,view=study_obj)




# --------------------------------------------------------------------------------------------------------------------------------------------
# Flashcard

# Class for voting for option 1 and option 2 buttonss
class FlashcardView(discord.ui.View):
    # If the flashcard has been flipped
    flipped = False
    # Button for voting for the first option
    @discord.ui.button(label="Reverse the flashcard", row=0, style=discord.ButtonStyle.primary,emoji="🔄")
    async def flashcard_callback(self, button, interaction):
        # Get embed from original poll message to edit
        embed = interaction.message.embeds[0]
        # Flashcard was already flipped (question is now the answer, answer is now the question)
        if(self.flipped):
            answer = embed.fields[0].value
            question = embed.fields[1].value[2:-2]
            embed.set_field_at(index=0,name="Question/Term:",value=question, inline=False)
            embed.set_field_at(index=1,name="**Answer/Definition:**",value=f"||{answer}||", inline=False)
            self.flipped = False
            await interaction.response.edit_message(view=self,embed=embed)
            return

        # Extract the question and answer to the flashcard
        question = embed.fields[0].value
        answer = embed.fields[1].value[2:-2]

        # Flip the question and answer
        embed.set_field_at(index=0,name="Question/Term:",value=answer, inline=False)
        embed.set_field_at(index=1,name="**Answer/Definition:**",value=f"||{question}||", inline=False)
        self.flipped = True
        await interaction.response.edit_message(view=self,embed=embed)



# /flashcard <question/term> <answer/definition>
@bot.slash_command(guild_ids=[1077368721556901988], name="flashcard", description="Create a flashcard.")
@option("question", description="What is the term/question?")
@option("answer", description="Enter the first answer/definition")
async def flashcard(
    ctx: discord.ApplicationContext,
    question: str,
    answer: str,
):
    # Notifies the user they've successfully created a reminder
    embed = discord.Embed(title="Flashcard", description="Click on the answer to reveal it or reverse the flashcard", color=0xfca311)
    embed.add_field(name="Question/Term:", value=question, inline=False)
    embed.add_field(name="**Answer/Definition:**",value=f"||{answer}||", inline=False)
    await ctx.respond(embed=embed,view=FlashcardView())


# --------------------------------------------------------------------------------------------------------------------------------------------
# HELP


# /help
@bot.slash_command(guild_ids=[1077368721556901988], name="help", description="Help for StudyBot commands")
async def help(ctx: discord.ApplicationContext):

    embed = discord.Embed(title="StudyBot Help", description="Welcome to StudyBot! Below are a list of all of my commands and an example of how to use them!\nAll of my commands are slash commands, so type `/` to find them!", color=0xff0054)
    embed.add_field(name="/remindme <when> <day/hr/min/sec> <reminder message>", value="Use this to set a reminder for yourself! E.g. \n`/remindme 5 minutes 'Do the dishes'`", inline=False)
    embed.add_field(name="/remind <user> <when> <day/hr/min/sec> <reminder message>", value="If you want to remind another user. E.g. \n`/remind @JohnDoe 10 hours 'Sleep'`", inline=False)
    embed.add_field(name="/newtask <task description>", value="If you want to add a new item to your TODO list. You can also check/delete all commands through 2 buttons. E.g. \n`/newtask 'Finish Math homework'`", inline=False)
    embed.add_field(name="/finishtask <task number>", value="Once you've completed a task you can check it off with this command. E.g. \n`/finishtask 2`", inline=False)
    embed.add_field(name="/poll <question> <option 1> <option 2>", value="This command creates a 2 option poll for everyone in the server. E.g. \n`/poll 'Does pineapple belong on pizza?' 'Of course' 'Absolutely'`", inline=False)
    embed.add_field(name="/study <topic of study>", value="Want to keep track of how long you've studied? Use this command to set a study session. E.g. \n`/study 'Math'`", inline=False)
    embed.add_field(name="/flashcard <question/term> <answer/definition>", value="If you study best using flashcards, you can use this command to create your own reversible flashcard! E.g. \n`/flashcard 'StudyBot' 'Incredibly helpful'`", inline=False)
    embed.add_field(name="/newroom <name of room> <text channel or voice channel>", value="Want to create a private study room for you and your friends? E.g. \n`/newroom 'Chemistry' 'Text-Channel'`", inline=False)
    await ctx.respond(embed=embed)



# --------------------------------------------------------------------------------------------------------------------------------------------



def main():
  bot.run(TOKEN)

if __name__ == '__main__':
  main()
