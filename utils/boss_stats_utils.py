import requests
from bs4 import BeautifulSoup
import json
import re
def extract_forms(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    # Dictionary to hold the form HTML content
    form_dict = {}
    
    # Find all 'title' divs
    titles = soup.find_all('div', class_='title')
    
    # Initialize last_title as None
    last_title = None
    
    for title in titles:
        current_title = title.get_text(separator=" ", strip=True)
        # print('Current Title:', current_title)
        
        # Check if the current title is "Statistics"
        if current_title == "Statistics" and last_title:
            # Get the form name from the 'namesub' span in the last title
            namesub = title.find('span', class_='namesub')
            # if namesub:
            #     print('Namesub:', namesub.get_text(strip=True))
                
                # Extract the entire 'infobox' div containing the form details
            form_content = title.find_parent('div', class_='infobox')
            form_dict[last_title] = str(form_content)
        
        # Update last_title to be the current title for the next iteration
        last_title = current_title
    
    return form_dict

def get_stat(statContent, form_key):

    # Parse the HTML content
    soup = BeautifulSoup(statContent, 'html.parser')

    # Create a dictionary to store the extracted information
    data = {}

    # Define headers to exclude
    excluded_headers = ['Debuff', 'Debuff tooltip', 'Duration', 'Chance']

    # Find all the rows in the table
    for tr in soup.find_all('tr'):
        # Check if there's a <th> element in the row
        header_tag = tr.find('th')
        if header_tag:
            header = header_tag.get_text(strip=True)

            # Skip excluded headers
            if header in excluded_headers:
                continue

            data_cell = tr.find('td')
            
            if data_cell:
                # Initialize extracted_data list to collect all relevant text
                extracted_data = []
                
                remaining_text = data_cell.get_text(separator=" ", strip=True)
                if remaining_text:
                    extracted_data.append(remaining_text)

                # Add the result to the dictionary, handling empty extracted_data cases
                data[header] = extracted_data if len(extracted_data) > 1 else (extracted_data[0] if extracted_data else '')

    data['Type'] = extract_type(statContent)

    data['Environment'] = extract_environment(statContent)

    damage_dict = extract_damage(statContent)
    if not damage_dict:
        damage_dict = 'Varies per attack'
    data['Damage'] = damage_dict

    data['Max Life'] = extract_max_life(statContent)
    data['Defense'] = extract_defense(statContent)

    data['Immune to'] = extract_immunity_info(statContent)
    data['Knockback resist'] = extract_KBR(statContent)
    if data.get('Coins'):  # This will safely check if 'Coins' exists and is not None or empty
        data['Coins'] = coin_splitter(data['Coins'])
        coin_lst = data['Coins'].split(' , ')
        data['Coins'] = {'Normal': coin_lst[0], 'Expert': coin_lst[1], 'Master': coin_lst[1]}

    data['Title'] = form_key

    return data

def extract_audio(data_dict):
    # List to store keys with audio links
    audio = {}
    
    # Iterate through the dictionary
    for key, value in data_dict.items():
        # Check if the value is a string and contains an audio file link
        if isinstance(value, str) and ('wav' in value or 'mp3' in value):
            audio[key] = value
        # Check if the value is a list with audio links
        elif isinstance(value, list):
            if any('wav' in item or 'mp3' in item for item in value):
                audio[key] = value
    # print(audio)
    
    return audio

def extract_type(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    # List to store type values
    type_data = []
    
    # Locate the 'Type' row
    type_row = soup.find('th', string=lambda text: 'Type' in text)
    
    if type_row:
        # Find the containing <td> cell with the type values
        type_cell = type_row.find_next_sibling('td')
        
        # Check if type_cell exists
        if type_cell:
            # Find all span tags with the class 'nowrap tag'
            for tag in type_cell.find_all('span', class_='nowrap tag'):
                # Check if there is an <a> tag within the <span>
                type_name = tag.find('a')
                if type_name:
                    # If there's an <a> tag, extract its text
                    type_data.append(type_name.get_text(strip=True))
                else:
                    # If there's no <a> tag, extract the text from the <span> itself
                    type_data.append(tag.get_text(strip=True))
    
    # Return the type data as a list or empty list if none found
    return type_data if type_data else None

from bs4 import BeautifulSoup

def extract_loot_items(html, class_tag):
    soup = BeautifulSoup(html, 'html.parser')
    loot_items = soup.find_all('li', class_=class_tag) if soup else []
    
    extracted_items = []
    for item in loot_items:
        item_name_span = item.find('span', class_='i')
        percentage_div = item.find('div')
        number_span = item.find('span', class_='nowrap')
        
        if item_name_span and percentage_div:
            item_name = item_name_span.get_text(strip=True)
            next_div = percentage_div.find_next_sibling('div')
            percentage = next_div.get_text(strip=True) if next_div else 'N/A'
            number_range = number_span.get_text(strip=True) if number_span else '1'
            extracted_items.append((item_name, percentage, number_range))
    
    return extracted_items if extracted_items else [('No loot items found', 'N/A', 'N/A')]

def combine_loot(loot_sources):
    loot_list = []
    for loot in loot_sources:
        for item in loot:
            if item[1] != 'N/A':
                text_loot = f"Item: {item[0]}, Percentage: {item[1]}, Quantity: {item[2]}"
                loot_list.append(text_loot)
    return loot_list

def extract_environment(html):
    soup = BeautifulSoup(html, 'html.parser')
    environment_data = []
    
    environment_row = soup.find('a', title='Environment') if soup else None
    if environment_row:
        tags_div = environment_row.find_parent('tr').find('div', class_='tags')
        if tags_div:
            for tag in tags_div.find_all('span', class_='tag'):
                environment_data.append(tag.get_text(strip=True))
    
    return environment_data if environment_data else None

def extract_damage(html):
    soup = BeautifulSoup(html, 'html.parser')
    damage_data = {}
    
    damage_row = soup.find('th', string="Damage") if soup else None
    if damage_row:
        damage_cell = damage_row.find_next_sibling('td')
        current_mode_data = []
        current_note = None
        
        if damage_cell:
            for span in damage_cell.find_all(['span', 'br', 'sup']):
                if 'm-normal' in span.get('class', []):
                    current_mode_data.append(('Normal', span.get_text(strip=True)))
                elif 'm-expert' in span.get('class', []):
                    current_mode_data.append(('Expert', span.get_text(strip=True)))
                elif 'm-master' in span.get('class', []):
                    current_mode_data.append(('Master', span.get_text(strip=True)))
                elif 'note-text' in span.get('class', []):
                    current_note = span.get_text(strip=True)
                elif span.name == 'br':
                    if current_mode_data:
                        damage_data[current_note] = current_mode_data
                        current_mode_data = []
                        current_note = None
        
            if current_mode_data:
                damage_data[current_note] = current_mode_data

    return damage_data if damage_data else '(Varies per attack)'

def extract_max_life(html):
    soup = BeautifulSoup(html, 'html.parser')
    max_life_data = {}
    
    max_life_row = soup.find('th', string="Max Life") if soup else None
    if max_life_row:
        max_life_cell = max_life_row.find_next_sibling('td')
        if max_life_cell:
            for span in max_life_cell.find_all('span'):
                if 'm-normal' in span.get('class', []):
                    max_life_data['Normal'] = span.get_text(strip=True)
                elif 'm-expert' in span.get('class', []):
                    max_life_data['Expert'] = span.get_text(strip=True)
                elif 'm-master' in span.get('class', []):
                    max_life_data['Master'] = span.get_text(strip=True)
    
    return max_life_data if max_life_data else None

def extract_defense(html):
    soup = BeautifulSoup(html, 'html.parser')
    defense_data = {'Base':'N/A','Increased Defense':'N/A'}

    defense_row = soup.find('th', string=lambda text: text and 'Defense' in text) if soup else None
    if defense_row:
        defense_cell = defense_row.find_next_sibling('td')
        if defense_cell:
            base_defense = defense_cell.find('span', class_='m-all')
            if base_defense:
                defense_data['Base'] = base_defense.get_text(strip=True)
                additional_text = defense_cell.get_text(separator=" ", strip=True).replace(defense_data.get('Base', ''), "").strip()
                if additional_text:
                    defense_data['Increased Defense'] = additional_text
                
            else:
                base_defense = defense_cell.get_text(separator=" ", strip=True).replace(defense_data.get('Base', ''), "").strip()
                additional_parts = base_defense.split('/')
                if len(additional_parts) == 2:
                    def_dict = {}
                    def_dict['Normal'] = additional_parts[0].strip()
                    def_dict['Expert'] = additional_parts[1].strip()
                    def_dict['Master'] = additional_parts[1].strip()
                    

                    defense_data['Base'] = def_dict
                else:
                    defense_data['Base'] = base_defense

    return defense_data if defense_data else None

def extract_KBR(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Find all rows containing knockback resist data
    kb_resist_rows = soup.find_all('tr')
    kb_resist_dict= {}

    for row in kb_resist_rows:
        # Check if the row has a <th> with the title "Knockback"
        th = row.find('a', title='Knockback')
        if th:
            all_resist = row.find('span', class_='m-all')
            if all_resist:
                # Apply value for all modes
                resist_value = all_resist.get_text(strip=True)
                kb_resist_dict = {
                    'Normal': resist_value,
                    'Expert': resist_value,
                    'Master': resist_value
                }
            else:
                # Extract specific mode values
                normal_resist = row.find('span', class_='m-normal')
                expert_resist = row.find('span', class_='m-expert')
                master_resist = row.find('span', class_='m-master')

                # Store values in the dictionary
                kb_resist_dict = {
                    'Normal': normal_resist.get_text(strip=True) if normal_resist else 'N/A',
                    'Expert': expert_resist.get_text(strip=True) if expert_resist else 'N/A',
                    'Master': master_resist.get_text(strip=True) if master_resist else 'N/A'
                }
    return kb_resist_dict

def extract_immunity_info(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Try to find the td with class 'immunities' first
    immunities_td = soup.find('td', class_='immunities')
    
    if immunities_td:
        links = immunities_td.find_all('a')
        titles = [link.get('title', 'N/A') for link in links] if links else []
        return titles if titles else ['All debuffs except Whip debuffs']

    # If 'immunities' class is not found, check for the 'Immune to' th
    immune_info_th = soup.find('th', string='Immune to')
    if immune_info_th:
        # Find the parent <tr> of the <th>
        immune_info_row = immune_info_th.find_parent('tr')
        if immune_info_row:
            immune_info_td = immune_info_row.find('td')
            if immune_info_td:
                # Extract text and links from the td, ensuring spaces are preserved
                immune_info_text = ' '.join(immune_info_td.stripped_strings)
                
                # If the text contains 'All', return the full text
                if 'All' in immune_info_text:
                    return [immune_info_text]
                else:
                    links = immune_info_td.find_all('a')
                    titles = [link.get('title', 'N/A') for link in links] if links else []
                    return titles if titles else [immune_info_text]
    
    return None

def coin_splitter(text):
    coin_mapping = {
        'PC': 'Platinum Coin',
        'GC': 'Gold Coin',
        'SC': 'Silver Coin',
        'CC': 'Copper Coin'
    }

    # Define the coin hierarchy (higher to lower)
    hierarchy = {
        'PC': -1,  # Platinum Coin is the highest
        'GC': -2,  # Gold Coin
        'SC': -3,  # Silver Coin
        'CC': -4   # Copper Coin is the lowest
    }
    
    split_text = text.split(' ')
    previous = ''
    current = ''
    idx_list = []
    idx_cummulate = []
    for i in range(len(split_text)):
        current = split_text[i]
        
        if(previous in hierarchy and current in hierarchy):
            if(hierarchy[previous] <= hierarchy[current]):
                idx_list.append(i-1)

        if(current in hierarchy):
            previous = current

    for i in range(len(idx_list)):
        idx = idx_list[i]+i
        split_text.insert(idx, ',')

    # Map abbreviations to full names using coin_mapping
    mapped_text = []
    for token in split_text:
        if token in coin_mapping:
            mapped_text.append(coin_mapping[token])  # Replace abbreviation with full name
        else:
            mapped_text.append(token)  # Keep the original token (quantities, commas)

    return ' '.join(mapped_text)

def format_boss_info(boss_dict):
    info = []

    # General information
    info.append(f"{boss_dict['Title']} is a {', '.join(boss_dict.get('Type', ['unknown type']))}.")
    info.append(f"It is usually encountered or summoned in {', '.join(boss_dict.get('Environment', ['unknown environments']))} and operates with an AI type described as {boss_dict.get('AI Type', 'unknown')}.")

    # Damage information
    damage_info = boss_dict.get('Damage', {})
    if damage_info == "(Varies per attack)":
        info.append("The damage it deals varies per attack, making it unpredictable.")
    elif damage_info:
        damage_descriptions = []
        for attack, damages in damage_info.items():
            attack_name = attack if attack else "a general attack"
            mode_descriptions = [f"{mode}: {value}" for mode, value in damages]
            damage_descriptions.append(f"{attack_name} ({', '.join(mode_descriptions)})")
        info.append(f"In terms of damage, it can deliver the following: {', '.join(damage_descriptions)}.")

    # Max Life
    max_life = boss_dict.get('Max Life', {})
    if max_life:
        life_descriptions = [f"{mode}: {life}" for mode, life in max_life.items()]
        info.append(f"Its maximum life values are: {', '.join(life_descriptions)}.")

    # Defense information
    defense_info = boss_dict.get('Defense', {})
    if defense_info:
        base_defense = defense_info.get('Base', 'unknown')
        additional_defense = defense_info.get('Increased Defense', 'unknown')
        if isinstance(base_defense, dict):
            defense_descriptions = [f"{mode}: {value}" for mode, value in base_defense.items()]
            info.append(f"Defensive capabilities vary with modes: {', '.join(defense_descriptions)}.")
        else:
            info.append(f"Its base defense is {base_defense}, with an increased defense described as {additional_defense}.")

    # Immunities
    immunities = boss_dict.get('Immune to', [])
    if immunities:
        info.append(f"It has immunity to: {', '.join(immunities)}.")

    # Coins
    coins = boss_dict.get('Coins', {})
    if coins:
        coin_descriptions = [f"{mode}: {value}" for mode, value in coins.items()]
        info.append(f"When defeated, it provides the following coin rewards: {', '.join(coin_descriptions)}.")

    # Sounds
    sound_keys = boss_dict.get('Sound', {})
    if sound_keys:
        sound_descriptions = [f"{key} sound: {sound}" for key, sound in sound_keys.items()]
        info.append(f"Sounds associated with it include: {', '.join(sound_descriptions)}.")

    # Knockback resistance
    kbr = boss_dict.get('Knockback resist', {})
    if kbr:
        kbr_descriptions = [f"{mode}: {value}" for mode, value in kbr.items()]
        info.append(f"It exhibits knockback resistance with the following values: {', '.join(kbr_descriptions)}.")

    return " ".join(info)


def remove_square_brackets(text):
    # Use regex to replace [number] patterns with an empty string
    cleaned_text = re.sub(r'\[\d+\]', '', text)
    return cleaned_text
