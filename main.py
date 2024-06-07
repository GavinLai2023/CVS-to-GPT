#!/usr/bin/env python
# coding: utf-8


import openai
import os
import csv
import concurrent.futures
from docx import Document
import configparser

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Read values from the configuration file
openai.api_key = config.get('openai', 'api_key')
model_name = config.get('openai', 'model')




def get_ai_response(prompt, system_message) :
    print(f"Getting AI response...{prompt}")
    messages = [{"role": "system", "content": system_message}, {"role": "user", "content": prompt}]
    # result = openai.chat.completions.create(model=model, messages=messages, temperature=0.5, max_tokens=1500) 
    result = openai.chat.completions.create(model=model_name, messages=messages) 
    print("AI response received.")
    return result.choices[0].message.content



def process_input_csv_file(input_csv_file):
    print("Processing input CSV file...")
    with open(input_csv_file, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)
    print("Input CSV file processed.")
    return rows



def save_response_to_word(response, file_name, folder_name="articles"):
    # Ensure the folder exists
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Create a Word document
    doc = Document()
    doc.add_paragraph(response)

    #处理掉文件命中不允许的特殊字符和最右侧的空格
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        file_name = (file_name.replace(char, '')).rstrip()
        
    # Save the document
    file_path = os.path.join(folder_name, f"{file_name}.docx")
    doc.save(file_path)
    print(f"response saved to {file_path}")


def main(input_file_name,system_message_file):
    rows = process_input_csv_file(input_file_name) #read each row of the csv file

    print("Reading system message file...")
    with open(system_message_file, 'r') as file:
        system_message = file.read()
    print("System message file read.")

    prompts = [row[0] for row in rows if row]  # Extract the first column from each row (assumed to be the prompt) if the row is not empty

    print("Starting ThreadPoolExecutor...")
    # Create a ThreadPoolExecutor to handle tasks concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        data_for_executor = [(prompt, system_message) for prompt in prompts]
        # Submit tasks to the executor and keep track of them using a dictionary
        # This maps futures (tasks) to their corresponding data (prompt and system message)
        future_to_data = {executor.submit(get_ai_response, prompt, system_prompt): (prompt, system_prompt) for (prompt, system_prompt) in data_for_executor}
        for future in concurrent.futures.as_completed(future_to_data):
            (prompt, system_prompt) = future_to_data[future]
            try:
                print(f"Processing prompt: {prompt}")
                ai_response = future.result()
                save_response_to_word(ai_response, prompt)
                print(f"Prompt: {prompt} processed.")
            except Exception as exc:
                print(f'Generating output for {prompt} generated an exception: {exc}')
    print("ThreadPoolExecutor finished.")



main('input.csv','system_prompt.txt')


input("press Enter to exit...")




