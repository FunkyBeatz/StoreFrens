# Flask setup to keep the bot alive
import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    # Use the PORT environment variable assigned by Render
    port = int(os.environ.get('PORT', 8080))  # Default to 8080 if no port is assigned
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()


# Using this 2nd folder only to make it work in Vercel