# How to run the Terraria ChatBot:

### Step 1: Get the Llama3.2:3B
- Access the Ollama website: https://ollama.com/
- Install Ollama.
- Open terminal: ollama run llama3.2
After downloading the model, you can move on to the next steps.

### Step 2: Setup the environment
On your terminal:
- (Optional, recommended) Create a virtual environment and activate it
- Install the libraries by: pip install -r requirements.txt
- Rename the "blank.env" to ".env" and then fill in with your API keys and authentication secret.

### Step 3: Retrieve and break down information
Still on your terminal:
- Run the web scraping file (By default, it scrapes the information of the boss "Skeletron Prime", which is also our experiment subject): python web_scraping.py
- Run the ingest file: python ingest.py

### Step 4: Run the chatbot
Still on your terminal:
- Run the main file: chainlit run main.py
