import os
from dotenv import load_dotenv
import datetime
import asyncio
from telethon import TelegramClient
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pytz  # Для роботи з часовими зонами

# Завантаження змінних з .env
load_dotenv()

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')

client = TelegramClient('session_name', api_id, api_hash)

async def fetch_channel_statistics(channel_username, start_date, end_date):
    try:
        await client.start()
        channel = await client.get_entity(channel_username)

        total_messages = 0
        total_views = 0
        total_reactions = 0
        total_comments = 0

        async for message in client.iter_messages(channel, offset_date=end_date, reverse=True):
            if message.date < start_date:
                break

            total_messages += 1
            total_views += message.views if message.views else 0
            total_reactions += sum(reaction.count for reaction in message.reactions.results) if message.reactions else 0
            total_comments += message.replies.replies if message.replies else 0

        return {
            "total_messages": total_messages,
            "total_views": total_views,
            "total_reactions": total_reactions,
            "total_comments": total_comments,
            "average_views": total_views / total_messages if total_messages > 0 else 0,
            "average_reactions": total_reactions / total_messages if total_messages > 0 else 0,
            "average_comments": total_comments / total_messages if total_messages > 0 else 0
        }
    except Exception as e:
        print(f"Помилка отримання статистики: {e}")
        return None

def start_analysis():
    channel_name = channel_entry.get()
    start_date = start_date_entry.get()
    end_date = end_date_entry.get()

    try:
        # Конвертуємо дати в datetime з часовою зоною UTC
        timezone = pytz.UTC
        start_date_obj = timezone.localize(datetime.datetime.strptime(start_date, '%Y-%m-%d'))
        end_date_obj = timezone.localize(datetime.datetime.strptime(end_date, '%Y-%m-%d'))
        
        # Використання існуючого циклу подій
        loop = asyncio.get_event_loop()
        if loop.is_running():
            statistics_future = asyncio.ensure_future(fetch_channel_statistics(channel_name, start_date_obj, end_date_obj))
            loop.run_until_complete(statistics_future)
            statistics = statistics_future.result()
        else:
            statistics = loop.run_until_complete(fetch_channel_statistics(channel_name, start_date_obj, end_date_obj))

        if statistics:
            display_statistics(statistics)
        else:
            tk.messagebox.showerror("Помилка", "Немає даних за вибраний період.")
    except Exception as e:
        tk.messagebox.showerror("Помилка", f"Сталася помилка: {e}")

def display_statistics(statistics):
    for child in stats_tree.get_children():
        stats_tree.delete(child)
    
    metrics = [
        ("Загальна кількість повідомлень", statistics["total_messages"]),
        ("Загальна кількість переглядів", statistics["total_views"]),
        ("Загальна кількість реакцій", statistics["total_reactions"]),
        ("Загальна кількість коментарів", statistics["total_comments"]),
        ("Середня кількість переглядів", round(statistics["average_views"], 2)),
        ("Середня кількість реакцій", round(statistics["average_reactions"], 2)),
        ("Середня кількість коментарів", round(statistics["average_comments"], 2)),
    ]
    
    for metric, value in metrics:
        stats_tree.insert("", "end", values=(metric, value))
    
    labels = ['Повідомлення', 'Перегляди', 'Реакції', 'Коментарі']
    values = [
        statistics['total_messages'],
        statistics['total_views'],
        statistics['total_reactions'],
        statistics['total_comments']
    ]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(labels, values, color='blue')
    ax.set_title("Метрики каналу")
    ax.set_xlabel("Метрики")
    ax.set_ylabel("Значення")

    for widget in graph_frame.winfo_children():
        widget.destroy()

    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.get_tk_widget().pack()
    canvas.draw()

# GUI
root = tk.Tk()
root.title("Аналізатор Телеграм-каналу")

tabs = ttk.Notebook(root)
tabs.pack(expand=1, fill="both")

analyze_tab = ttk.Frame(tabs)
tabs.add(analyze_tab, text="Аналіз")

ttk.Label(analyze_tab, text="Назва каналу:").grid(row=0, column=0, padx=5, pady=5)
channel_entry = ttk.Entry(analyze_tab, width=30)
channel_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(analyze_tab, text="Дата початку (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5)
start_date_entry = ttk.Entry(analyze_tab, width=30)
start_date_entry.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(analyze_tab, text="Дата закінчення (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5)
end_date_entry = ttk.Entry(analyze_tab, width=30)
end_date_entry.grid(row=2, column=1, padx=5, pady=5)

start_button = ttk.Button(analyze_tab, text="Розпочати аналіз", command=start_analysis)
start_button.grid(row=3, column=0, columnspan=2, pady=10)

stats_frame = ttk.Frame(analyze_tab)
stats_frame.grid(row=4, column=0, columnspan=2, pady=10)

stats_tree = ttk.Treeview(stats_frame, columns=("Метрика", "Значення"), show="headings", height=7)
stats_tree.heading("Метрика", text="Метрика")
stats_tree.heading("Значення", text="Значення")
stats_tree.pack()

graph_tab = ttk.Frame(tabs)
tabs.add(graph_tab, text="Графік")

graph_frame = ttk.Frame(graph_tab)
graph_frame.pack(fill="both", expand=True)

root.mainloop()
