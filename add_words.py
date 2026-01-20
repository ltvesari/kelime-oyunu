import json
import os

def load_current_verbs(filename="verbs.json"):
    if not os.path.exists(filename):
        return [], 0
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        return [], 0
    max_id = max(item["id"] for item in data)
    return data, max_id

def add_new_verbs(new_verbs, filename="verbs.json"):
    current_data, max_id = load_current_verbs(filename)
    current_verbs_set = {item["verb"].lower() for item in current_data}
    
    added_count = 0
    skipped_count = 0
    
    for verb_data in new_verbs:
        if verb_data["verb"].lower() in current_verbs_set:
            print(f"Skipping duplicate: {verb_data['verb']}")
            skipped_count += 1
            continue
            
        max_id += 1
        verb_data["id"] = max_id
        # Set defaults if missing
        if "weight" not in verb_data:
            verb_data["weight"] = 100
        if "correct_count" not in verb_data:
            verb_data["correct_count"] = 0
            
        current_data.append(verb_data)
        current_verbs_set.add(verb_data["verb"].lower())
        added_count += 1
        
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(current_data, f, ensure_ascii=False, indent=2)
        
    print(f"Added {added_count} new verbs. Skipped {skipped_count} duplicates.")
    print(f"Total verbs: {len(current_data)}")

if __name__ == "__main__":
    # Example usage / Test
    # existing verbs won't be re-added
    pass
