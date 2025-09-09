import random
import tkinter as tk
import json


character = {
    "name": "Gingus",
    "race": "Human",
    "class": "Barbarian",
    "level": 1,
    "proficiency": 2,
    "stats": {
        "STR": 20, 
        "DEX": 20,
        "CON": 20,
        "INT": 6,
        "WIS": 6,
        "CHA": 6
    },
    "weapons": {
        "Longsword": {
        "hit_mod": 2,
        "damage_die": 6,
        "damage_die_count": 1,
        "damage_mod": 2,
    },
    "Shortbow": {
        "hit_mod": 2,
        "damage_die": 6,
        "damage_die_count": 1,
        "damage_mod": 2,
    }
    },
    "inventory": [],
    "gold": 10,
    "notes": "",
    "hp": {
        "current": 12,
        "max": 12
    }, 
    "ac": 14
}

def save_character(character, filename="character.json"):
    with open(filename, "w") as f:
        json.dump(character, f, indent=4)
        

def load_character(filename="character.json"):
    with open(filename, "r") as f:
        return json.load(f)



def roll_to_hit(weapon):
    return roll_with_mod(20, 1, weapon['hit_mod'])

def roll_damage(weapon):
    return roll(weapon["damage_die"], weapon["damage_die_count"]) + weapon["damage_mod"]


def mod_formula(stat):
    value = ((character["stats"][stat] - 10) // 2)
    return value

mods = {
    "STR": mod_formula('STR'),
    "DEX": mod_formula("DEX"),
    "CON": mod_formula("CON"),
    "INT": mod_formula("INT"),
    "WIS": mod_formula("WIS"),
    "CHA": mod_formula("CHA"),
}

def roll(d_number, d_count=1):
    value = 0
    for i in range(d_count):
        value += random.randint(1, d_number)
    return value

def roll_with_mod(d_number, d_count, ability):
    return (roll(d_number, d_count) + mods[ability])

def ability_check(ability):
    return roll_with_mod(20, 1, ability)




def gui_app():
    
    global character
    try:
        character = load_character("character.json")
    except FileNotFoundError:
        pass  # stick with defaults if no file
    
    root = tk.Tk()
    root.title("D&D Helper")
    root.geometry("600x400")
    # --- Functions must come BEFORE widgets ---
    def update_combat_stats():
        try:
            character["hp"]["current"] = int(hp_current_entry.get())
            character["hp"]["max"] = int(hp_max_entry.get())
            character["ac"] = int(ac_entry.get())
        except ValueError:
            pass  # ignore invalid entries

    def save_to_file():
        update_combat_stats()
        character["name"] = name_entry.get()
        save_character(character)

    def load_from_file():
        global character
        try:
            character = load_character()
            # Refresh GUI entries
            name_entry.delete(0, tk.END)
            name_entry.insert(0, character["name"])

            hp_current_entry.delete(0, tk.END)
            hp_current_entry.insert(0, character["hp"]["current"])
            hp_max_entry.delete(0, tk.END)
            hp_max_entry.insert(0, character["hp"]["max"])

            ac_entry.delete(0, tk.END)
            ac_entry.insert(0, character["ac"])
        except FileNotFoundError:
            print("No saved character file found!")

    # --- Character Info ---
    tk.Label(root, text="Character Name:").grid(row=0, column=0, sticky="e")
    name_entry = tk.Entry(root, width=20)
    name_entry.insert(0, character["name"])
    name_entry.grid(row=0, column=1, columnspan=2, sticky="w")

    tk.Label(root, text=f'Level {character["level"]} {character["race"]} {character["class"]}')\
        .grid(row=0, column=3, columnspan=3)

    # --- Ability Checks ---
    result_labels = {}
    for col, ability in enumerate(character["stats"].keys()):
        btn = tk.Button(
            root,
            text=f"{ability} ({mods[ability]})",
            command=lambda a=ability: result_labels[a].config(text=ability_check(a))
        )
        btn.grid(row=1, column=col, padx=10, pady=5)

        lbl = tk.Label(root, text="")
        lbl.grid(row=2, column=col)
        result_labels[ability] = lbl

    # --- Custom Roller ---
    tk.Label(root, text="Roll Anything").grid(row=3, column=1, columnspan=2, pady=10)

    dice_count_entry = tk.Entry(root, width=5)
    dice_count_entry.insert(0, "1")
    dice_count_entry.grid(row=4, column=0)

    tk.Label(root, text="d").grid(row=4, column=1)
    dice_sides_entry = tk.Entry(root, width=5)
    dice_sides_entry.insert(0, "20")
    dice_sides_entry.grid(row=4, column=2)

    result_label = tk.Label(root, text="")
    result_label.grid(row=5, column=1, columnspan=2, pady=5)

    def roll_custom():
        try:
            count = int(dice_count_entry.get())
            sides = int(dice_sides_entry.get())
            result = roll(sides, count)
            result_label.config(text=f"Rolled {count}d{sides}: {result}")
        except ValueError:
            result_label.config(text="Please enter valid numbers!")

    roll_button = tk.Button(root, text="Roll!", command=roll_custom)
    roll_button.grid(row=4, column=3, padx=10)

    # --- Weapons Section ---
    tk.Label(root, text="Weapons").grid(row=6, column=0, columnspan=6, pady=10)

    for row, (weapon_name, weapon) in enumerate(character["weapons"].items(), start=7):
        tk.Label(root, text=weapon_name).grid(row=row, column=0, padx=10, sticky="w")

        hit_result = tk.Label(root, text="")
        hit_result.grid(row=row, column=2, padx=5)
        tk.Button(
            root, text="Roll to Hit",
            command=lambda w=weapon, lbl=hit_result: lbl.config(
                text=f"Hit: {roll(20) + w['hit_mod']}"
            )
        ).grid(row=row, column=1, padx=5)

        dmg_result = tk.Label(root, text="")
        dmg_result.grid(row=row, column=4, padx=5)
        tk.Button(
            root, text="Roll Damage",
            command=lambda w=weapon, lbl=dmg_result: lbl.config(
                text=f"Damage: {roll(w['damage_die'], w['damage_die_count']) + w['damage_mod']}"
            )
        ).grid(row=row, column=3, padx=5)

    # --- Combat Stats Section ---
    tk.Label(root, text="Combat Stats").grid(row=20, column=0, columnspan=6, pady=10)

    tk.Label(root, text="HP:").grid(row=21, column=0, sticky="e")
    hp_current_entry = tk.Entry(root, width=5)
    hp_current_entry.insert(0, character["hp"]["current"])
    hp_current_entry.grid(row=21, column=1)
    tk.Label(root, text="/").grid(row=21, column=2)
    hp_max_entry = tk.Entry(root, width=5)
    hp_max_entry.insert(0, character["hp"]["max"])
    hp_max_entry.grid(row=21, column=3)

    tk.Label(root, text="AC:").grid(row=22, column=0, sticky="e")
    ac_entry = tk.Entry(root, width=5)
    ac_entry.insert(0, character["ac"])
    ac_entry.grid(row=22, column=1)

    tk.Label(root, text="Initiative:").grid(row=23, column=0, sticky="e")
    initiative_label = tk.Label(root, text=f"{mods['DEX']:+}")
    initiative_label.grid(row=23, column=1)

    # --- Save / Load Buttons ---
    tk.Button(root, text="Save Character", command=save_to_file).grid(row=25, column=0, padx=5, pady=10)
    tk.Button(root, text="Load Character", command=load_from_file).grid(row=25, column=1, padx=5, pady=10)

    root.mainloop()
    
if __name__ == "__main__":
    gui_app()