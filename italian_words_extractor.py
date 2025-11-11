import requests
from bs4 import BeautifulSoup
import re
import json
import csv

def extract_italian_words(url):
    """
    Extract 1000 most common Italian words from the given URL
    Returns a list of dictionaries containing word, part of speech, and definition
    """
    
    # Fetch the webpage
    response = requests.get(url)
    response.raise_for_status()
    
    # Parse the HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the main list containing all vocabulary items
    main_list = soup.find('ol', {'id': 'main-list'})
    
    if not main_list:
        # Fallback: find any ordered list with li elements containing vocab
        main_list = soup.find('ol')
        if not main_list:
            raise ValueError("Could not find the vocabulary list on the page")
    
    words_data = []
    
    # Extract each vocabulary item
    vocab_items = main_list.find_all('li')
    
    for item in vocab_items:
        # Find the vocab, pos, and definition elements
        vocab_div = item.find('div', class_='vocab')
        pos_div = item.find('div', class_='pos')
        definition_div = item.find('div', class_='definition')
        
        if vocab_div and pos_div and definition_div:
            # Extract text and clean it
            word = vocab_div.get_text().strip()
            pos = pos_div.get_text().strip()
            definition = definition_div.get_text().strip()
            
            # Clean up the part of speech (remove brackets)
            pos = re.sub(r'^\[|\]$', '', pos)
            
            # Clean up the definition (remove parentheses)
            definition = re.sub(r'^\(|\)$', '', definition)
            
            # Skip empty entries
            if word and pos and definition:
                words_data.append({
                    'word': word,
                    'pos': pos,
                    'definition': definition
                })
    
    return words_data

def save_to_csv(words_data, filename="italian_1112_words.csv"):
    """Save the extracted words to a CSV file"""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['word', 'pos', 'definition']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for word_data in words_data:
            writer.writerow(word_data)
    
    print(f"Saved {len(words_data)} words to {filename}")

def save_to_json(words_data, filename="italian_1112_words.json"):
    """Save the extracted words to a JSON file"""
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(words_data, jsonfile, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(words_data)} words to {filename}")

def save_to_txt(words_data, filename="italian_1112_words.txt"):
    """Save the extracted words to a TXT file"""
    with open(filename, 'w', encoding='utf-8') as txtfile:
        txtfile.write("1000 Most Common Italian Words\n")
        txtfile.write("=" * 50 + "\n\n")
        
        for i, word_data in enumerate(words_data, 1):
            txtfile.write(f"{i:3d}. {word_data['word']:<20} [{word_data['pos']}] - {word_data['definition']}\n")
    
    print(f"Saved {len(words_data)} words to {filename}")

def save_words_only_txt(words_data, filename="italian_words_only.txt"):
    """Save only the Italian words to a simple TXT file, one word per line"""
    with open(filename, 'w', encoding='utf-8') as txtfile:
        for word_data in words_data:
            txtfile.write(f"{word_data['word']}\n")
    
    print(f"Saved {len(words_data)} words (words only) to {filename}")

def print_sample_words(words_data, num_samples=10):
    """Print a sample of the extracted words"""
    print(f"\nSample of {num_samples} words:")
    print("-" * 50)
    for i, word in enumerate(words_data[:num_samples]):
        print(f"{i+1:2d}. {word['word']:<15} [{word['pos']}] - {word['definition']}")

if __name__ == "__main__":
    # URL to scrape
    url = "https://travelwithlanguages.com/blog/most-common-italian-words.html"
    
    try:
        # Extract the words
        print("Extracting Italian words from the website...")
        words = extract_italian_words(url)
        
        print(f"Successfully extracted {len(words)} Italian words!")
        
        # Print sample
        print_sample_words(words)
        
        # Save to files
        save_to_csv(words)
        save_to_json(words)
        save_to_txt(words)
        save_words_only_txt(words)  
        
        # Print some statistics
        pos_counts = {}
        for word in words:
            pos = word['pos']
            pos_counts[pos] = pos_counts.get(pos, 0) + 1
        
        print(f"\nPart of speech distribution:")
        for pos, count in sorted(pos_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {pos}: {count} words")
            
    except Exception as e:
        print(f"Error occurred: {e}")
        print("Please check your internet connection and try again.")