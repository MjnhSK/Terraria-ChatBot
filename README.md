# How to run the Terraria Chat Bot:

### Step 1: Get the Llama3.2:3B
Access the Ollama website: 

### Step 2: Install the necessary libraries
On your terminal:
- (Optional, recommended) Create a virtual environment and activate it
- Install the libraries by: pip install -r requirements.txt

### Step 3: Retrieve and break down information
Still on your terminal:
- Run the web scraping file (By default, it scrapes the information of the boss "Skeletron Prime", which is also our experiment subject): python web_scraping.py
- Run the ingest file: python ingest.py

### Step 4: Run the chat bot
Still on your terminal:
- Run the main file: chainlit run main.py