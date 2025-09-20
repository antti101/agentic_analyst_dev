import json
import os
import time

import openai
from dotenv import load_dotenv

load_dotenv()

def rephrase_hint_with_gpt(hint: str) -> str:
    """Uses GPT-3.5-Turbo to rephrase a hint for a pharmacy context."""
    if not hint or not hint.strip():
        return ""  # Return empty if hint is empty

    try:
        prompt = (
            f"Rephrase the following data metric hint for a pharmacy analytics system. "
            f"Make it clear, concise, and relevant for a pharmacy manager or data analyst. "
            f"Focus on concepts like prescription data, patient adherence, drug inventory, and sales. "
            f"Do not include the original hint in your response. Just provide the rephrased text.\n\n"
            f"Original hint: '{hint}'\n\n"
            f"Rephrased hint for a pharmacy:"
        )
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert assistant that rephrases technical data hints for a pharmacy business context."}, 
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=60,
            n=1,
            stop=None,
        )
        rephrased = response.choices[0].message.content.strip()
        
        # Clean up the response in case the model adds extra quotes or text
        if rephrased.startswith('"') and rephrased.endswith('"'):
            rephrased = rephrased[1:-1]
        
        return rephrased
    except Exception as e:
        print(f"\nError rephrasing hint '{hint}': {e}")
        return hint  # Return original hint on error

def process_semantic_layer():
    """Reads the semantic layer file, rephrases all hints using an LLM,
    and overwrites the file with the updated content.
    """
    # Ensure the OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set. Please set it before running this script.")
        return
    openai.api_key = os.getenv("OPENAI_API_KEY")

    input_file = 'semantic_layer_simple.txt'
    output_file = 'semantic_layer_simple.txt'

    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        return

    updated_items = []
    total_items = len(lines)
    print(f"Starting to rephrase hints for {total_items} items. This may take some time and will incur API costs...")

    for i, line in enumerate(lines):
        if not line.strip():
            continue
        
        try:
            item = json.loads(line)
            original_hint = item.get("hint", "")
            
            if original_hint:
                # Display progress
                print(f"\rProcessing item {i+1}/{total_items} ('{item.get('name')}')...", end="")
                new_hint = rephrase_hint_with_gpt(original_hint)
                item["hint"] = new_hint
            
            updated_items.append(item)
            
            # Add a delay to avoid hitting API rate limits
            time.sleep(0.5)
        except json.JSONDecodeError:
            print(f"\nSkipping invalid JSON line: {line}")
            continue
        except Exception as e:
            print(f"\nAn unexpected error occurred on item {i+1}: {e}")
            # Add the original item back if something went wrong
            if 'item' in locals():
                updated_items.append(item)
            continue

    # Write the updated items back to the file
    try:
        with open(output_file, 'w') as f:
            for item in updated_items:
                f.write(json.dumps(item) + '\n')
        print(f"\nSuccessfully rephrased hints in {output_file}.")
    except IOError as e:
        print(f"\nError writing to file: {e}")

if __name__ == "__main__":
    process_semantic_layer()
