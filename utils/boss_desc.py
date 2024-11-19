from bs4 import BeautifulSoup
import requests

def extract_intro(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Extract flavor text
    flavor_text_element = soup.find('div', class_='flavor-text')
    flavor_text = flavor_text_element.get_text(strip=True, separator=' ') if flavor_text_element else ''

    # Extract hat note
    hat_note_element = soup.find('div', class_='hat-note')
    hat_note = hat_note_element.get_text(strip=True, separator=' ') if hat_note_element else ''


    # Extract all elements until the next <div> tag
    paragraphs = []
    for element in soup.find_all(['p', 'div']):
        if element.name == 'div' and element.get('id') == 'toc': # Stop when reaching the TOC 
            break

        if element.name == 'p':
            text = element.get_text(strip=True, separator=' ')
            if text not in paragraphs:
                paragraphs.append(text)
            else:
                print('Found repetition:', text)
        
        elif element.get('class') and 'c' in element.get('class'):
            text = element.get_text(strip=True, separator=' ')
            if text not in paragraphs:
                paragraphs.append(text)
            else:
                print('Found repetition:', text)

    if(flavor_text!=''):
        flavor_text+= '. '
    if(hat_note!=''):
        hat_note+= '. '    

    result = f"{flavor_text}{hat_note}{' '.join(paragraphs)}"
    return result


def fetch_info(url):

    # Make a GET request to fetch the HTML content
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract the relevant information
        content = soup.find('div', class_='mw-parser-output')

        # Convert the content to text format
        info = content.get_text(separator=' ')

        return info

import json
import re

def text_to_json(file_path):
    # Read the text file
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()

    # Initialize the dictionary to store the structure
    toc_dict = {}
    
    # Split text into lines
    lines = text.strip().splitlines()

    current_section = None
    current_subsection = None
    content_buffer = []
    
    # Regular expression for detecting section headers and subsections
    section_pattern = re.compile(r'^\d+\s+([A-Za-z\s]+)$')
    subsection_pattern = re.compile(r'^\d+\.\d+\s+([A-Za-z\s]+)$')

    # Iterate over the lines
    for line in lines:
        section_match = section_pattern.match(line)
        subsection_match = subsection_pattern.match(line)

        # If the line matches a section header
        if section_match:
            # If there is content in the buffer, store it in the current section/subsection
            if current_section:
                if current_subsection:
                    toc_dict[current_section][current_subsection] = '\n'.join(content_buffer).strip()
                    current_subsection = None  # Reset subsection
                else:
                    toc_dict[current_section] = '\n'.join(content_buffer).strip()
            
            # Start a new section
            current_section = section_match.group(1).strip()
            toc_dict[current_section] = {}
            content_buffer = []
        
        # If the line matches a subsection header
        elif subsection_match:
            # If there is content in the buffer, store it in the current subsection
            if current_subsection:
                toc_dict[current_section][current_subsection] = '\n'.join(content_buffer).strip()
            
            # Start a new subsection
            current_subsection = subsection_match.group(1).strip()
            toc_dict[current_section][current_subsection] = ""
            content_buffer = []
        
        else:
            # Add non-header lines to the content buffer
            content_buffer.append(line)
    
    # Save any remaining content in the buffer
    if current_section:
        if current_subsection:
            toc_dict[current_section][current_subsection] = '\n'.join(content_buffer).strip()
        else:
            toc_dict[current_section] = '\n'.join(content_buffer).strip()

    return toc_dict
