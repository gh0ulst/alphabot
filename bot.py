# -*- coding: utf-8 -*-
"""bot.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1fSqtu9SePo0n9mJpVcGR0HuYDbZrUWuR
"""

import discord
import openai
import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import asyncio

# ==== YOUR KEYS ====
DISCORD_TOKEN = 'MTM2NjIyNTgzNjA4ODM2NTE3OA.GMihte.XGcWCgvnLFbki_79RuFM3OZ6x6szPzmAhNKFPc'
OPENAI_API_KEY = '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'

openai.api_key = OPENAI_API_KEY

# ==== Global Variables ====
faq_articles = []
vectorizer = TfidfVectorizer()
faq_vectors = None

# ==== Scrape FAQ Content ====
def fetch_faq_articles():
    url = "https://help.alpha-futures.com/en/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    texts = []

    for article in soup.find_all(['h1', 'h2', 'h3', 'p', 'li']):
        text = article.get_text().strip()
        if text and len(text) > 20:  # Only meaningful texts
            texts.append(text)

    return texts

# ==== Refresh FAQ Content ====
def refresh_faq():
    global faq_articles, vectorizer, faq_vectors
    faq_articles = fetch_faq_articles()
    faq_vectors = vectorizer.fit_transform(faq_articles)
    print("FAQ content refreshed!")

# ==== Find Best Match ====
def find_best_match(question):
    question_vec = vectorizer.transform([question])
    similarities = cosine_similarity(question_vec, faq_vectors)
    best_idx = similarities.argmax()
    best_score = similarities[0, best_idx]
    if best_score < 0.2:  # Low confidence
        return None
    return faq_articles[best_idx]

# ==== Generate AI Reply ====
async def generate_reply(user_question):
    best_context = find_best_match(user_question)

    if not best_context:
        return "Sorry, I couldn't find a matching answer from the FAQ."

    prompt = f"""
You are Alpha Futures FAQ Bot.
ONLY answer based on the FAQ content provided below.
If you are unsure or the information is not covered, say you don't know.

FAQ Content:
{best_context}

User Question:
{user_question}

Answer:"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=500,
        )

        answer = response.choices[0].message['content'].strip()
        return answer
    except Exception as e:
        return f"Error generating reply: {str(e)}"

# ==== Setup Discord Bot ====
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = discord.Bot(intents=intents)

# ==== Background Task to Refresh FAQ ====
async def refresh_faq_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        refresh_faq()
        await asyncio.sleep(86400)  # Refresh every 24 hours

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}!')
    try:
        synced = await bot.sync_commands()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    bot.loop.create_task(refresh_faq_task())

# ==== Slash Commands ====

@bot.slash_command(name="faq", description="Ask a question about Alpha Futures!")
async def faq(ctx, question: discord.Option(str, "Type your question")):
    await ctx.defer()
    reply = await generate_reply(question)

    embed = discord.Embed(
        title="Alpha Futures FAQ Answer",
        description=reply,
        color=discord.Color.blue()
    )
    embed.set_footer(text="Asked via /faq command • Powered by Alpha Futures Help Center")

    await ctx.followup.send(embed=embed)

@bot.slash_command(name="help", description="How to use the Alpha FAQ Bot")
async def help_command(ctx):
    embed = discord.Embed(
        title="How to Use Alpha FAQ Bot",
        description=(
            "**Use `/faq` to ask any question about Alpha Futures!**\n\n"
            "- Example: `/faq How do I deposit funds?`\n"
            "- I'll answer based ONLY on the official FAQ.\n\n"
            "_If your question is not in the FAQ, I'll let you know!_"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text="Alpha Futures FAQ Bot Help")

    await ctx.respond(embed=embed)

# ==== Start Bot ====
refresh_faq()
bot.run(DISCORD_TOKEN)