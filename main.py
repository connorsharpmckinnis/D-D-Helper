import random
import tkinter as tk

stats = {
    "STR": 10, 
    "DEX": 15,
    "CON": 14,
    "INT": 8,
    "WIS": 10,
    "CHA": 8
}

weapons = {
    "Longsword": {
        "hit_mod": 3,
        "damage_die": 6,
        "damage_die_count": 1,
        "damage_mod": 2,
    },
    "Shortbow": {
        "hit_mod": 3,
        "damage_die": 6,
        "damage_die_count": 1,
        "damage_mod": 2,
    }
}

def roll_to_hit(weapon):
    return roll_with_mod(20, 1, weapon['hit_mod'])

def roll_damage(weapon):
    return roll(weapon["damage_die"], weapon["damage_die_count"]) + weapon["damage_mod"]


def mod_formula(stat):
    value = ((stats[stat] - 10) // 2)
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
    
    root = tk.Tk()

    root.title("D&D Helper")
    root.geometry("600x400")
    label = tk.Label(root, text="Hello, Adventurer!")    
    label.grid(row=0,column=0, columnspan=6, pady=10)
    
    result_labels = {}
    for col, ability in enumerate(stats.keys()):
        btn = tk.Button(
            root,
            text=f"{ability} ({mods[ability]})",
            command=lambda a=ability: result_labels[a].config(text=ability_check(a))
        )
        btn.grid(row=1, column=col, padx=10, pady=5)
        
        lbl = tk.Label(root, text="")
        lbl.grid(row=2, column=col)
        result_labels[ability] = lbl
    
    tk.Label(root, text="Roll Anything").grid(row=3, column=1, columnspan=2, pady=10)
    
    dice_count_entry = tk.Entry(root, width=5)
    dice_count_entry.insert(0, "1")  # default
    dice_count_entry.grid(row=4, column=0)

    tk.Label(root, text="d").grid(row=4, column=1)
    dice_sides_entry = tk.Entry(root, width=5)
    dice_sides_entry.insert(0, "20")  # default
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

    weapon_result_labels = {}

    for row, (weapon_name, weapon) in enumerate(weapons.items(), start=7):
        # Weapon name
        tk.Label(root, text=weapon_name).grid(row=row, column=0, padx=10, sticky="w")

        # Roll to Hit
        hit_result = tk.Label(root, text="")
        hit_result.grid(row=row, column=2, padx=5)
        hit_button = tk.Button(
            root, text="Roll to Hit",
            command=lambda w=weapon, lbl=hit_result: lbl.config(
                text=f"Hit: {roll(20) + w['hit_mod']}"
            )
        )
        hit_button.grid(row=row, column=1, padx=5)

        # Roll Damage
        dmg_result = tk.Label(root, text="")
        dmg_result.grid(row=row, column=4, padx=5)
        dmg_button = tk.Button(
            root, text="Roll Damage",
            command=lambda w=weapon, lbl=dmg_result: lbl.config(
                text=f"Damage: {roll(w['damage_die'], w['damage_die_count']) + w['damage_mod']}"
            )
        )
        dmg_button.grid(row=row, column=3, padx=5)
    
    root.mainloop()
    
if __name__ == "__main__":
    gui_app()