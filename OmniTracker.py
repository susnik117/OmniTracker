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
        self.setFixedHeight(642)
        self.setFixedWidth(791)
        self.setWindowTitle('OmniTracker')
        self.todays_date = dt.date.today()
        self.general_open()

        self.todo_plus.hide()
        self.diary_plus.hide()
        self.schedule_plus.hide()

        self.todo.move(0, 0)
        self.diary.move(0, 0)
        self.schedule.move(0, 0)
        self.results.move(0, 0)
        self.settings.move(0, 0)

        # -------------Создание меню и действий---------------
        self.menu_bar = QMenuBar(self)
        self.menu = self.menu_bar.addMenu('Открыть')

        self.general_menu = self.menu.addAction('Главная панель')
        self.todo_act = self.menu.addAction('Задачник')
        self.diary_act = self.menu.addAction('Ежедневник')
        self.schedule_act = self.menu.addAction('Планировщик')
        self.results_act = self.menu.addAction('Результаты')
        self.settings_act = self.menu.addAction('Настройки')

        # --------------Привязка действий------------------------

        self.general_menu.triggered.connect(self.general_open)
        self.todo_act.triggered.connect(self.todo_open)
        self.diary_act.triggered.connect(self.diary_open)
        self.schedule_act.triggered.connect(self.schedule_open)
        self.results_act.triggered.connect(self.results_open)
        self.settings_act.triggered.connect(self.settings_open)

        # --------------Привязка кнопок---------------------
        self.diarybtn_todo.clicked.connect(self.diary_open)
        self.diarybtn_schedule.clicked.connect(self.diary_open)
        self.todobtn_diary.clicked.connect(self.todo_open)
        self.todobtn_schedule.clicked.connect(self.todo_open)
        self.schedulebtn_todo.clicked.connect(self.schedule_open)
        self.schedulebtn_diary.clicked.connect(self.schedule_open)

        self.plus_btn.clicked.connect(self.plus)

        self.todo_plus.clicked.connect(self.todo_open_plus)
        self.diary_plus.clicked.connect(self.diary_open_plus)
        self.schedule_plus.clicked.connect(self.schedule_open_plus)

    # ---------------------------Функции открывашки--------------------------------
    # TODO: сделать так, чтобы открывали другие вкладки
    def general_open(self):
        self.general.show()  # показываем только глав панель
        self.todo.hide()
        self.diary.hide()
        self.schedule.hide()
        self.results.hide()
        self.settings.hide()

        self.todo_plus.hide()
        self.diary_plus.hide()
        self.schedule_plus.hide()

        self.date.setText(f'{self.todays_date}')

    def todo_open(self):
        self.general.hide()
        self.todo.show()  # показываем только задачник
        self.diary.hide()
        self.schedule.hide()
        self.results.hide()
        self.settings.hide()

    def diary_open(self):
        self.general.hide()
        self.todo.hide()
        self.diary.show()  # показываем только ежедневник
        self.schedule.hide()
        self.results.hide()
        self.settings.hide()

    def schedule_open(self):
        self.general.hide()
        self.todo.hide()
        self.diary.hide()
        self.schedule.show()  # показываем только планировщик
        self.results.hide()
        self.settings.hide()

    def results_open(self):
        self.general.hide()
        self.todo.hide()
        self.diary.hide()
        self.schedule.hide()
        self.results.show()  # показываем только результаты
        self.settings.hide()


    def settings_open(self):
        self.general.hide()
        self.todo.hide()
        self.diary.hide()
        self.schedule.hide()
        self.results.hide()
        self.settings.show()  # показываем только настройки

        self.todo_plus.hide()
        self.diary_plus.hide()
        self.schedule_plus.hide()

    def plus(self):
        self.todo_plus.show()
        self.diary_plus.show()
        self.schedule_plus.show()

    def todo_open_plus(self):
        self.general.hide()
        self.todo.show()

    def diary_open_plus(self):
        self.general.hide()
        self.diary.show()

    def schedule_open_plus(self):
        self.general.hide()
        self.schedule.show()

    # -----------------------------Функции для добавления задач----------------------

    def todo_add(self):
        ...

if __name__ == '__main__':
    app = QApplication(sys.argv)
    om = OmniTracker()
    om.show()
    sys.exit(app.exec())
