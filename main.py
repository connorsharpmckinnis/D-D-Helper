import random
import tkinter as tk
import json
import platform

from tkinter import ttk
from ttkthemes import ThemedTk




STYLE = {
    "bg_main": "#9d9d9d",
    "bg_frame": "#9d9d9d",
    "accent": "#AFAFAF",
    "accent2": "#2196F3",
    "text": "#363636",
    "font_title": ("Helvetica", 12, "bold"),
    "font_normal": ("Helvetica", 10),
}



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

    root = ThemedTk(theme="black")
    root.title("D&D Helper - Modern UI")
    root.geometry("800x600")

    # Use the ThemedTk's current theme colors for accent and background
    themed_style = ttk.Style(root)
    # Remove border for pill shape
    themed_style.layout("Accent.TButton", [
        ("Button.padding", {"children": [
            ("Button.label", {"side": "left", "expand": 1})
        ], "sticky": "nswe"})
    ])
    # Get themed background and foreground if available
    try:
        accent_bg = STYLE["accent"]
        accent_fg = STYLE["text"]
    except Exception:
        accent_bg = STYLE["accent"]
        accent_fg = STYLE["text"]
    themed_style.configure(
        "Accent.TButton",
        background=accent_bg,
        foreground=accent_fg,
        font=STYLE["font_normal"],
        padding=(12, 6),  # pill shape
        highlightthickness=0,
        relief="flat",
        borderwidth=0,
        focuscolor=accent_bg
    )
    
    # -- Outer frame with scrolling and scrollbar -- #
    # Use themed background for main backgrounds
    arc_bg = themed_style.lookup("TFrame", "background", default="#ECECEC")
    arc_fg = themed_style.lookup("TLabel", "foreground", default=STYLE["text"])
    # Outer frame and canvas
    outer_frame = tk.Frame(root, bg=arc_bg)
    outer_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(outer_frame, bg=arc_bg, highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)
    
    scrollbar = tk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    
    canvas.configure(yscrollcommand=scrollbar.set)
    
    scrollable_frame = tk.Frame(canvas, bg=arc_bg)

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
    info_frame = tk.Frame(scrollable_frame, padx=10, pady=10, bg=arc_bg, relief="flat")
    info_frame.pack(fill="x", padx=6, pady=4)

    tk.Label(info_frame, text="Character Name:", bg=arc_bg, fg=arc_fg, font=STYLE["font_normal"]).grid(row=0, column=0, sticky="e", padx=6, pady=4)
    name_entry = tk.Entry(info_frame, width=20, bg=arc_bg, fg=arc_fg, insertbackground=arc_fg, font=STYLE["font_normal"])
    name_entry.insert(0, character["name"])
    name_entry.grid(row=0, column=1, sticky="w", padx=6, pady=4)

    tk.Label(
        info_frame,
        text=f'Level {character["level"]} {character["race"]} {character["class"]}',
        bg=arc_bg, fg=arc_fg, font=STYLE["font_normal"]
    ).grid(row=0, column=2, padx=10, pady=4)

    # --- Ability Checks ---
    stats_frame = tk.LabelFrame(scrollable_frame, text="Ability Checks", padx=10, pady=5, bg=arc_bg, fg=arc_fg, font=STYLE["font_title"])
    stats_frame.pack(fill="x", pady=6, padx=6)

    result_labels = {}
    for col, ability in enumerate(character["stats"].keys()):
        btn = ttk.Button(
            stats_frame,
            text=f"{ability} ({mods[ability]})",
            command=lambda a=ability: result_labels[a].config(text=ability_check(a)),
            style="Accent.TButton"
        )
        btn.grid(row=0, column=col, padx=6, pady=4)
        lbl = tk.Label(stats_frame, text="", bg=arc_bg, fg=arc_fg, font=STYLE["font_normal"])
        lbl.grid(row=1, column=col, padx=6, pady=4)
        result_labels[ability] = lbl
        
    # --- Skills Section ---
    skills_frame = tk.LabelFrame(scrollable_frame, text="Skills", padx=10, pady=5, bg=arc_bg, fg=arc_fg, font=STYLE["font_title"])
    skills_frame.pack(fill="x", padx=6, pady=6)

    skill_result_labels = {}

    for i, skill_name in enumerate(character["skills"].keys()):
        mod = skill_modifier(skill_name)

        row = i // 3
        col = (i % 3) * 2  # leave space for button + label

        btn = ttk.Button(
            skills_frame,
            text=f"{skill_name} ({mod:+})",
            command=lambda s=skill_name: skill_result_labels[s].config(
                text=f"{roll(20) + skill_modifier(s)}"
            ),
            style="Accent.TButton"
        )
        btn.grid(row=row*2, column=col, sticky="w", pady=4, padx=6)

        lbl = tk.Label(skills_frame, text="", bg=arc_bg, fg=arc_fg, font=STYLE["font_normal"])
        lbl.grid(row=row*2+1, column=col, sticky="w", pady=4, padx=6)

        skill_result_labels[skill_name] = lbl

    # --- Custom Roller ---
    roller_frame = tk.LabelFrame(scrollable_frame, text="Custom Roller", padx=10, pady=5, bg=arc_bg, fg=arc_fg, font=STYLE["font_title"])
    roller_frame.pack(fill="x", pady=6, padx=6)

    dice_count_entry = tk.Entry(roller_frame, width=5, bg=arc_bg, fg=arc_fg, insertbackground=arc_fg, font=STYLE["font_normal"])
    dice_count_entry.insert(0, "1")
    dice_count_entry.grid(row=0, column=0, padx=6, pady=4)

    tk.Label(roller_frame, text="d", bg=arc_bg, fg=arc_fg, font=STYLE["font_normal"]).grid(row=0, column=1, padx=6, pady=4)
    dice_sides_entry = tk.Entry(roller_frame, width=5, bg=arc_bg, fg=arc_fg, insertbackground=arc_fg, font=STYLE["font_normal"])
    dice_sides_entry.insert(0, "20")
    dice_sides_entry.grid(row=0, column=2, padx=6, pady=4)

    result_label = tk.Label(roller_frame, text="", bg=arc_bg, fg=arc_fg, font=STYLE["font_normal"])
    result_label.grid(row=1, column=0, columnspan=3, pady=6, padx=6)

    def roll_custom():
        try:
            count = int(dice_count_entry.get())
            sides = int(dice_sides_entry.get())
            result = roll(sides, count)
            result_label.config(text=f"Rolled {count}d{sides}: {result}")
        except ValueError:
            result_label.config(text="Please enter valid numbers!")

    roll_button = ttk.Button(
        roller_frame,
        text="Roll!",
        command=roll_custom,
        style="Accent.TButton"
    )
    roll_button.grid(row=0, column=3, padx=10, pady=4)

    # --- Weapons ---
    weapons_frame = tk.LabelFrame(scrollable_frame, text="Weapons", padx=10, pady=5,  bg=arc_bg, fg=arc_fg, font=STYLE["font_title"])
    weapons_frame.pack(fill="x", pady=6, padx=6)

    for row, (weapon_name, weapon) in enumerate(character["weapons"].items()):
        tk.Label(weapons_frame, text=weapon_name, bg=arc_bg, fg=arc_fg, font=STYLE["font_normal"]).grid(row=row, column=0, padx=6, pady=4, sticky="w")

        hit_result = tk.Label(weapons_frame, text="", bg=arc_bg, fg=arc_fg, font=STYLE["font_normal"])
        hit_result.grid(row=row, column=2, padx=6, pady=4)
        ttk.Button(
            weapons_frame,
            text="Roll to Hit",
            command=lambda w=weapon, lbl=hit_result: lbl.config(
                text=f"Hit: {roll(20) + w['hit_mod']}",
                background=arc_bg
            ),
            style="Accent.TButton"
        ).grid(row=row, column=1, padx=6, pady=4)

        dmg_result = tk.Label(weapons_frame, text="", bg=arc_bg, fg=arc_fg, font=STYLE["font_normal"])
        dmg_result.grid(row=row, column=4, padx=6, pady=4)
        ttk.Button(
            weapons_frame,
            text="Roll Damage",
            command=lambda w=weapon, lbl=dmg_result: lbl.config(
                text=f"Damage: {roll(w['damage_die'], w['damage_die_count']) + w['damage_mod']}",
            ),
            style="Accent.TButton"
        ).grid(row=row, column=3, padx=6, pady=4)

    # --- Combat Stats ---
    combat_frame = tk.LabelFrame(scrollable_frame, text="Combat Stats", padx=10, pady=5, bg=arc_bg, fg=arc_fg, font=STYLE["font_title"])
    combat_frame.pack(fill="x", pady=6, padx=6)

    tk.Label(combat_frame, text="HP:", bg=arc_bg, fg=arc_fg, font=STYLE["font_normal"]).grid(row=0, column=0, sticky="e", padx=6, pady=4)
    hp_current_entry = tk.Entry(combat_frame, width=5, bg=arc_bg, fg=arc_fg, insertbackground=arc_fg, font=STYLE["font_normal"])
    hp_current_entry.insert(0, character["hp"]["current"])
    hp_current_entry.grid(row=0, column=1, padx=6, pady=4)
    tk.Label(combat_frame, text="/", bg=arc_bg, fg=arc_fg, font=STYLE["font_normal"]).grid(row=0, column=2, padx=6, pady=4)
    hp_max_entry = tk.Entry(combat_frame, width=5, bg=arc_bg, fg=arc_fg, insertbackground=arc_fg, font=STYLE["font_normal"])
    hp_max_entry.insert(0, character["hp"]["max"])
    hp_max_entry.grid(row=0, column=3, padx=6, pady=4)

    tk.Label(combat_frame, text="AC:", bg=arc_bg, fg=arc_fg, font=STYLE["font_normal"]).grid(row=1, column=0, sticky="e", padx=6, pady=4)
    ac_entry = tk.Entry(combat_frame, width=5, bg=arc_bg, fg=arc_fg, insertbackground=arc_fg, font=STYLE["font_normal"])
    ac_entry.insert(0, character["ac"])
    ac_entry.grid(row=1, column=1, padx=6, pady=4)

    def roll_initiative():
        roll_val = random.randint(1, 20)
        total = roll_val + mods["DEX"]
        initiative_result_label.config(text=total)

    tk.Label(combat_frame, text="Initiative:", bg=arc_bg, fg=arc_fg, font=STYLE["font_normal"]).grid(row=2, column=0, sticky="e", padx=6, pady=4)
    initiative_button = ttk.Button(
        combat_frame,
        text=f"{mods['DEX']:+}",
        command=roll_initiative,
        style="Accent.TButton"
    )
    initiative_button.grid(row=2, column=1, padx=6, pady=4)
    initiative_result_label = tk.Label(combat_frame, text="", bg=arc_bg, fg=arc_fg, font=STYLE["font_normal"])
    initiative_result_label.grid(row=2, column=2, sticky="w", padx=6, pady=4)

    # --- Notes and Inventory (side by side) ---
    bottom_frame = tk.Frame(scrollable_frame, padx=10, pady=5, bg=arc_bg)
    bottom_frame.pack(fill="both", expand=True, padx=6, pady=6)

    notes_frame = tk.LabelFrame(bottom_frame, text="Notes", padx=10, pady=5, bg=arc_bg, fg=arc_fg, font=STYLE["font_title"])
    notes_frame.pack(side="left", fill="both", expand=True, padx=6, pady=6)

    notes_text = tk.Text(notes_frame, height=10, wrap="word", bg=arc_bg, fg=arc_fg, insertbackground=arc_fg, selectbackground=STYLE["accent2"], font=STYLE["font_normal"])
    notes_text.insert("1.0", character["notes"])
    notes_text.pack(fill="both", expand=True, padx=6, pady=6)

    inventory_frame = tk.LabelFrame(bottom_frame, text="Inventory", padx=10, pady=5, bg=arc_bg, fg=arc_fg, font=STYLE["font_title"])
    inventory_frame.pack(side="right", fill="both", expand=True, padx=6, pady=6)

    inventory_listbox = tk.Listbox(inventory_frame, height=10, bg=arc_bg, fg=arc_fg, selectbackground=STYLE["accent2"], font=STYLE["font_normal"])
    inventory_listbox.pack(fill="both", expand=True, padx=6, pady=6)
    for item in character["inventory"]:
        inventory_listbox.insert(tk.END, item)

    new_item_entry = tk.Entry(inventory_frame, bg="#FFFFFF", fg=arc_fg, insertbackground=arc_fg, font=STYLE["font_normal"])
    new_item_entry.pack(fill="x", pady=6, padx=6)

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

    ttk.Button(
        inventory_frame,
        text="Add",
        command=add_item,
        style="Accent.TButton"
    ).pack(side="left", padx=6, pady=6)
    ttk.Button(
        inventory_frame,
        text="Remove Selected",
        command=remove_item,
        style="Accent.TButton"
    ).pack(side="right", padx=6, pady=6)

    # --- Save / Load Buttons ---
    control_frame = tk.Frame(scrollable_frame, pady=10, bg=arc_bg)
    control_frame.pack(fill="x", padx=6, pady=6)
    ttk.Button(
        control_frame,
        text="Save Character",
        command=save_to_file,
        style="Accent.TButton"
    ).pack(side="left", padx=10, pady=6)
    ttk.Button(
        control_frame,
        text="Load Character",
        command=load_from_file,
        style="Accent.TButton"
    ).pack(side="left", padx=10, pady=6)

    root.mainloop()
    
if __name__ == "__main__":
    gui_app()
