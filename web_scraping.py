import requests
from bs4 import BeautifulSoup
import json
from utils.boss_stats_utils import *
from utils.boss_desc import *
from fpdf import FPDF
import os

def fetch_wiki_page(url):
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"Error fetching page: {response.status_code}")
    
    return response.text

def extract_boss_name(url):
    # Use regex to find the last part of the URL after the last '/'
    match = re.search(r'\/([^\/]+)$', url)
    if match:
        # Replace underscores with spaces and return the formatted boss name
        return match.group(1)
    return None


def web_scraping(url_lst):
    for url in url_lst:    
        boss_name = extract_boss_name(url)
        html_content = fetch_wiki_page(url)

        # Loot
        general_drop = extract_loot_items(html_content, '')
        normal_drop = extract_loot_items(html_content, 'm-normal')
        em_shareDrop = extract_loot_items(html_content, 'm-expert-master')
        master_drop = extract_loot_items(html_content, 'm-master')

        # Forms & Stats window
        forms = extract_forms(html_content)
        stat_of_forms = []
        stat_data = {}
        normal_loot = combine_loot([general_drop, normal_drop])
        expert_loot = combine_loot([general_drop, em_shareDrop])
        master_loot = combine_loot([general_drop, em_shareDrop, master_drop])
        for form in forms.keys():
            statContent = forms[form]
            stat_data = get_stat(statContent, form)
            # Check if stat_data is a dictionary
            if isinstance(stat_data, dict):
                stat_data['Sound'] = extract_audio(stat_data)
                stat_of_forms.append(remove_square_brackets(format_boss_info(stat_data)))
            else:
                print(f"Warning: stat_data for {form} is not a dictionary: {stat_data}")
        result_string = '\n\n\n'.join(stat_of_forms)

        # Joining session
        intro = extract_intro(html_content)
        text = fetch_info(url)
        lines = text.splitlines()
        for i in range(len(lines)):
            lines[i] = lines[i].strip()

        # Find sessions
        section_pattern = re.compile(r'^\d+\s+([A-Za-z\s]+)$')
        subsection_pattern = re.compile(r'^\d+\.\d+\s+([A-Za-z\s]+)$')
        Content_check = False
        sessions = []
        for line in lines:
            section_match = section_pattern.match(line)
            subsection_match = subsection_pattern.match(line)
            
            # If a section match is found, break the loop
            if(line == 'Contents'):
                Content_check = True
                # print("The table of contents is incoming")

            if section_match is not None:
                # print("Section header found, breaking loop.")
                sessions.append(line)
            if subsection_match is not None:
                # print("Section header found, breaking loop.")
                sessions.append(line)  

        for i in range(len(sessions)):
            sessions[i] = sessions[i].split(' ')[-1]
        sessions

        session_dict = {}
        key = 'Introduction'
        session_dict[key] = ''
        session_dict['Statistics'] = result_string
        for i in range(len(lines)):
            if lines[i] in sessions:
                key = lines[i]
                if key not in session_dict:
                    session_dict[key] = ''
            else:
                session_dict[key] = (session_dict[key] + ' ' + lines[i]).strip()
        session_dict['Introduction'] = intro
        del session_dict['References']
        
        # Loot information
        loot_lst = []
        loot = {'Normal Drop': normal_loot, 'Expert Drop': expert_loot, 'Master Drop': master_loot}
        if loot:
            for mode, items in loot.items():
                loot_lst.append(f"{mode}: {'; '.join(items) if items else 'No items'}\n")
        else:
            loot_lst.append("Loot: N/A")

        session_dict['Loot'] = '\n'.join(loot_lst)
        del session_dict['Arms']

        # Convert the dictionary to a string format
        dict_string = '\n'.join([f"{key}: {value}" for key, value in session_dict.items()])

        for key, value in session_dict.items():
            # Convert the session's data into a string
            dict_string = f"{key}: {value}"

            # Define inputs
            output_folder = f"data/{boss_name}"

            # Ensure the output folder exists
            os.makedirs(output_folder, exist_ok=True)

            # Define the PDF file path
            pdf_file_path = os.path.join(output_folder, f"{key}.pdf")

            # Function to replace unsupported characters for PDF generation
            def replace_unsupported_characters(text):
                # List of supported characters for the Helvetica font
                supported_characters = re.compile(r'[\x00-\x7F\xA0-\xFF]+')
                return ''.join([char if supported_characters.match(char) else ' ' for char in text])

            # Clean the content
            cleaned_content = replace_unsupported_characters(dict_string)

            # Initialize the PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', size=12)

            # Write cleaned content to the PDF
            pdf.multi_cell(0, 10, cleaned_content)

            # Save the PDF
            pdf.output(pdf_file_path)
            print(f"PDF saved at {pdf_file_path}")
if __name__ == "__main__":
    url_lst = ['https://terraria.wiki.gg/wiki/Skeletron_Prime']
    web_scraping(url_lst)