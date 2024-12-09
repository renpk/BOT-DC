import os
import discord  # type: ignore
from discord.ext import commands  # type: ignore
import re
from PIL import Image
from aiohttp import ClientSession
from io import BytesIO
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Set up your Discord bot token
load_dotenv()  # Load .env file
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    raise ValueError("Token tidak ditemukan. Pastikan file .env berisi TOKEN.")

CHANNEL_ID = '1305812477547642891'  # Channel ID

# Membuat objek Intents untuk memungkinkan akses ke pesan dan lainnya
intents = discord.Intents.default()
intents.message_content = True

# Membuat objek bot dengan intents yang sudah ditentukan
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Command untuk memeriksa pesan terbaru dan mengirim gambar PNG
@bot.command()
async def c(ctx):
    channel = bot.get_channel(int(CHANNEL_ID))
    if not channel:
        print("Channel tidak ditemukan.")
        return

    # Ambil pesan terakhir di channel
    async for message in channel.history(limit=1):
        print(f"Memeriksa pesan terbaru: {message.content}")

        # Cari URL gambar dengan regex
        image_urls = find_image_urls(message.content)

        if image_urls:
            async with ClientSession() as session:
                for image_url in image_urls:
                    print(f"URL gambar ditemukan: {image_url}")
                    if not image_url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        await fetch_image_from_page(image_url, channel, session)
                    else:
                        await download_and_send_image(image_url, channel, session)
        else:
            print("Tidak ada URL gambar yang ditemukan dalam pesan.")

# Function untuk mencari URL gambar dalam pesan
def find_image_urls(text):
    url_pattern = r'https?://[^\s]+(?:\.(?:jpg|jpeg|png|gif)|/share/contents/preview/[^\s]+)'
    return re.findall(url_pattern, text)

# Function untuk mengambil gambar dari halaman web
async def fetch_image_from_page(url, channel, session):
    print(f"Mencari gambar di halaman: {url}")
    async with session.get(url) as response:
        if response.status == 200:
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')

            meta_tag = soup.find("meta", property="og:image")
            if meta_tag and meta_tag.get("content"):
                img_url = meta_tag["content"]
                print(f"Gambar ditemukan melalui og:image: {img_url}")
                await download_and_send_image(img_url, channel, session)
            else:
                print("Tidak menemukan tag og:image, mencoba mencari gambar lain di halaman.")
                img_tags = soup.find_all('img')
                for img in img_tags:
                    img_url = img.get('src')
                    if img_url:
                        if not img_url.startswith('http'):
                            img_url = f'{url}{img_url}'
                        print(f"Gambar ditemukan di halaman: {img_url}")
                        await download_and_send_image(img_url, channel, session)
                        return
        else:
            print(f"Gagal mengambil halaman, status code: {response.status}")

# Function untuk mengunduh dan mengirim gambar dalam format PNG
async def download_and_send_image(image_url, channel, session):
    print(f"Mendownload gambar dari URL: {image_url}")
    try:
        async with session.get(image_url) as response:
            if response.status == 200:
                image_data = BytesIO(await response.read())
                image = Image.open(image_data)
                png_image_data = BytesIO()
                image.save(png_image_data, format='PNG')
                png_image_data.seek(0)

                await channel.send(file=discord.File(png_image_data, 'converted_image.png'))
                print("Gambar berhasil dikirim ke channel!")
            else:
                print(f"Gagal mendownload gambar, status code: {response.status}")
    except Exception as e:
        print(f"Terjadi kesalahan saat mendownload atau mengirim gambar: {e}")

# Jalankan bot
bot.run(TOKEN)