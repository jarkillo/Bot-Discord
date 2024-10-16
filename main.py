import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import os
from dotenv import load_dotenv
import asyncio

load_dotenv("token.env")
token = os.getenv('DISCORD_TOKEN')

# Solo incluir los intents necesarios
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="?", intents=intents)

# Variables globales para almacenar la cola
song_queue = []

# Configuración de yt_dlp
ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': 'False',
    'quiet': True,
    'extract_flat': True,
    'source_address': '0.0.0.0',
}
itag_list = [141, 140, 139, 251, 171, 250, 249]

@bot.event
async def on_ready():
    print(f'{bot.user} está conectado!')

@bot.command()
async def join(ctx):
    """Conectar el bot al canal de voz"""
    if ctx.voice_client:
        await ctx.send("Ya estoy conectado a un canal de voz.")
    elif ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("Tienes que estar en un canal de voz para que el bot se conecte.")

@bot.command()
async def leave(ctx):
    """Desconectar el bot del canal de voz"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Me he desconectado del canal de voz.")
    else:
        await ctx.send("No estoy conectado a ningún canal de voz.")

@bot.command()
async def play(ctx, url: str):
    """Reproducir música desde una URL de YouTube o playlist"""
    # Si no está en un canal de voz, se conecta automáticamente
    if not ctx.voice_client:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
        else:
            await ctx.send("Tienes que estar en un canal de voz para que el bot se conecte.")
            return

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Verifica si el video es privado
            if info.get("is_private", False):
                await ctx.send("Este video es privado y no puede ser reproducido.")
                return

            # Busca el primer formato de audio disponible
            stream_url = None
            for fmt in info.get('formats', []):
                if fmt.get('acodec') != 'none':  # Verificar si tiene un códec de audio
                    stream_url = fmt.get('url')
                    break

            if not stream_url:
                await ctx.send("No se encontró un formato de audio compatible.")
                return

    except Exception as e:
        await ctx.send(f"Error al reproducir el video: {str(e)}")
        return

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -ar 48000 -maxrate 128k -bufsize 1M'
    }

    await asyncio.sleep(1)
    ctx.voice_client.play(discord.FFmpegOpusAudio(source=stream_url, **ffmpeg_options),
                          after=lambda e: print(f"Error: {e}") if e else None)
    await ctx.send(f"Reproduciendo: {info['title']}")

    if not ctx.voice_client.is_playing():
        await play_next(ctx)


async def play_next(ctx):
    """Reproducir la siguiente canción en la cola"""
    if len(song_queue) > 0:
        url = song_queue.pop(0)
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['formats'][0]['url']
            ctx.voice_client.play(discord.FFmpegPCMAudio(executable="C:/ffmpeg/bin/ffmpeg.exe", source=url2),
                                  after=lambda e: bot.loop.create_task(play_next(ctx)))
            await ctx.send(f"Reproduciendo ahora: {info['title']}")
    else:
        await ctx.send("La cola está vacía.")


async def play_next(ctx):
    """Reproducir la siguiente canción en la cola"""
    if len(song_queue) > 0:
        url = song_queue.pop(0)
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['formats'][0]['url']
            ctx.voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg/bin/ffmpeg.exe", source=url2),
                                  after=lambda e: bot.loop.create_task(play_next(ctx)))
            await ctx.send(f"Reproduciendo ahora: {info['title']}")
    else:
        await ctx.send("La cola está vacía.")

@bot.command()
async def queue(ctx):
    """Mostrar las canciones en la cola"""
    if len(song_queue) == 0:
        await ctx.send("La cola está vacía.")
    else:
        await ctx.send(f"Canciones en la cola: {', '.join(song_queue)}")

@bot.command()
async def skip(ctx):
    """Saltar a la siguiente canción"""
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Canción saltada.")
        await play_next(ctx)

@bot.command()
async def stop(ctx):
    """Detener la música"""
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("Música detenida.")
    else:
        await ctx.send("No hay música reproduciéndose.")

@bot.command()
async def sintetika_mix(ctx):
    """Reproducir la lista de reproducción Sintetika Mix"""
    url = "https://www.youtube.com/playlist?list=PLgCeG97g1zB9jqqaT4zDFPJFq08G1Ddn9"
    if not ctx.voice_client:
        await ctx.send("Primero necesito unirme a un canal de voz. Usa ?join")
        return

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        for entry in info['entries']:
            if 'webpage_url' in entry:
                song_queue.append(entry['webpage_url'])
        await ctx.send(f"Lista de reproducción 'Sintetika Mix' añadida.")

    if not ctx.voice_client.is_playing():
        await play_next(ctx)

# Ejecutar el bot con el token
bot.run(token)
