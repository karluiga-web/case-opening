# -------------------------------------------------
# main.py
# CS2 Case Opening Simulator with Multi-Case, Qualities & Auto-Sell
# -------------------------------------------------

import tkinter as tk
import random
import time
import threading

# Import full CS2 case list
from cases import CASES

# -------------------------------------------------
# REAL CS2 DROP CHANCES
# -------------------------------------------------

RARITY_CHANCES = {
    "Mil-Spec": 0.7992,
    "Restricted": 0.1598,
    "Classified": 0.0320,
    "Covert": 0.0064,
    "Rare Special": 0.0026
}

STATTRAK_CHANCES = {
    "Mil-Spec": 0.0799,
    "Restricted": 0.0160,
    "Classified": 0.0032,
    "Covert": 0.0006,
    "Rare Special": 0.0003
}

KEY_PRICE = 2.49   # Real CS2 key cost

# -------------------------------------------------
# SELLING CONFIG
# -------------------------------------------------

SELL_PRICES = {
    "Mil-Spec": 5,
    "Restricted": 15,
    "Classified": 40,
    "Covert": 250,
    "Rare Special": 1000
}

STAT_TRACK_MULTIPLIER = 2

# -------------------------------------------------
# SKIN QUALITIES
# -------------------------------------------------

QUALITIES = {
    "Factory New": 0.20,
    "Minimal Wear": 0.25,
    "Field-Tested": 0.30,
    "Well-Worn": 0.15,
    "Battle-Scarred": 0.10
}

def roll_quality():
    r = random.random()
    cum = 0
    for qual, prob in QUALITIES.items():
        cum += prob
        if r < cum:
            return qual
    return "Field-Tested"

# -------------------------------------------------
# MAIN GAME CLASS
# -------------------------------------------------

