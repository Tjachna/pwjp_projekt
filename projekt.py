import os
import sys
import re
import textract
from typing import List
import requests
from nltk.tokenize import sent_tokenize
import nltk
from typing import List, Tuple
from colorama import init, Fore

import concurrent.futures

nltk.download('punkt')

def read_file(file_path: str) -> str:
    _, file_extension = os.path.splitext(file_path)
    if file_extension == '.txt':
        with open(file_path, encoding='utf-8-sig') as file:
            return file.read()
    elif file_extension in ['.docx', '.pdf']:
        return textract.process(file_path).decode('utf-8')
    else:
        raise ValueError("Unsupported file format")

def split_into_chunks(text: str, chunk_size: int = 10) -> List[str]:
    words = text.split()
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks

def split_into_sentences(text: str) -> List[str]:
    sentences = sent_tokenize(text)
    result = []
    for sentence in sentences:
        parts = re.split(r'"', sentence)
        for i, part in enumerate(parts):
            if i % 2 == 0:
                result.append(part.strip())
            else:
                result.append(f'"{part}"')
    return result

def bing_search_single_fragment(fragment: str) -> Tuple[str, int]:
    headers = {"Ocp-Apim-Subscription-Key": "5c4a9fc00ad742b898a72848b7857fdb"}
    params = {
        "q": '"' + fragment + '"',
        "count": 10,
    }
    response = requests.get("https://api.bing.microsoft.com/v7.0/search", headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()
    if 'webPages' not in search_results:
        return fragment, 0
    return fragment, len(search_results['webPages']['value'])

def bing_search_fragments(fragments: List[str]) -> List[str]:
    plagiarised_fragments = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_fragment = {executor.submit(bing_search_single_fragment, fragment): fragment for fragment in fragments}
        for future in concurrent.futures.as_completed(future_to_fragment):
            try:
                result = future.result()
                if result[1] > 0:
                    plagiarised_fragments.append(result[0])
            except Exception as e:
                print
    return plagiarised_fragments

def calculate_plagiarism(wholeList: List[str], results: List[str]) -> Tuple[float, float]:
    plagiarized_fragments_count = len(results)
    plagiarism_percentage = (plagiarized_fragments_count / len(wholeList)) * 100

    plagiarized_characters_count = sum([len(fragment) for fragment in results])
    total_characters_count = sum([len(fragment) for fragment in wholeList])
    plagiarized_characters_percentage = (plagiarized_characters_count / total_characters_count) * 100

    return plagiarism_percentage, plagiarized_characters_percentage

def display_results(plagiarism_result: float, fragments: List[str], plagiarised_framents: List[str]):
    print(f"Procent splagiatowania (fragment): {plagiarism_result[0]:.2f}%")
    print(f"Procent splagiatowania (znaki): {plagiarism_result[1]:.2f}%")

def display_colored_text(fragments: List[str], plagiarised_framents: List[str]):
    for fragment in fragments:
        if fragment in plagiarised_framents:
            print(Fore.RED + fragment, end=' ')
        else:
            print(Fore.RESET + fragment, end=' ')
    print()

def main(file_path: str):
    text = read_file(file_path)
    fragments = split_into_sentences(text)
    plagiarised_framents = bing_search_fragments(fragments)
    plagiarism_result = calculate_plagiarism(fragments, plagiarised_framents)
    display_results(plagiarism_result, fragments, plagiarised_framents)
    display_colored_text(fragments, plagiarised_framents)

if len(sys.argv) < 2:
    sys.exit(1)
main(sys.argv[1])