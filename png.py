import os
import discord # type: ignore
from discord.ext import commands # type: ignore
import re
from PIL import Image
import requests
from io import BytesIO
from bs4 import BeautifulSoup
 

# Set up your Discord bot token
TOKEN = os.environ.get('TOKEN')
# GUILD_ID = '1305812477547642891'  # Optional, if you want to specify a guild
CHANNEL_ID = '1305812477547642891'  # Channel where the message with the file was sent
# Membuat objek Intents untuk memungkinkan akses ke pesan dan lainnya
intents = discord.Intents.default()
intents.message_content = True  # Mengaktifkan akses ke isi pesan
# Membuat objek client dengan intents yang sudah ditentukan
client = discord.Client(intents=intents)
# Membuat objek bot dengan intents yang sudah ditentukan
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Command untuk memeriksa pesan terbaru dan mengirim gambar PNG
@bot.command()
async def c(ctx):
    # Ambil channel dari server (guild) dan ID channel
    channel = bot.get_channel(int(CHANNEL_ID))
    
    # Ambil pesan terakhir di channel menggunakan async for
    async for message in channel.history(limit=1):  # Hanya mengambil 1 pesan terakhir
        print(f"Memeriksa pesan terbaru: {message.content}")
        
        # Cari URL gambar dengan regex (mencocokkan link gambar atau halaman)
        image_urls = find_image_urls(message.content)
        
        if image_urls:
            for image_url in image_urls:
                print(f"URL gambar ditemukan: {image_url}")
                # Cek apakah URL adalah halaman web dan ambil gambar dari halaman tersebut
                if not image_url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    # Jika URL adalah halaman, ambil gambar dari halaman tersebut
                    await fetch_image_from_page(image_url, channel)
                else:
                    # Jika URL sudah mengarah ke gambar, langsung download dan kirim
                    await download_and_send_image(image_url, channel)
        else:
            print("Tidak ada URL gambar yang ditemukan dalam pesan.")

# Function untuk mencari URL gambar dalam pesan
def find_image_urls(text):
    # Regex untuk mencari URL gambar (ext: png, jpg, jpeg, gif) atau halaman yang mungkin berisi gambar
    url_pattern = r'https?://[^\s]+(?:\.jpg|\.jpeg|\.png|\.gif|/share/contents/preview/[^\s]+)'
    return re.findall(url_pattern, text)

# Function untuk mengambil gambar dari halaman web
async def fetch_image_from_page(url, channel):
    print(f"Mencari gambar di halaman: {url}")
    
    # Mengambil HTML dari URL
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Mencari gambar menggunakan tag <meta> dengan property og:image
        meta_tag = soup.find("meta", property="og:image")
        
        if meta_tag and meta_tag.get("content"):
            img_url = meta_tag["content"]
            print(f"Gambar ditemukan melalui og:image: {img_url}")
            # Coba unduh dan kirim gambar
            await download_and_send_image(img_url, channel)
        else:
            print("Tidak menemukan tag og:image, mencoba mencari gambar lain di halaman.")
            # Jika tidak ada og:image, coba mencari gambar dalam tag <img>
            img_tags = soup.find_all('img')
            for img in img_tags:
                img_url = img.get('src')
                if img_url:
                    if not img_url.startswith('http'):
                        # Jika URL gambar relatif, bangun URL absolut
                        img_url = f'{url}{img_url}'
                    print(f"Gambar ditemukan di halaman: {img_url}")
                    # Coba unduh dan kirim gambar
                    await download_and_send_image(img_url, channel)
                    return
    else:
        print(f"Gagal mengambil halaman, status code: {response.status_code}")

# Function untuk mengunduh dan mengirim gambar dalam format PNG
async def download_and_send_image(image_url, channel):
    print(f"Mendownload gambar dari URL: {image_url}")
    try:
        # Menggunakan requests untuk mendownload gambar
        response = requests.get(image_url)
        
        # Periksa status code dari respons HTTP
        if response.status_code == 200:
            print(f"Gambar berhasil didownload. Ukuran gambar: {len(response.content)} bytes")
            # Membaca gambar dari response
            image_data = BytesIO(response.content)

            # Mengonversi gambar ke format PNG menggunakan Pillow (PIL)
            image = Image.open(image_data)
            png_image_data = BytesIO()  # Menyiapkan tempat untuk gambar PNG
            image.save(png_image_data, format='PNG')  # Simpan sebagai PNG
            png_image_data.seek(0)  # Reset pointer untuk mengirimkan file
            
            # Kirim gambar dalam format PNG ke channel
            await channel.send(file=discord.File(png_image_data, 'RUET_Thumbnail.png'))
            print('Gambar berhasil dikirim ke channel!')
        else:
            print(f"Gagal mendownload gambar, status code: {response.status_code}")
    except Exception as e:
        print(f"Terjadi kesalahan saat mendownload atau mengirim gambar: {e}")

# Jalankan bot
bot.run(TOKEN)