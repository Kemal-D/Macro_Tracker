import tkinter as tk
from tkinter import ttk, Menu, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import datetime

# Database setup
engine = create_engine('sqlite:///macro_tracker.db', echo=True)
Session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

class Food(Base):
    __tablename__ = 'foods'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    calories = Column(Integer)
    protein = Column(Float)
    fat = Column(Float)
    carbohydrates = Column(Float)

class FoodEntry(Base):
    __tablename__ = 'food_entries'
    id = Column(Integer, primary_key=True)
    date = Column(Date, default=datetime.datetime.now)
    food_name = Column(String)
    calories = Column(Integer)
    protein = Column(Float)
    fat = Column(Float)
    carbohydrates = Column(Float)

Base.metadata.create_all(engine)

def load_foods_from_excel(filepath):
    try:
        with Session() as session:
            df = pd.read_excel(filepath)
            for index, row in df.iterrows():
                if not session.query(Food).filter_by(name=row['name']).first():
                    session.add(Food(
                        name=row['name'],
                        calories=int(row['calories']),
                        protein=float(row['protein']),
                        fat=float(row['fat']),
                        carbohydrates=float(row['carbohydrates'])
                    ))
            session.commit()
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load data from Excel: {e}")

root = tk.Tk()
root.title("Macro Tracker")
root.geometry('1000x600')

menu_bar = Menu(root)
root.config(menu=menu_bar)
file_menu = Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Exit", command=root.quit)
menu_bar.add_cascade(label="File", menu=file_menu)

frame = ttk.Frame(root, padding="20")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
chart_frame = ttk.Frame(root, padding="20")
chart_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

ttk.Label(frame, text="Select Food:").grid(column=0, row=0, sticky=tk.W)
food_combobox = ttk.Combobox(frame, width=25)
food_combobox.grid(column=1, row=0)

fig, ax = plt.subplots(figsize=(5, 5))
chart = FigureCanvasTkAgg(fig, chart_frame)
chart.get_tk_widget().pack()

def refresh_foods():
    with Session() as session:
        foods = session.query(Food).all()
        food_combobox['values'] = [f.name for f in foods]

def update_chart():
    with Session() as session:
        today = datetime.datetime.now().date()
        totals = session.query(
            FoodEntry.calories, FoodEntry.protein, FoodEntry.fat, FoodEntry.carbohydrates
        ).filter(FoodEntry.date == today).all()
        if totals:
            total_calories = sum(item[0] for item in totals)
            total_protein = sum(item[1] for item in totals)
            total_fat = sum(item[2] for item in totals)
            total_carbs = sum(item[3] for item in totals)
            ax.clear()
            ax.pie([total_protein, total_fat, total_carbs], labels=['Protein', 'Fat', 'Carbs'], autopct='%1.1f%%')
            ax.set_title(f"Total Calories: {total_calories}")
            chart.draw()

def add_selected_food():
    with Session() as session:
        food = session.query(Food).filter(Food.name == food_combobox.get()).first()
        if food:
            session.add(FoodEntry(
                food_name=food.name, calories=food.calories, protein=food.protein,
                fat=food.fat, carbohydrates=food.carbohydrates))
            session.commit()
            update_chart()
            messagebox.showinfo("Info", f"Added {food.name} to today's intake")

add_button = ttk.Button(frame, text="Add Selected Food", command=add_selected_food)
add_button.grid(column=1, row=1)

load_foods_from_excel('Foods.xlsx')
refresh_foods()
update_chart()

root.mainloop()