class CaseGame:
    def __init__(self, root):
        self.root = root
        self.root.title("CS2 Case Opening Simulator")
        self.balance = 500
        self.inventory = []

        # -----------------------------
        # UI LAYOUT
        # -----------------------------

        top = tk.Frame(root)
        top.pack(pady=10)

        mid = tk.Frame(root)
        mid.pack(pady=10)

        bot = tk.Frame(root)
        bot.pack(pady=10)

        # BALANCE LABEL
        self.balance_label = tk.Label(top, text=f"Balance: ${self.balance}", font=("Arial", 18))
        self.balance_label.pack()

        # CASE SELECTOR
        self.selected_case = tk.StringVar(value=list(CASES.keys())[0])

        self.case_menu = tk.OptionMenu(
            mid, self.selected_case, *CASES.keys(),
            command=lambda _: self.update_case_price()
        )
        self.case_menu.config(font=("Arial", 14))
        self.case_menu.pack()

        # PRICE LABEL
        self.case_price_label = tk.Label(mid, text="", font=("Arial", 14))
        self.case_price_label.pack()
        self.update_case_price()

        # OPEN BUTTON
        self.open_button = tk.Button(mid, text="Open Case", font=("Arial", 16),
                                     command=self.start_case)
        self.open_button.pack(pady=5)

        # MULTI-CASE OPEN BUTTON
        self.multi_case_frame = tk.Frame(mid)
        self.multi_case_frame.pack(pady=5)

        tk.Label(self.multi_case_frame, text="Multi-Case Count:", font=("Arial", 12)).pack(side="left")
        self.multi_case_count = tk.IntVar(value=5)
        tk.Entry(self.multi_case_frame, textvariable=self.multi_case_count, width=5, font=("Arial", 12)).pack(side="left", padx=5)
        tk.Button(self.multi_case_frame, text="Open Multiple Cases", font=("Arial", 12),
                  command=self.start_multi_case).pack(side="left", padx=5)

        # SPIN RESULT LABEL
        self.rolling_label = tk.Label(mid, text="", font=("Arial", 20, "bold"), width=45, height=2)
        self.rolling_label.pack(pady=20)

        # INVENTORY
        tk.Label(bot, text="Inventory:", font=("Arial", 16)).pack()
        self.inventory_box = tk.Listbox(bot, width=70, height=10, font=("Arial", 12))
        self.inventory_box.pack()
        self.inventory_box.bind("<<ListboxSelect>>", self.on_select)

        # SELL BUTTON
        self.sell_button = tk.Button(bot, text="Sell Selected Item", font=("Arial", 14),
                                     state="disabled", command=self.sell_item)
        self.sell_button.pack(pady=5)

        # INVENTORY VALUE LABEL
        self.inventory_value_label = tk.Label(bot, text="Inventory Value: $0", font=("Arial", 14))
        self.inventory_value_label.pack(pady=5)

        # SELL ALL OF A RARITY
        self.sell_all_frame = tk.Frame(bot)
        self.sell_all_frame.pack(pady=5)

        self.sell_rarity_var = tk.StringVar(value="Mil-Spec")
        rarities = ["Mil-Spec", "Restricted", "Classified", "Covert", "Rare Special"]
        self.sell_all_menu = tk.OptionMenu(self.sell_all_frame, self.sell_rarity_var, *rarities)
        self.sell_all_menu.config(font=("Arial", 12))
        self.sell_all_menu.pack(side="left", padx=5)

        self.sell_all_button = tk.Button(self.sell_all_frame, text="Sell All of Rarity",
                                         font=("Arial", 12), command=self.sell_all_rarity)
        self.sell_all_button.pack(side="left", padx=5)

        # AUTO-SELL OPTIONS
        self.auto_sell_frame = tk.LabelFrame(bot, text="Auto-Sell Options", font=("Arial", 12))
        self.auto_sell_frame.pack(pady=5)

        self.auto_sell_vars = {}
        for rarity in rarities:
            var = tk.BooleanVar(value=False)
            chk = tk.Checkbutton(self.auto_sell_frame, text=rarity, variable=var, font=("Arial", 12))
            chk.pack(side="left", padx=5)
            self.auto_sell_vars[rarity] = var

        self.selected_index = None

    # -------------------------------------------------
    # UPDATE CASE PRICE DISPLAY
    # -------------------------------------------------

    def update_case_price(self):
        case_name = self.selected_case.get()
        case_price = CASES[case_name]["price"]
        total_cost = case_price + KEY_PRICE
        self.case_price_label.config(
            text=f"Case Price: ${case_price:.2f}  |  Key: ${KEY_PRICE:.2f}  |  Total: ${total_cost:.2f}"
        )

    # -------------------------------------------------
    # SINGLE CASE OPEN
    # -------------------------------------------------

    def start_case(self):
        self.open_button.config(state="disabled")
        threading.Thread(target=self.case_animation).start()

    # -------------------------------------------------
    # MULTI-CASE OPEN
    # -------------------------------------------------

    def start_multi_case(self):
        count = self.multi_case_count.get()
        if count <= 0:
            self.rolling_label.config(text="Enter a valid number of cases!", fg="red")
            return
        self.open_button.config(state="disabled")
        threading.Thread(target=self.multi_case_animation, args=(count,)).start()

    def multi_case_animation(self, count):
        for _ in range(count):
            self.case_animation()
            time.sleep(0.1)
        self.open_button.config(state="normal")

    # -------------------------------------------------
    # CASE ANIMATION LOGIC
    # -------------------------------------------------

    def case_animation(self):
        case_name = self.selected_case.get()
        case_price = CASES[case_name]["price"]
        total_cost = case_price + KEY_PRICE

        if self.balance < total_cost:
            self.rolling_label.config(text="Not enough money!", fg="red")
            return

        self.balance -= total_cost
        self.update_balance()

        items = CASES[case_name]["items"]

        # Fake spin animation
        for _ in range(15):
            rarity = random.choice(list(items.keys()))
            name, color = random.choice(items[rarity])
            self.set_label(name, color)
            time.sleep(0.03)

        # Real drop
        rarity = self.roll_rarity()
        name, color = random.choice(items[rarity])
        is_st = random.random() < STATTRAK_CHANCES[rarity]
        display = ("StatTrak™ " if is_st else "") + name
        quality = roll_quality()
        display_with_quality = f"{display} [{quality}]"

        # AUTO-SELL
        if self.auto_sell_vars.get(rarity, tk.BooleanVar()).get():
            value = SELL_PRICES[rarity] * (STAT_TRACK_MULTIPLIER if is_st else 1)
            self.balance += value
            self.set_label(f"Auto-sold {display_with_quality} for ${value}", "green")
        else:
            self.inventory.append((name, rarity, color, is_st, quality))
            self.inventory_box.insert(tk.END, f"{display_with_quality} ({rarity})")
            self.set_label(display_with_quality, "orange" if is_st else color)

        self.update_inventory_value()

    # -------------------------------------------------
    # REAL CS2 RARITY SYSTEM
    # -------------------------------------------------

    def roll_rarity(self):
        r = random.random()
        cum = 0
        for rarity, prob in RARITY_CHANCES.items():
            cum += prob
            if r < cum:
                return rarity
        return "Mil-Spec"

    # -------------------------------------------------
    # SELLING ITEMS
    # -------------------------------------------------

    def on_select(self, event):
        sel = self.inventory_box.curselection()
        if sel:
            self.selected_index = sel[0]
            self.sell_button.config(state="normal")
        else:
            self.sell_button.config(state="disabled")

    def sell_item(self):
        if self.selected_index is None:
            return

        name, rarity, color, is_st, quality = self.inventory[self.selected_index]
        value = SELL_PRICES[rarity] * (STAT_TRACK_MULTIPLIER if is_st else 1)

        self.balance += value
        self.update_balance()

        del self.inventory[self.selected_index]
        self.inventory_box.delete(self.selected_index)

        self.update_inventory_value()
        self.sell_button.config(state="disabled")

    def sell_all_rarity(self):
        rarity_to_sell = self.sell_rarity_var.get()
        total = 0
        indexes_to_remove = []

        for i, (name, rarity, color, is_st, quality) in enumerate(self.inventory):
            if rarity == rarity_to_sell:
                total += SELL_PRICES[rarity] * (STAT_TRACK_MULTIPLIER if is_st else 1)
                indexes_to_remove.append(i)

        if total == 0:
            self.rolling_label.config(text=f"No {rarity_to_sell} items to sell!", fg="red")
            return

        self.balance += total
        self.update_balance()

        for i in reversed(indexes_to_remove):
            del self.inventory[i]
            self.inventory_box.delete(i)

        self.update_inventory_value()
        self.rolling_label.config(text=f"Sold all {rarity_to_sell} items for ${total}", fg="green")

    # -------------------------------------------------
    # UI HELPERS
    # -------------------------------------------------

    def update_balance(self):
        self.balance_label.config(text=f"Balance: ${self.balance}")

    def update_inventory_value(self):
        total = 0
        for name, rarity, color, is_st, quality in self.inventory:
            total += SELL_PRICES[rarity] * (STAT_TRACK_MULTIPLIER if is_st else 1)
        self.inventory_value_label.config(text=f"Inventory Value: ${total}")

    def set_label(self, text, color):
        self.rolling_label.config(text=text, fg=color)

# -------------------------------------------------
# RUN GAME
# -------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    game = CaseGame(root)
    root.mainloop()