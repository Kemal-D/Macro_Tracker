import tkinter as tk
from tkinter import ttk, Menu, simpledialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import datetime

# Database setup
engine = create_engine('sqlite:///macro_tracker.db', echo=False)  # Turn off echo for production
Session = scoped_session(sessionmaker(bind=engine))  # Use scoped_session for better session management
Base = declarative_base()

# Define database models
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

Base.metadata.create_all(engine)  # Create tables based on models

# Load foods from Excel while reducing database calls
def load_foods_from_excel(filepath):
    session = Session()
    try:
        existing_foods = {food.name for food in session.query(Food.name).all()}  # Load existing food names into a set
        df = pd.read_excel(filepath)
        for index, row in df.iterrows():
            if row['name'] not in existing_foods:
                session.add(Food(
                    name=row['name'],
                    calories=int(row['calories']),
                    protein=float(row['protein']),
                    fat=float(row['fat']),
                    carbohydrates=float(row['carbohydrates'])
                ))
                existing_foods.add(row['name'])
        session.commit()
    except Exception as e:
        messagebox.showerror("Error Loading Excel", f"An error occurred: {e}")
    finally:
        session.close()  # Ensure the session is closed after operation

load_foods_from_excel('Foods.xlsx')  # Load foods at startup

# Setup the main application window
root = tk.Tk()
root.title("Macro Tracker")
root.geometry('1000x600')

# Configure menu
menu_bar = Menu(root)
root.config(menu=menu_bar)
file_menu = Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Exit", command=root.quit)
menu_bar.add_cascade(label="File", menu=file_menu)

# Setup frames for UI
frame = ttk.Frame(root, padding="20")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
chart_frame = ttk.Frame(root, padding="20")
chart_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

# Dropdown for selecting food
ttk.Label(frame, text="Select Food:").grid(column=0, row=0, sticky=tk.W)
food_combobox = ttk.Combobox(frame, width=25)
food_combobox.grid(column=1, row=0)

# Setup the pie chart
fig, ax = plt.subplots(figsize=(5, 5))
chart = FigureCanvasTkAgg(fig, chart_frame)
chart.get_tk_widget().pack()

# Function to refresh the list of foods in the dropdown
def refresh_foods():
    session = Session()
    try:
        foods = session.query(Food).all()
        food_combobox['values'] = [f.name for f in foods]
    finally:
        session.close()

refresh_foods()

# Function to update the pie chart with the latest food entries
def update_chart():
    session = Session()
    try:
        today = datetime.datetime.now().date()
        totals = session.query(
            FoodEntry.calories, FoodEntry.protein, FoodEntry.fat, FoodEntry.carbohydrates
        ).filter(FoodEntry.date == today).all()
        if totals:
            data = [sum(items) for items in zip(*totals)]
            ax.clear()
            ax.pie(data[1:], labels=['Protein', 'Fat', 'Carbs'], autopct='%1.1f%%')
            ax.set_title(f"Total Calories: {data[0]}")
            chart.draw()
    finally:
        session.close()

# Function to add a selected food to the daily entries
def add_selected_food():
    session = Session()
    try:
        food = session.query(Food).filter(Food.name == food_combobox.get()).first()
        if food:
            session.add(FoodEntry(food_name=food.name, **{attr: getattr(food, attr) for attr in ['calories', 'protein', 'fat', 'carbohydrates']}))
            session.commit()
            update_chart()
            messagebox.showinfo("Info", f"Added {food.name} to today's intake")
    finally:
        session.close()

add_button = ttk.Button(frame, text="Add Selected Food", command=add_selected_food)
add_button.grid(column=1, row=1)

# Function to close the application and cleanup
def on_close(root):
    """ Close the application cleanly. """
    try:
        db_session.remove()
        engine.dispose()  # Close the connection pool
    finally:
        root.destroy()

root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))

load_foods_from_excel('Foods.xlsx')
root.mainloop()
