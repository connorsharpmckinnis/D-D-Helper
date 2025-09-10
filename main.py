import random
import tkinter as tk
import json
import platform


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
    "ac": 14,
    "skills": {
        "Athletics": {"ability": "STR", "prof": 2},
        "Acrobatics": {"ability": "DEX", "prof": 2},
    }
}

def skill_modifier(skill_name):
    skill = character["skills"][skill_name]
    ability = skill["ability"]
    return mods[ability] + skill["prof"]

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
    root.geometry("800x600")
    root.configure(bg="#f7f7f7")  # light gray background for the app

    
    # -- Outer frame with scrolling and scrollbar -- #
    outer_frame = tk.Frame(root, bg="#f7f7f7")
    outer_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(outer_frame, bg="#f7f7f7", highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)
    
    scrollbar = tk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    
    canvas.configure(yscrollcommand=scrollbar.set)
    
    scrollable_frame = tk.Frame(canvas, bg="#f7f7f7")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    

    # --- Functions ---
    def update_combat_stats():
        try:
            character["hp"]["current"] = int(hp_current_entry.get())
            character["hp"]["max"] = int(hp_max_entry.get())
            character["ac"] = int(ac_entry.get())
        except ValueError:
            pass

    def save_to_file():
        update_combat_stats()
        update_notes()
        character["name"] = name_entry.get()
        save_character(character)

    def load_from_file():
        global character
        try:
            character = load_character()
            # Refresh GUI
            name_entry.delete(0, tk.END)
            name_entry.insert(0, character["name"])
            hp_current_entry.delete(0, tk.END)
            hp_current_entry.insert(0, character["hp"]["current"])
            hp_max_entry.delete(0, tk.END)
            hp_max_entry.insert(0, character["hp"]["max"])
            ac_entry.delete(0, tk.END)
            ac_entry.insert(0, character["ac"])
            notes_text.delete("1.0", tk.END)
            notes_text.insert("1.0", character["notes"])
            inventory_listbox.delete(0, tk.END)
            for item in character["inventory"]:
                inventory_listbox.insert(tk.END, item)
        except FileNotFoundError:
            print("No saved character file found!")

    def update_notes():
        character["notes"] = notes_text.get("1.0", tk.END).strip()
        
    def _on_mousewheel(event):
        """Scroll for Windows and Linux"""
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_mousewheel_mac(event):
        """Scroll for macOS"""
        canvas.yview_scroll(int(-1*event.delta), "units")

    # Detect platform
    if platform.system() == "Darwin":
        # macOS
        canvas.bind_all("<MouseWheel>", _on_mousewheel_mac)
    else:
        # Windows / Linux
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # --- Character Info ---
    info_frame = tk.Frame(scrollable_frame, padx=10, pady=5, bg="#e0e0e0", relief="groove", bd=2)
    info_frame.pack(fill="x")

    tk.Label(info_frame, text="Character Name:", bg="#e0e0e0", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="e")
    name_entry = tk.Entry(info_frame, width=20)
    name_entry.insert(0, character["name"])
    name_entry.grid(row=0, column=1, sticky="w")

    tk.Label(
        info_frame,
        text=f'Level {character["level"]} {character["race"]} {character["class"]}'
    ).grid(row=0, column=2, padx=10)

    # --- Ability Checks ---
    stats_frame = tk.LabelFrame(scrollable_frame, text="Ability Checks", padx=10, pady=5, bg="#f0f0ff", font=("Arial", 10, "bold"))
    stats_frame.pack(fill="x", pady=5)

    result_labels = {}
    for col, ability in enumerate(character["stats"].keys()):
        btn = tk.Button(
            stats_frame,
            text=f"{ability} ({mods[ability]})",
            command=lambda a=ability: result_labels[a].config(text=ability_check(a))
        )
        btn.grid(row=0, column=col, padx=5, pady=2)
        lbl = tk.Label(stats_frame, text="")
        lbl.grid(row=1, column=col)
        result_labels[ability] = lbl
        
    # --- Skills Section ---
    skills_frame = tk.LabelFrame(scrollable_frame, text="Skills", padx=10, pady=5, bg="#f0fff0", font=("Arial", 10, "bold"))
    skills_frame.pack(fill="x", padx=10, pady=5)

    skill_result_labels = {}

    for col, skill_name in enumerate(character["skills"].keys()):
        mod = skill_modifier(skill_name)

        btn = tk.Button(
            skills_frame,
            text=f"{skill_name} ({mod:+})",
            wraplength=50,
            justify="center",
            command=lambda s=skill_name: skill_result_labels[s].config(
                text=f"{roll(20) + skill_modifier(s)}"
            )
        )
        btn.grid(row=0, column=col, sticky="w", pady=2)

        lbl = tk.Label(skills_frame, text="")
        lbl.grid(row=1, column=col, sticky="w")
        skill_result_labels[skill_name] = lbl

    # --- Custom Roller ---
    roller_frame = tk.LabelFrame(scrollable_frame, text="Custom Roller", padx=10, pady=5, bg="#f0fff0", font=("Arial", 10, "bold"))
    roller_frame.pack(fill="x", pady=5)

    dice_count_entry = tk.Entry(roller_frame, width=5)
    dice_count_entry.insert(0, "1")
    dice_count_entry.grid(row=0, column=0)

    tk.Label(roller_frame, text="d").grid(row=0, column=1)
    dice_sides_entry = tk.Entry(roller_frame, width=5)
    dice_sides_entry.insert(0, "20")
    dice_sides_entry.grid(row=0, column=2)

    result_label = tk.Label(roller_frame, text="")
    result_label.grid(row=1, column=0, columnspan=3, pady=5)

    def roll_custom():
        try:
            count = int(dice_count_entry.get())
            sides = int(dice_sides_entry.get())
            result = roll(sides, count)
            result_label.config(text=f"Rolled {count}d{sides}: {result}")
        except ValueError:
            result_label.config(text="Please enter valid numbers!")

    roll_button = tk.Button(roller_frame, text="Roll!", command=roll_custom, bg="#ffc0c0", relief="raised", bd=2, padx=5, pady=5)
    roll_button.grid(row=0, column=3, padx=10)

    # --- Weapons ---
    weapons_frame = tk.LabelFrame(scrollable_frame, text="Weapons", padx=10, pady=5,  bg="#f7f0ff", font=("Arial", 10, "bold"))
    weapons_frame.pack(fill="x", pady=5)

    for row, (weapon_name, weapon) in enumerate(character["weapons"].items()):
        tk.Label(weapons_frame, text=weapon_name).grid(row=row, column=0, padx=5, sticky="w")

        hit_result = tk.Label(weapons_frame, text="", bg="#f7f0ff")
        hit_result.grid(row=row, column=2, padx=5)
        tk.Button(
            weapons_frame, text="Roll to Hit",
            command=lambda w=weapon, lbl=hit_result: lbl.config(
                text=f"Hit: {roll(20) + w['hit_mod']}",
            ),
            bg="#ffd0d0", relief="raised", bd=2, padx=5, pady=3
        ).grid(row=row, column=1, padx=5)

        dmg_result = tk.Label(weapons_frame, text="", bg="#f7f0ff")
        dmg_result.grid(row=row, column=4, padx=5)
        tk.Button(
            weapons_frame, text="Roll Damage",
            command=lambda w=weapon, lbl=dmg_result: lbl.config(
                text=f"Damage: {roll(w['damage_die'], w['damage_die_count']) + w['damage_mod']}",
            ),
            bg="#ffd0d0", relief="raised", bd=2, padx=5, pady=3
        ).grid(row=row, column=3, padx=5)

    # --- Combat Stats ---
    combat_frame = tk.LabelFrame(scrollable_frame, text="Combat Stats", padx=10, pady=5, bg="#f0fff7", font=("Arial", 10, "bold"))
    combat_frame.pack(fill="x", pady=5)

    tk.Label(combat_frame, text="HP:").grid(row=0, column=0, sticky="e")
    hp_current_entry = tk.Entry(combat_frame, width=5)
    hp_current_entry.insert(0, character["hp"]["current"])
    hp_current_entry.grid(row=0, column=1)
    tk.Label(combat_frame, text="/").grid(row=0, column=2)
    hp_max_entry = tk.Entry(combat_frame, width=5)
    hp_max_entry.insert(0, character["hp"]["max"])
    hp_max_entry.grid(row=0, column=3)

    tk.Label(combat_frame, text="AC:").grid(row=1, column=0, sticky="e")
    ac_entry = tk.Entry(combat_frame, width=5)
    ac_entry.insert(0, character["ac"])
    ac_entry.grid(row=1, column=1)

    def roll_initiative():
        roll_val = random.randint(1, 20)
        total = roll_val + mods["DEX"]
        initiative_result_label.config(text=total)

    tk.Label(combat_frame, text="Initiative:").grid(row=2, column=0, sticky="e")
    initiative_button = tk.Button(combat_frame, text=f"{mods['DEX']:+}", command=roll_initiative)
    initiative_button.grid(row=2, column=1)
    initiative_result_label = tk.Label(combat_frame, text="")
    initiative_result_label.grid(row=2, column=2, sticky="w")

    # --- Notes and Inventory (side by side) ---
    bottom_frame = tk.Frame(scrollable_frame, padx=10, pady=5, bg="#f7f7f7")
    bottom_frame.pack(fill="both", expand=True)

    notes_frame = tk.LabelFrame(bottom_frame, text="Notes", padx=10, pady=5)
    notes_frame.pack(side="left", fill="both", expand=True, padx=5)

    notes_text = tk.Text(notes_frame, height=10, wrap="word")
    notes_text.insert("1.0", character["notes"])
    notes_text.pack(fill="both", expand=True)

    inventory_frame = tk.LabelFrame(bottom_frame, text="Inventory", padx=10, pady=5)
    inventory_frame.pack(side="right", fill="both", expand=True, padx=5)

    inventory_listbox = tk.Listbox(inventory_frame, height=10)
    inventory_listbox.pack(fill="both", expand=True)
    for item in character["inventory"]:
        inventory_listbox.insert(tk.END, item)

    new_item_entry = tk.Entry(inventory_frame)
    new_item_entry.pack(fill="x", pady=2)

    def add_item():
        item = new_item_entry.get().strip()
        if item:
            character["inventory"].append(item)
            inventory_listbox.insert(tk.END, item)
            new_item_entry.delete(0, tk.END)

    def remove_item():
        selection = inventory_listbox.curselection()
        if selection:
            index = selection[0]
            inventory_listbox.delete(index)
            del character["inventory"][index]

    tk.Button(inventory_frame, text="Add", command=add_item, bg="#d0ffd0", relief="raised", bd=2, padx=5, pady=3).pack(side="left", padx=2, pady=2)
    tk.Button(inventory_frame, text="Remove Selected", command=remove_item, bg="#ffd0d0", relief="raised", bd=2, padx=5, pady=3).pack(side="right", padx=2, pady=2)

    # --- Save / Load Buttons ---
    control_frame = tk.Frame(scrollable_frame, pady=10, bg="#f7f7f7")
    control_frame.pack(fill="x")
    tk.Button(control_frame, text="Save Character", command=save_to_file, bg="#d0ffd0", relief="raised", bd=2, padx=10, pady=5).pack(side="left", padx=10)
    tk.Button(control_frame, text="Load Character", command=load_from_file, bg="#ffffc0", relief="raised", bd=2, padx=10, pady=5).pack(side="left", padx=10)

    root.mainloop()
    
if __name__ == "__main__":
    gui_app()