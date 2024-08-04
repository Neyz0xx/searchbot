import os
import re
import discord
import aiofiles
import asyncio
from queue import Queue
from discord.ext import commands
import os
import time
from keep_alive import keep_alive
import base64
import requests
import aiohttp
import numlookupapi

keep_alive()
ipinfo_token = ""
token = os.environ.get("token")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
numlookup_api_key = os.environ.get("numlookupapi")
client = numlookupapi.Client(numlookup_api_key)





@bot.command()
async def close(ctx):
    await ctx.send("Shutting down...")
    await bot.close()


async def get_geoip_info(ip_address):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://ipinfo.io/{ip_address}/json?token={ipinfo_token}") as response:
            if response.status != 200:
                return None
            data = await response.json()
            return data
            
#############################################



SEARCH_TYPES = ["email", "username", "name", "password", "hash", "lastip"]

def decode_key(encoded_key):
    decoded_bytes = base64.b64decode(encoded_key.encode('utf-8'))
    return decoded_bytes.decode('utf-8')

async def search_snusbase(search_input, search_type):
    api_key_encoded = os.environ.get("apikey")
    api_key = decode_key(api_key_encoded)

    url = 'https://api-experimental.snusbase.com/data/search'
    headers = {
        'Auth': api_key,
        'Content-Type': 'application/json'
    }
    payload = {
        'terms': [search_input],
        'types': [search_type],
        'wildcard': False
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get('results', {})
    else:
        return {"error": response.text}

def format_results(results):
    if not results:
        return "Aucun résultat trouvé dans la DB."
    output = []
    for database, entries in results.items():
        for entry in entries:
            for key, value in entry.items():
                output.append(f"{key}: {value}")
            output.append('-' * 50)
    return "\n".join(output)

@bot.command()
async def search(ctx, search_type: str, *, search_input: str):
    if search_type not in SEARCH_TYPES:
        await ctx.send(f"Invalid search type. Please use one of the following: {', '.join(SEARCH_TYPES)}")
        return

    results = await search_snusbase(search_input, search_type)
    if "error" in results:
        await ctx.send(f"Error: {results['error']}")
    else:
        formatted_results = format_results(results)
        await ctx.send(formatted_results)



#############################################


@bot.command(name="geoip")
async def geoip(ctx, *, ip_address: str):
    
    ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    if not ip_pattern.match(ip_address):
        await ctx.send("Adresse IP invalide.")
        return
    
    try:
        geoip_info = await get_geoip_info(ip_address)
        if not geoip_info:
            await ctx.send("Impossible de récupérer les informations de localisation pour cette adresse IP.")
            return
        
        embed = discord.Embed(title=f"Informations pour l'adresse IP : {ip_address}")
        embed.add_field(name="IP", value=ip_address)
        embed.add_field(name="Ville", value=geoip_info.get('city', 'Non disponible'), inline=False)
        embed.add_field(name="Région", value=geoip_info.get('region', 'Non disponible'), inline=False)
        embed.add_field(name="Pays", value=geoip_info.get('country', 'Non disponible'), inline=False)
        embed.add_field(name="Organisation", value=geoip_info.get('org', 'Non disponible'), inline=False)
        embed.set_footer(text="lookup, made by xdatabase")
        await ctx.send(f"Consultez vos MP, je vous ai envoyé les détails pour l'adresse IP: {ip_address}, {ctx.author.mention} .")
        await ctx.author.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite : {e}")



@bot.command()
async def lookup(ctx, phone_number: str):
    """Commande pour rechercher des informations sur un numéro de téléphone."""
    # Préparez l'URL de la requête avec le numéro de téléphone et la clé API.
    url = f"https://api.numlookupapi.com/v1/validate/{phone_number}"
    headers = {
        'x-api-key': NUMLOOKUPAPI_KEY  # La clé API doit être une chaîne de caractères.
    }

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        if response.status_code == 200:
            # Créez un embed avec les informations retournées par l'API.
            embed = discord.Embed(title="Informations du Numéro de Téléphone", color=discord.Color.blue())
            embed.add_field(name="Numéro", value=data.get('international_format', 'N/A'), inline=False)
            embed.add_field(name="Pays", value=data.get('country', 'N/A'), inline=False)
            embed.add_field(name="Type de Ligne", value=data.get('line_type', 'N/A'), inline=False)
            embed.add_field(name="Opérateur", value=data.get('carrier', 'N/A'), inline=False)
            embed.add_field(name="Validité", value=data.get('valid', 'N/A'), inline=False)

            # Envoyez l'embed dans le canal Discord.
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Erreur: Impossible d'obtenir les informations pour le numéro {phone_number}.")
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite: {e}")



# Start the bot with your token
bot.run(token)
