import openai
from openai import OpenAI
import os
from mitreattack.stix20 import MitreAttackData

openai.api_key = os.getenv("OPENAI_API_KEY")    

# Load the MITRE ATT&CK dataset using MitreAttackData
mitre_attack_data = MitreAttackData("enterprise-attack.json")

def extract_keywords_from_description(description):
    # Define the merged prompt
    prompt = (f"Given the cybersecurity scenario description: '{description}', identify and list the key terms, "
              "techniques, or technologies relevant to MITRE ATT&CK. Extract TTPs from the scenario. "
              "If the description is too basic, expand upon it with additional details, applicable campaign, "
              "or attack types based on dataset knowledge. Then, extract the TTPs from the revised description.")
    
    # Set up the messages for the OpenAI API
    messages = [
        {
            "role": "system",
            "content": "You are a cybersecurity professional with more than 25 years of experience."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    # Make the API call
    try:
        client = OpenAI() 
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=2048,
            n=1,
            stop=None,
            temperature=0.7
        )
        response_content = response.choices[0].message.content.strip()
        
        # Split the response content into individual keywords
        # This step can be refined based on the actual model responses
        keywords = response_content.split(', ')
        return keywords

    except Exception as e:
        print("An error occurred while connecting to the OpenAI API:", e)
        return []

def score_matches(matches, keywords):
    scores = []
    for match in matches:
        score = sum([keyword in match['name'] for keyword in keywords]) + \
                sum([keyword in match['description'] for keyword in keywords])
        scores.append((match, score))
    return scores

def search_dataset_for_matches(keywords):
    matches = []
    for item in mitre_attack_data.get_techniques():
        if any(keyword in item['name'] for keyword in keywords):
            matches.append(item)
        elif 'description' in item and any(keyword in item['description'] for keyword in keywords):
            matches.append(item)
    return matches

def generate_ttp_chain(match):
    # Create a prompt for GPT-3 to generate a TTP chain for the provided match
    prompt = (f"Given the MITRE ATT&CK technique '{match['name']}' and its description '{match['description']}', "
              "generate an example scenario and TTP chain demonstrating its use.")
    
    # Set up the messages for the OpenAI API
    messages = [
        {
            "role": "system",
            "content": "You are a cybersecurity professional with expertise in MITRE ATT&CK techniques."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    # Make the API call
    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=2048,
            n=1,
            stop=None,
            temperature=0.7
        )
        response_content = response.choices[0].message.content.strip()
        return response_content

    except Exception as e:
        print("An error occurred while generating the TTP chain:", e)
        return "Unable to generate TTP chain."

description = input("Enter your scenario description: ")
keywords = extract_keywords_from_description(description)
matches = search_dataset_for_matches(keywords)
scored_matches = score_matches(matches, keywords)

# Sort by score in descending order and take the top 3
top_matches = sorted(scored_matches, key=lambda x: x[1], reverse=True)[:3]

print("Top 3 matches from the MITRE ATT&CK dataset:")
for match, score in top_matches:
    print("Name:", match['name'])
    print("Summary:", match['description'])
    ttp_chain = generate_ttp_chain(match)
    print("Example Scenario and TTP Chain:", ttp_chain)
    print("-" * 50)
