import yt_dlp

ydl_opts = {
    'quiet': True,
    'default_search': 'ytsearch',
    'max_downloads': 20,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    search_info = ydl.extract_info('funny cats', download=False)
    print(search_info['entries'])
