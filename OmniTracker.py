import sys
from io import StringIO
import datetime as dt
from PyQt6.QtWidgets import QMainWindow, QApplication, QMenuBar
from PyQt6 import uic

class OmniTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        with open('OmniTracker.ui', 'r', encoding='utf8') as f:
            ui_data = f.read()
            uic.loadUi(StringIO(ui_data), self)
        self.setFixedHeight(640)
        self.setFixedWidth(791)
        self.setWindowTitle('OmniTracker')

        self.todo.move(0, 0)
        self.diary.move(0, 0)
        self.schedule.move(0, 0)

        # -------------Создание меню и действий---------------
        self.menu_bar = QMenuBar(self)
        self.menu_bar.resize(100, 20)

        self.main_menu = self.menu_bar.addAction('Главная панель')
        self.todo_act = self.menu_bar.addAction('Задачник')
        self.diary_act = self.menu_bar.addAction('Ежедневник')
        self.schedule_act = self.menu_bar.addAction('Планировщик')
        self.results_act = self.menu_bar.addAction('Результаты')
        self.settings_act = self.menu_bar.addAction('Настройки')

        # --------------Привязка действий------------------------

        self.main_menu.triggered.connect(self.main_open)
        self.todo_act.triggered.connect(self.todo_open)
        self.diary_act.triggered.connect(self.diary_open)
        self.schedule_act.triggered.connect(self.schedule_open)

        self.main_open()

    def main_open(self):
        self.schedule.hide()
        self.diary.hide()
        self.todo.hide()
        self.general.show()

    def todo_open(self):
        self.schedule.hide()
        self.diary.hide()
        self.todo.show()
        self.general.hide()

    def diary_open(self):
        self.schedule.hide()
        self.diary.show()
        self.todo.hide()
        self.general.hide()

    def schedule_open(self):
        self.schedule.show()
        self.diary.hide()
        self.todo.hide()
        self.general.hide()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    om = OmniTracker()
    om.show()
    sys.exit(app.exec())