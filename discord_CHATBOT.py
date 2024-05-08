import discord
import asyncio
import requests
from datetime import datetime, timedelta
import os

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.presences = True
intents.members = True
intents.guilds = True
client = discord.Client(intents=intents)

last_message_time = {}
inactivity_threshold = 60

def load_personality():
    try:
        with open('personality.txt', 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return "Your name is Chode. Always answer with short, direct answers."

def generate_response(conversation_text, guild):
    personality = load_personality()
    url = "http://localhost:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "lmstudio-community/Phi-3-mini-4k-instruct-GGUF",
        "messages": [
            {"role": "system", "content": personality},
            {"role": "user", "content": conversation_text}
        ],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json()["choices"][0]["message"]['content']
    except requests.RequestException as e:
        return f"Error: Failed to generate response due to {str(e)}"

def log_chat_history(message):
    try:
        timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
        with open('chat_history.txt', 'a') as file:
            file.write(f"[{timestamp}] {message.author.display_name}: {message.content}\n")
        update_user_profile(message.author)
    except Exception as e:
        print(f"Failed to log message: {str(e)}")

def update_user_profile(user):
    try:
        profiles = {}
        if os.path.exists('user_profiles.txt'):
            with open('user_profiles.txt', 'r') as file:
                profiles = eval(file.read())
        profiles[user.id] = {
            'last_seen': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'name': user.display_name
        }
        with open('user_profiles.txt', 'w') as file:
            file.write(str(profiles))
    except Exception as e:
        print(f"Failed to update user profile: {str(e)}")

def get_member_statuses(guild):
    statuses = []
    for member in guild.members:
        if member.status != discord.Status.offline:
            status = f"{member.display_name} ({member.status})"
            statuses.append(status)
    return '\n'.join(statuses)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')
    client.loop.create_task(check_inactivity())

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    log_chat_history(message)
    last_message_time[message.channel.id] = datetime.utcnow()

    if 'chode' in message.content.lower():
        conversation_text = f"{message.author.display_name} mentioned Chode: {message.content}"
        async with message.channel.typing():
            response_from_lm = generate_response(conversation_text, message.guild)  # Pass guild object
            await message.channel.send(response_from_lm)

    if 'status check' in message.content.lower():
        statuses = get_member_statuses(message.guild)
        if statuses:
            await message.channel.send(f"Here are the currently online members:\n{statuses}")
        else:
            await message.channel.send("No members are currently online.")

async def check_inactivity():
    while True:
        now = datetime.utcnow()
        for channel_id, timestamp in list(last_message_time.items()):
            if now - timestamp > timedelta(minutes=inactivity_threshold):
                channel = client.get_channel(channel_id)
                if channel:
                    async with channel.typing():
                        prompt = "No one has said anything in a while. Check who is online and maybe send them a message using the @ function."
                        response = generate_response(prompt, channel.guild)  # Pass guild object
                        await channel.send(response)
                last_message_time[channel_id] = now
        await asyncio.sleep(60)




client.run('YOUR DISCORD BOT TOKEN')



