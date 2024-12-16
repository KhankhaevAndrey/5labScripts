import asyncio
import sqlite3
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QProgressBar, QLabel
from PyQt5.QtCore import QTimer
import aiohttp
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Асинхронное приложение")
        self.setGeometry(100, 100, 700, 500)

        self.layout = QVBoxLayout()
        self.load_button = QPushButton("Загрузить данные")
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("Ожидание...")
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ID", "Title", "Body"])

        self.layout.addWidget(self.load_button)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)


        self.load_button.clicked.connect(self.load_data)


        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(10000)


        self.init_db()

        self.db_lock = asyncio.Lock()

    def init_db(self):
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            title TEXT,
            body TEXT
        )
        """)
        conn.commit()
        conn.close()

    async def fetch_data(self):
        url = "https://jsonplaceholder.typicode.com/posts"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                await asyncio.sleep(2)
                return await response.json()

    async def save_data(self, data):
        async with self.db_lock:
            conn = sqlite3.connect("data.db", check_same_thread=False)
            cursor = conn.cursor()
            for item in data:
                cursor.execute("INSERT OR IGNORE INTO posts (id, title, body) VALUES (?, ?, ?)",
                               (item['id'], item['title'], item['body']))
            conn.commit()
            conn.close()

    def display_data(self):
        conn = sqlite3.connect("data.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM posts")
        rows = cursor.fetchall()
        self.table.setRowCount(0)
        for row in rows:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            for column, value in enumerate(row):
                self.table.setItem(row_position, column, QTableWidgetItem(str(value)))
        conn.close()



    async def load_data_task(self):
            self.status_label.setText("Загрузка даных")
            self.progress_bar.setValue(0)

            await asyncio.sleep(1)
            self.progress_bar.setValue(24)

            data = await self.fetch_data()
            self.progress_bar.setValue(50)

            await asyncio.sleep(1)
            self.progress_bar.setValue(72)


            await self.save_data(data)
            self.progress_bar.setValue(100)


            self.display_data()
            self.status_label.setText("Готово")


            await asyncio.sleep(0.5)
            self.progress_bar.setValue(0)

    def load_data(self):
        asyncio.create_task(self.load_data_task())

    def update_data(self):
        asyncio.create_task(self.load_data_task())



app = QApplication(sys.argv)

loop = asyncio.get_event_loop()

window = MainWindow()
window.show()


async def run_qt_app():
    while True:
        await asyncio.sleep(0.01)
        app.processEvents()

loop.run_until_complete(run_qt_app())
