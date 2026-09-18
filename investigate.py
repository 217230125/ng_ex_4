import json
import ollama
from parse_data import load_items, get_unclaimed_items, save_result


def build_prompt(description, available_items):
    """Build system prompt and user prompt following README rules"""
    items_json_string = json.dumps(available_items, ensure_ascii=False)

    system_prompt = """You are campus lost‑and‑found matching assistant.
Rules:
1. ONLY use the provided item list data.
2. Not every detail has to match for a candidate match.
3. You MUST return ONLY pure JSON, NO extra text, NO markdown formatting.
4. Output JSON must strictly follow this structure:
{
    "matches": ["ITEM_ID"],
    "confidence": "LOW"
}
5. matches is a list of item id strings. Use empty list [] if there are no matches.
6. confidence value must be exactly one of: LOW, MEDIUM, HIGH.
7. Only consider items which are unclaimed, ignore claimed items completely.
"""

    user_prompt = f"""Lost item user description: {description}
Available unclaimed lost‑and‑found items:
{items_json_string}

Find all possible matching item IDs and assign confidence level. Output only JSON.
"""
    return system_prompt, user_prompt


def ask_qwen(system_prompt, user_prompt):
    """Call local Qwen model via ollama and return model response content"""
    response = ollama.chat(
        model="qwen",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response["message"]["content"]


def parse_response(response_text):
    """Clean model output and parse JSON string to python dictionary"""
    if not response_text or len(response_text.strip()) == 0:
        raise ValueError("Ollama returned empty response")

    cleaned_text = response_text.strip()
    # remove markdown code block markers
    if cleaned_text.startswith("```json"):
        cleaned_text = cleaned_text[7:].strip()
    if cleaned_text.startswith("```"):
        cleaned_text = cleaned_text[3:].strip()
    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-3].strip()

    cleaned_text = cleaned_text.strip()

    # Extract only the first {} json object, ignore extra text before/after
    start_idx = cleaned_text.find("{")
    end_idx = cleaned_text.rfind("}")
    if start_idx == -1 or end_idx == -1:
        raise ValueError("No valid JSON object found in model response")

    json_only = cleaned_text[start_idx : end_idx + 1]
    return json.loads(json_only)


def validate_result(result, available_items):
    """Validate result structure, key types and check for valid item IDs"""
    if not isinstance(result, dict):
        raise ValueError("Result must be a dictionary")

    required_keys = {"matches", "confidence"}
    if not required_keys.issubset(result.keys()):
        raise ValueError("Missing required keys: matches, confidence")

    matches_list = result["matches"]
    confidence_level = result["confidence"]

    if not isinstance(matches_list, list):
        raise ValueError("matches must be a list")
    if not isinstance(confidence_level, str):
        raise ValueError("confidence must be a string")

    if confidence_level not in ["LOW", "MEDIUM", "HIGH"]:
        raise ValueError("confidence must be LOW, MEDIUM or HIGH")

    valid_item_ids = {item["id"] for item in available_items}
    for match_id in matches_list:
        if match_id not in valid_item_ids:
            raise ValueError(f"Invalid item id: {match_id}")

    return True


def display_matches(result, available_items):
    """Print match result in user‑friendly formatted output as required"""
    print("CAMPUS LOST‑AND‑FOUND ASSISTANT")
    print("=" * 50)
    print(f"Describe the item you lost: {result.get('user_description', '')}")
    print("Searching for possible matches...")
    print("MATCH RESULT")
    print("-" * 50)
    print(f"Confidence: {result['confidence']}")
    print("Possible matches:")

    match_ids = result["matches"]
    if len(match_ids) == 0:
        print("No matches found. matches = []")
        return

    item_lookup_map = {item["id"]: item for item in available_items}
    for item_id in match_ids:
        item = item_lookup_map[item_id]
        print(f"ID: {item['id']}")
        print(f"Item: {item['item']}")
        print(f"Color: {item['color']}")
        print(f"Location: {item['location']}")
        print(f"Date found: {item['date']}")
    print("Result saved to output/match_result.json")


def main():
    raw_item_data = load_items("found_items.json")
    unclaimed_item_list = get_unclaimed_items(raw_item_data)

    user_input_description = input("Please describe your lost item: ")

    sys_prompt, usr_prompt = build_prompt(user_input_description, unclaimed_item_list)
    model_raw_response = ask_qwen(sys_prompt, usr_prompt)
    parsed_result = parse_response(model_raw_response)

    validate_result(parsed_result, unclaimed_item_list)

    output_payload = {
        "user_description": user_input_description,
        **parsed_result
    }

    save_result(output_payload, "output/match_result.json")
    display_matches(output_payload, unclaimed_item_list)


if __name__ == "__main__":
    main()
