from sys import argv, exit
from io import StringIO
from PyQt6.QtWidgets import QMainWindow, QListWidgetItem, QApplication, QMenuBar, QLineEdit, QMessageBox
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import QTime, QDate
from PyQt6 import uic
import sqlite3
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


# TODO: сделать так, чтобы панели, на которых выбираются уже существующие задачи выдвигались только тогда, когда
# TODO: соответствующие checkbox'ы нажаты

# TODO: сделать так, чтобы на вкладках с инструментами можно было переключаться между стандартной вкладкой и вкладкой +

# TODO: сейчас у меня так, что когда я перехожу между вкладками, то листы, на которых есть критерии, перезаполняются
#  Надо сделать проверку, что лист уже заполнен и в зависимости от результата заполнять или не заполнять

# TODO: можно сделать так, что некоторые из элементов интерфейса (например, QLineEdit для критериев) создавались бы не
#  в программе, а в designer'е

# TODO: сделать так, что если пользователь изменил кол-во критериев, то была возможность отредактировать бывшие критерии

# TODO: сделать так, что при повторном нажатии на "+" на главной панели кнопки закрывались


class OmniTracker(QMainWindow):
    """Класс, выполняющий функционал предложения"""

    # ================================ ИНИЦИАЛИЗАЦИЯ ==================================
    def __init__(self):
        super().__init__()
        with open('OmniTracker.ui', 'r', encoding='utf8') as f:
            ui_data = f.read()
            uic.loadUi(StringIO(ui_data), self)
        self.setFixedHeight(662)
        self.setFixedWidth(791)
        self.setWindowTitle('OmniTracker')
        self.today_weekday = str(QDate.currentDate().dayOfWeek())
        self.todays = QDate.currentDate()
        self.qtoday = QDate.toString(self.todays, 'dd-MM-yyyy')
        self.date.setText(f'{self.qtoday}')
        self.is_plus_ready = False  # для того, чтобы кнопочка "+" на глав панеле
        self.con = sqlite3.connect('tasks.sql')
        self.cur = self.con.cursor()  # курсор

        self.todo_plus.hide()
        self.diary_plus.hide()
        self.schedule_plus.hide()

        self.windows = [self.general, self.todo, self.todo_2, self.diary, self.diary_2, self.schedule, self.schedule_2,
                        self.results, self.settings]
        # все окна в один лист, чтобы можно было легко их открывать/перемещать

        self.days = [self.monday, self.tuesday, self.wednesday, self.thursday, self.friday, self.saturday, self.sunday]
        # все дни из ежедневника в один лист

        for wind in self.windows:
            wind.move(0, 0)

        self.criterion1 = QLineEdit(self)
        self.criterion2 = QLineEdit(self)
        self.criterion3 = QLineEdit(self)
        self.criterion4 = QLineEdit(self)
        self.criterion5 = QLineEdit(self)

        self.crits = [self.criterion1, self.criterion2, self.criterion3, self.criterion4, self.criterion5]  # список
        # всех полей для критериев

        y_move = 100
        for crit in self.crits:
            crit.resize(80, 20)
            crit.move(400, y_move)
            crit.hide()
            y_move += 53

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

        self.general_menu.triggered.connect(lambda: self.open('g'))
        self.todo_act.triggered.connect(lambda: self.open('t2'))
        self.diary_act.triggered.connect(lambda: self.open('d2'))
        self.schedule_act.triggered.connect(lambda: self.open('sch2'))
        self.results_act.triggered.connect(lambda: self.open('r'))
        self.settings_act.triggered.connect(lambda: self.open('se'))

        # --------------Привязка кнопок---------------------
        self.diarybtn_todo.clicked.connect(lambda: self.open('d'))  # для перемещения между инструментами в вкладках "+"
        self.diarybtn_schedule.clicked.connect(lambda: self.open('d'))
        self.todobtn_diary.clicked.connect(lambda: self.open('t'))
        self.todobtn_schedule.clicked.connect(lambda: self.open('t'))
        self.schedulebtn_todo.clicked.connect(lambda: self.open('sch'))
        self.schedulebtn_diary.clicked.connect(lambda: self.open('sch'))

        self.plus_to_normal_todo.clicked.connect(lambda: self.open('t2'))  # для перемещения между окнами "+" и обычным
        self.plus_to_normal_diary.clicked.connect(lambda: self.open('d2'))
        self.plus_to_normal_schedule.clicked.connect(lambda: self.open('sch2'))

        self.normal_to_plus_todo.clicked.connect(lambda: self.open('t'))
        self.normal_to_plus_diary.clicked.connect(lambda: self.open('d'))
        self.normal_to_plus_schedule.clicked.connect(lambda: self.open('sch'))

        self.plus_btn.clicked.connect(lambda: self.open('p'))  # для кнопки "+" на глав. панеле
        self.todo_plus.clicked.connect(lambda: self.open('t'))
        self.diary_plus.clicked.connect(lambda: self.open('d'))
        self.schedule_plus.clicked.connect(lambda: self.open('sch'))

        self.addbtn_todo.clicked.connect(self.todo_add)  # для добавления задач в инструменты
        self.addbtn_diary.clicked.connect(self.diary_add)
        self.addbtn_schedule.clicked.connect(self.schedule_add)

        self.cb_todo.stateChanged.connect(lambda: self.show_tasks('t'))  # для показа задач в окне "+"
        self.cb_diary.stateChanged.connect(lambda: self.show_tasks('d'))
        self.show_all_tasks.stateChanged.connect(lambda: self.show_tasks('d22'))
        self.cb_schedule.stateChanged.connect(lambda: self.show_tasks('sch'))
        self.calendarWidget.clicked.connect(lambda: self.show_tasks('sch'))
        self.calendarWidget_2.clicked.connect(lambda: self.show_tasks('sch2'))

        self.delbtn_todo.clicked.connect(lambda: self.delete_tasks('t'))  # для удаления задач
        self.delbtn_todo_2.clicked.connect(lambda: self.delete_tasks('t2'))
        self.delbtn_diary.clicked.connect(lambda: self.delete_tasks('d'))
        self.delbtn_diary_2.clicked.connect(lambda: self.delete_tasks('d2'))
        self.delbtn_schedule.clicked.connect(lambda: self.delete_tasks('sch'))
        self.delbtn_schedule_2.clicked.connect(lambda: self.delete_tasks('sch2'))

        self.complete_todo.clicked.connect(lambda: self.complete('t'))  # для выполнения задач
        self.complete_diary.clicked.connect(lambda: self.complete('d'))
        self.cancel_diary.clicked.connect(lambda: self.complete('d22'))  # отмена выполнения в ежедневнике
        self.complete_schedule.clicked.connect(lambda: self.complete('sch'))

        self.changebtn_todo.clicked.connect(  # для изменения задач
            lambda: self.redo('t', self.tasks_todo.currentItem().text())
            if self.tasks_todo.currentItem() is not None
            else QMessageBox.warning(self, 'Изменение', 'Задача не выбрана!'))
        self.changebtn_diary.clicked.connect(
            lambda: self.redo('d', self.tasks_diary.currentItem().text())
            if self.tasks_diary.currentItem() is not None
            else QMessageBox.warning(self, 'Изменение', 'Задача не выбрана!'))
        self.changebtn_schedule.clicked.connect(
            lambda: self.redo('sch', self.tasks_schedule.currentItem().text())
            if self.tasks_schedule.currentItem() is not None
            else QMessageBox.warning(self, 'Изменение', 'Задача не выбрана!'))

        self.exist_tasks_todo.itemClicked.connect(lambda: self.show_crits('t'))  # для регистрации нажатий по листам
        self.tasks_todo.itemClicked.connect(lambda: self.show_crits('t2'))
        self.exist_tasks_diary.itemClicked.connect(lambda: self.show_crits('d'))
        self.tasks_diary.itemClicked.connect(lambda: self.show_crits('d2'))
        self.exist_tasks_schedule.itemClicked.connect(lambda: self.show_crits('sch'))
        self.tasks_schedule.itemClicked.connect(lambda: self.show_crits('sch2'))

        # --------------------------Графики---------------------------------------

       # self.current_graph = self.make_graph(self.general, 0, 90, 487, 348)

    # =========================== ФУНКЦИИ ==========================================

    def open(self, window):  # открывает вкладки
        for wind in self.windows:
            wind.hide()

        for crit in self.crits:
            crit.hide()

        self.cb_todo.setChecked(False)
        self.cb_schedule.setChecked(False)
        self.cb_diary.setChecked(False)
        self.show_all_tasks.setChecked(False)

        self.exist_tasks_todo.clear()
        self.exist_tasks_diary.clear()
        self.exist_tasks_schedule.clear()

        self.todo_plus.hide()
        self.diary_plus.hide()
        self.schedule_plus.hide()

        self.crits_todo.clear()
        self.days_diary.clear()
        self.crits_schedule.clear()

        match window:
            case 'g':
                self.general.show()
                self.today_list.clear()
                self.today_list.addItem('\n\n')
                diary_tasks = self.cur.execute("""SELECT name, date_of_complete, days_of_week FROM diary""").fetchall()
                schedule_tasks = self.cur.execute("""SELECT name, date FROM schedule """).fetchall()
                for task in schedule_tasks:  # задачи из планировщика
                    # проверяем на то, что сегодня -- тот день, в которую должна высвечиваться задача
                    if self.todays == QDate.fromString(task[1], 'dd-MM-yyyy'):
                        t = QListWidgetItem(task[0])
                        font = t.font()
                        font.setPointSize(12)  # размер в пунктах
                        font.setBold(True)  # полужирный
                        t.setFont(font)
                        self.today_list.addItem(t)

                for task in diary_tasks:  # задачи из ежедневника
                    # проверяем на то, что сегодня -- тот день недели, в которую должна высвечиваться задача
                    if self.today_weekday in task[2] and task[1] != self.todays:
                        self.today_list.addItem(task[0])

            case 't':
                self.todo.show()
                crits_db = self.cur.execute('SELECT name FROM criterions')

                self.tasks_criterions_todo.clear()
                for i, crit in zip(crits_db, self.crits):
                    self.tasks_criterions_todo.addItem(i[0])
                    crit.show()
                    self.tasks_criterions_todo.addItem('\n')
            case 't2':
                self.todo_2.show()
                self.show_tasks('t2')
            case 'd':
                self.diary.show()
                self.show_tasks('d')
            case 'd2':
                self.diary_2.show()
                self.show_tasks('d2')
            case 'sch':
                self.schedule.show()
                crits_db = self.cur.execute('SELECT name FROM criterions')
                self.tasks_criterions_schedule.clear()
                for line, crit in zip(crits_db, self.crits):
                    self.tasks_criterions_schedule.addItem(line[0])
                    crit.show()
                    self.tasks_criterions_schedule.addItem('\n')
            case 'sch2':
                self.schedule_2.show()
                self.show_tasks('sch2')
            case 'r':
                self.results.show()
            case 'se':
                self.settings.show()
            case 'p':
                self.general.show()
                self.todo_plus.show()
                self.diary_plus.show()
                self.schedule_plus.show()

    # -----------------------------Функции для добавления задач----------------------

    def todo_add(self):
        """Добавить задачу в задачник"""
        if not self.name_todo.text():
            QMessageBox.warning(self, 'Ошибка ввода', "У задачи нет имени!")
            return

        try:
            fnum = int(self.criterion1.text().strip() or 0)
            snum = int(self.criterion2.text().strip() or 0)
            tnum = int(self.criterion3.text().strip() or 0)
            frnum = int(self.criterion4.text().strip() or 0)
            fvnum = int(self.criterion5.text().strip() or 0)

            if not all(not x or str(x).isdigit() for x in [fnum, snum, tnum, frnum, fvnum]):
                QMessageBox.warning(self, 'Ошибка ввода', 'В вводе критериев обнаружены не-цифры!')
                return

            if any(x for x in [fnum, snum, tnum, frnum, fvnum] if 0 > x or x > 5):
                QMessageBox.warning(self, 'Ошибка ввода', 'В критерии нужно вводить цифры в промежутке от 1 до 5!')
                return

            self.cur.execute("""INSERT INTO todo(name, crit1, crit2, crit3, crit4, crit5)
                                VALUES(?, ?, ?, ?, ?, ?)""", (self.name_todo.text(), fnum, snum, tnum, frnum,
                                                              fvnum))
            self.con.commit()
            self.name_todo.clear()
            for crit in self.crits:
                crit.clear()

        except sqlite3.IntegrityError:
            answer = QMessageBox.question(self, 'Добавление', f'Задача с именем {self.name_todo.text()} уже существует.'
                                                     f' Вы хотите переписать её?', QMessageBox.StandardButton.Yes |
                                QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            self.cur.execute("""UPDATE todo SET crit1 = ?, crit2 = ?, crit3 = ?, crit4 = ?, crit5 = ?
                                    WHERE name = ?""",
                             (fnum, snum, tnum, frnum, fvnum, self.name_todo.text()))
            self.con.commit()

            self.name_todo.clear()
            for crit in self.crits:
                crit.clear()

    def diary_add(self):
        """Добавить задачу в ежедневник"""
        if not self.name_diary.text():
            QMessageBox.warning(self, 'Ошибка ввода', "У задачи нет имени!")
            return

        if not any(x for x in self.days if x.isChecked()):
            QMessageBox.warning(self, 'Ошибка ввода', "Выберите хоть один день!")
            return
        try:
            days_active = ''.join(['1' if self.monday.isChecked() else '', '2' if self.tuesday.isChecked() else '',
                    '3' if self.wednesday.isChecked() else '', '4' if self.thursday.isChecked() else '',
                    '5' if self.friday.isChecked() else '', '6' if self.saturday.isChecked() else '',
                    '7' if self.sunday.isChecked() else ''])  # проверяем, в какие дни активна задача

            self.cur.execute("""INSERT INTO diary(name, days_of_week) VALUES(?, ?)""",
                             (self.name_diary.text(), days_active))

            self.con.commit()

        except sqlite3.IntegrityError:
            answer = QMessageBox.question(self, 'Добавление', f'Задача с именем {self.name_diary.text()} уже существует.'
                                                     f' Вы хотите переписать её?', QMessageBox.StandardButton.Yes |
                                QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            self.cur.execute("""UPDATE diary SET days_of_week = ? WHERE name = ?""",
                             (days_active, self.name_diary.text()))
            self.con.commit()

        self.name_diary.clear()
        for i in self.days:
            i.setChecked(False)

    def schedule_add(self):
        """Добавить задачу в планировщк"""
        fnum = int(self.criterion1.text().strip() or 0)
        snum = int(self.criterion2.text().strip() or 0)
        tnum = int(self.criterion3.text().strip() or 0)
        frnum = int(self.criterion4.text().strip() or 0)
        fvnum = int(self.criterion5.text().strip() or 0)

        if any(x for x in [fnum, snum, tnum, frnum, fvnum] if 0 > x or x > 5):
            QMessageBox.warning(self, 'Ошибка ввода', 'Критерии нужно вводить в промежутке от 1 до 5!')
            return

        if not all(not x or str(x).isdigit() for x in [fnum, snum, tnum, frnum, fvnum]):
            QMessageBox.warning(self, 'Ошибка ввода', 'В вводе критериев обнаружены не-цифры!')
            return

        if not self.name_schedule.text():
            QMessageBox.warning(self, 'Ошибка ввода', 'Имя не введено!')
            return

        if not self.calendarWidget.selectedDate():
            QMessageBox.warning(self, 'Ошибка ввода', 'Выберите дату для задачи!')
            return

        try:
            date = self.calendarWidget.selectedDate().toString('dd-MM-yyyy')
            time = self.timeEdit.time().toString('HH:mm')
            if self.todays > self.calendarWidget.selectedDate():  # проверяем, назначается задача ли в прошлое
                reply = QMessageBox.question(self, 'Добавление', 'Задача назначается в прошлое. '
                                                                 'За её выполнение дастся только половина'
                                                                 ' от изначальной суммы баллов. Назначить всё равно?',
                                             QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return

            self.cur.execute("""INSERT INTO schedule(name, date, time, crit1, crit2, crit3, crit4, crit5)
                                VALUES(?, ?, ?, ?, ?, ?, ?, ?)""", (self.name_schedule.text(), date, time,
                                                                    fnum, snum, tnum, frnum, fvnum))

            self.con.commit()

        except sqlite3.IntegrityError:
            answer = QMessageBox.question(self, 'Добавление', f'Задача с именем {self.name_schedule.text()} уже существует.'
                                                     f' Вы хотите переписать её?', QMessageBox.StandardButton.Yes |
                                QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return

            self.cur.execute("""UPDATE schedule SET date = ?, time = ?, 
                                    crit1 = ?, crit2 = ?, crit3 = ?, crit4 = ?, crit5 = ? WHERE name = ?""",
                             (date, time, fnum, snum, tnum, frnum, fvnum, self.name_diary.text()))
            self.con.commit()

        self.name_schedule.clear()
        for crit in self.crits:
            crit.clear()
        self.timeEdit.setTime(QTime(0, 0))

    # ------------------------------Работа с задачами----------------------------------------------------

    def show_tasks(self, tool_type):
        """Показать уже существующие задачи"""
        if 't' in tool_type:  # если выбран задачник
            rdr_todo = self.cur.execute('''SELECT name FROM todo''').fetchall()

            if tool_type == 't':
                if self.cb_todo.isChecked():
                    self.exist_tasks_todo.clear()
                    for task in rdr_todo:
                        self.exist_tasks_todo.addItem(*task)
                else:
                    for crit in self.crits:
                        crit.setText('')
                    self.name_todo.setText('')
                    self.exist_tasks_todo.clear()

            elif tool_type == 't2':
                self.tasks_todo.clear()
                for task in rdr_todo:
                    self.tasks_todo.addItem(*task)

        elif 'd' in tool_type:  # если выбран ежедневник
            rdr_diary = self.cur.execute('''SELECT name, date_of_complete, days_of_week FROM diary''').fetchall()

            if tool_type == 'd':  # если это "+"
                if self.cb_diary.isChecked():
                    self.exist_tasks_diary.clear()
                    for task in rdr_diary:
                        self.exist_tasks_diary.addItem(task[0])
                else:
                    self.exist_tasks_diary.clear()

            elif tool_type == 'd2':  # если это обычное окно
                self.tasks_diary.clear()
                for task in rdr_diary:
                    if (task[1] == self.todays.toString('dd-MM-yyyy')  # проверяем, что эта задача на сегодня и она
                            and str(QDate.currentDate().dayOfWeek()) in task[2:]):  # выполнена
                        item = QListWidgetItem(task[0])
                        item.setForeground(QBrush(QColor("gray")))
                        font = item.font()
                        font.setPointSize(7)  # размер шрифта
                        item.setFont(font)

                        self.tasks_diary.addItem(item)
                    elif self.today_weekday in task[2:]:

                        self.tasks_diary.addItem(task[0])

            elif tool_type == 'd22':  # показать все задачи в основном окне
                self.tasks_diary.clear()
                if self.show_all_tasks.isChecked():
                    for task in rdr_diary:
                        if task[1] == self.todays or self.today_weekday not in task[2:]:
                            item = QListWidgetItem(task[0])
                            item.setForeground(QBrush(QColor("gray")))

                            font = item.font()
                            font.setPointSize(7)  # размер шрифта
                            item.setFont(font)

                            self.tasks_diary.addItem(item)
                        else:
                            self.tasks_diary.addItem(task[0])

                else:
                    self.tasks_diary.clear()
                    for task in rdr_diary:
                        if task[1] == self.todays and self.today_weekday in task[2:]:
                            item = QListWidgetItem(task[0])
                            item.setForeground(QBrush(QColor("gray")))

                            font = item.font()
                            font.setPointSize(7)  # размер шрифта
                            item.setFont(font)

                            self.tasks_diary.addItem(item)
                        elif self.today_weekday in task[2:]:
                            self.tasks_diary.addItem(task[0])

        elif 'sch' in tool_type:  # если это планировщик
            rdr_schedule = self.cur.execute('''SELECT name, time, date FROM schedule''').fetchall()

            if tool_type == 'sch':  # если это окно "+"
                if self.cb_schedule.isChecked():
                    self.exist_tasks_schedule.clear()
                    for task in rdr_schedule:
                        self.exist_tasks_schedule.addItem(task[0])
                else:
                    for crit in self.crits:
                        crit.setText('')
                    self.name_schedule.setText('')
                    self.exist_tasks_schedule.clear()

            elif tool_type == 'sch2':  # если это обычное окно
                self.tasks_schedule.clear()
                selected = self.calendarWidget_2.selectedDate()
                for task in rdr_schedule:
                    if QDate.fromString(task[2], 'dd-MM-yyyy') == selected:
                        self.tasks_schedule.addItem(f'{task[0]}\n{task[1]}')

    def show_crits(self, tool_type: str):
        """Показывает критерии (для задачника и планировщика) и дни (для ежедневника)"""
        if 't' in tool_type:
            task_name = self.exist_tasks_todo.currentItem().text() if 't' == tool_type \
                else self.tasks_todo.currentItem().text()  # берём имя задачи
            tasks_crits = self.cur.execute("""SELECT crit1, crit2, crit3, crit4, crit5 FROM todo WHERE name = ?""",
                                           (task_name,)).fetchone()
            if tool_type == 't':
                name = self.cur.execute("""SELECT name FROM todo WHERE name = ?""",
                                        (task_name,)).fetchone()
                self.name_todo.setText(*name)
                for crit, num in zip(self.crits, tasks_crits):
                    crit.setText(str(num))

            if tool_type == 't2':
                criterions = self.cur.execute("SELECT name FROM criterions").fetchall()
                self.crits_todo.clear()
                for i, num in zip(criterions, tasks_crits):
                    self.crits_todo.addItem(f'{i[0]}:\n   {num}')

        elif 'd' in tool_type:
            task_name = self.exist_tasks_diary.currentItem().text() if 'd' == tool_type \
                else self.tasks_diary.currentItem().text() # берём имя задачи
            days_active = ''.join(self.cur.execute("""SELECT days_of_week FROM diary WHERE name = ?""",
                                           (task_name,)).fetchone())
            if tool_type == 'd':
                for day in self.days:
                    day.setChecked(False)
                self.name_diary.setText(task_name)

                if '1' in days_active:
                    self.monday.setChecked(True)
                if '2' in days_active:
                    self.tuesday.setChecked(True)
                if '3' in days_active:
                    self.wednesday.setChecked(True)
                if '4' in days_active:
                    self.thursday.setChecked(True)
                if '5' in days_active:
                    self.friday.setChecked(True)
                if '6' in days_active:
                    self.saturday.setChecked(True)
                if '7' in days_active:
                    self.sunday.setChecked(True)

            elif tool_type == 'd2':
                self.days_diary.clear()
                if '1' in days_active:
                    self.days_diary.addItem('Понедельник')
                if '2' in days_active:
                    self.days_diary.addItem('Вторник')
                if '3' in days_active:
                    self.days_diary.addItem('Среда')
                if '4' in days_active:
                    self.days_diary.addItem('Четверг')
                if '5' in days_active:
                    self.days_diary.addItem('Пятница')
                if '6' in days_active:
                    self.days_diary.addItem('Суббота')
                if '7' in days_active:
                    self.days_diary.addItem('Воскресенье')

        if 'sch' in tool_type:
            task_name = self.exist_tasks_schedule.currentItem().text().split()[0] if 'sch' == tool_type \
                else self.tasks_schedule.currentItem().text().split()[0]  # берём только имя задачи (без времени)
            tasks_crits = self.cur.execute("""SELECT crit1, crit2, crit3, crit4, crit5 FROM schedule
                                                WHERE name = ?""", (task_name,)).fetchone()  # берём значения
                                                                                                    # всех критериев
            if tool_type == 'sch':
                self.name_schedule.setText(task_name)
                for crit, num in zip(self.crits, tasks_crits):
                    crit.setText(str(num))

            if tool_type == 'sch2':
                criterions = self.cur.execute("SELECT name FROM criterions").fetchall()

                self.crits_schedule.clear()
                for i, num in zip(criterions, tasks_crits):
                    self.crits_schedule.addItem(f'{i[0]}:\n   {num}')

    def delete_tasks(self, tool_type):
        """Удалить уже существующие задачи"""
        if 't' in tool_type:
            task_name = self.exist_tasks_todo.currentItem() if tool_type == 't'\
                else self.tasks_todo.currentItem()
            if task_name is None:
                QMessageBox.warning(self, 'Удаление', 'Задача не выбрана!')
                return
            reply = QMessageBox.question(self, 'Удаление',
                                         f'Вы точно хотите удалить задачу {task_name.text()}?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
            self.cur.execute("""DELETE FROM todo WHERE name = ?""", (task_name.text(),))
            self.con.commit()

            if tool_type == 't':
                self.name_todo.clear()
                for crit in self.crits:
                    crit.clear()
                self.show_tasks('t')
            elif tool_type == 't2':
                self.crits_todo.clear()
                self.show_tasks('t2')

        elif 'd' in tool_type:
            task_name = self.exist_tasks_diary.currentItem() if tool_type == 'd'\
                else self.tasks_diary.currentItem()
            if task_name is None:
                QMessageBox.warning(self, 'Удаление', 'Задача не выбрана!')
                return
            reply = QMessageBox.question(self, 'Удаление', f'Вы точно хотите удалить задачу {task_name.text()}?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return

            self.cur.execute("""DELETE FROM diary WHERE name = ?""", (task_name.text(),))
            self.con.commit()

            if tool_type == 'd':
                for i in self.days:
                    i.setChecked(False)
                self.show_tasks('d')
            elif tool_type == 'd2':
                self.days_diary.clear()
                self.show_tasks('d2')

        if 'sch' in tool_type:
            item_schedule = self.exist_tasks_schedule.currentItem() if tool_type == 'sch'\
                else self.tasks_schedule.currentItem()
            if item_schedule is None:
                QMessageBox.warning(self, 'Удаление', 'Задача не выбрана!')
                return

            task_name = ' '.join(item_schedule.split('\n')[:-1]).strip()

            reply = QMessageBox.question(self, 'Удаление', f'Вы точно хотите удалить задачу {task_name.text()}?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return

            self.cur.execute("""DELETE FROM diary WHERE name = ?""", (task_name.text(),))
            self.con.commit()

            if tool_type == 'sch':
                self.name_todo.clear()
                for crit in self.crits:
                    crit.clear()
                self.show_tasks('sch')
            elif tool_type == 'sch2':
                self.crits_schedule.clear()
                self.show_tasks('sch2')

    def redo(self, tool_type, task):
        """изменяет задачу, направляя пользователя во вкладку "+" соответствующего инструмента"""
        if task is None:
            QMessageBox.warning(self, 'Изменение', 'Задача не выбрана!')
            return

        if 't' in tool_type:
            self.open('t')
            self.name_todo.setText(task)

            rdr = self.cur.execute("""SELECT name, crit1, crit2, crit3, crit4, crit5 FROM todo
                                    WHERE name = ?""", (task,)).fetchone()
            for crit, num in zip(self.crits, rdr[1:]):
                crit.setText(str(num))

        elif 'd' in tool_type:
            self.open('d')
            self.name_diary.setText(task)

            rdr = self.cur.execute('''SELECT name, days_of_week FROM diary WHERE name = ?''', (task,)).fetchall()

            if '1' in rdr[1]:
                self.monday.setChecked(True)
            if '2' in rdr[1]:
                self.tuesday.setChecked(True)
            if '3' in rdr[1]:
                self.wednesday.setChecked(True)
            if '4' in rdr[1]:
                self.thursday.setChecked(True)
            if '5' in rdr[1]:
                self.friday.setChecked(True)
            if '6' in rdr[1]:
                self.saturday.setChecked(True)
            if '7' in rdr[1]:
                self.sunday.setChecked(True)

        elif 'sch' in tool_type:
            self.open('sch')
            n_task = task.split('\n')[0]  # имя задачи
            self.name_schedule.setText(n_task)
            rdr = self.cur.execute("""SELECT name, date, time, crit1, crit2, crit3, crit4, crit5 FROM schedule
                                             WHERE name = ?""", (n_task,)).fetchone()
            self.calendarWidget.setSelectedDate(QDate.fromString(rdr[1], 'dd-MM-yyyy'))
            self.timeEdit.setTime(QTime.fromString(rdr[2], 'HH:mm'))

            for crit, num in zip(self.crits, rdr[3:]):
                crit.setText(str(num))

    def complete(self, tool_type):
        if tool_type == 't':  # если это задачник
            item = self.tasks_todo.currentItem()
            if item is None:
                QMessageBox.warning(self, 'Выполнение', 'Задача не выбрана!')
                return
            header_res, rdr_res = self.read_file('graph1.csv')
            header_todo, rdr_todo = self.todo_file[0], self.todo_file[1:]

            task = [x for x in rdr_todo if x and x[0] == item.text()]

            summa = sum(int(n) for n in task[0][1:] if n)
            QMessageBox.information(self, 'Выполнение', f"Задача {task[0][0]} выполнена! Начислено: {summa}")
            new_rows = [row for row in rdr_todo if row[0] != item.text()]

            updated_res = []  # обновление graph1
            today = False
            for row in rdr_res:
                if row[0] == QDate.toString(self.todays, 'dd-MM-yyyy'):
                    updated_res.append([row[0], str(int(row[1]) + summa)])
                    today = True
                else:
                    updated_res.append(row)
            if not today:
                updated_res.append([self.qtoday, str(summa)])

            self.write_file('graph1.csv', header_res, updated_res)  # пишем файл для первого графика
            self.write_file('todo.csv', header_todo, new_rows)  # пишем файл для задачника

            self.show_tasks('t2')
            self.show_crits('t2')
            self.current_graph = self.make_graph(self.general, 0, 90, 487, 348)

        elif tool_type == 'd':  # если это ежедневник
            item = self.tasks_diary.currentItem()
            if item is None:
                QMessageBox.warning(self, 'Выполнение', 'Задача не выбрана!')
                return
            header, rdr = self.diary_file[0], self.diary_file[1:]

            updated_row = [x for x in rdr if x and x[0] == item.text()]
            last_rows = [x for x in rdr if x and x[0] != item.text()]  # предыдущие строки, чтобы они не утерялись
            updated_row[0][1] = self.qtoday
            last_rows.append(*updated_row)  # перемещаем выполненную задачу в конец
            self.write_file('diary.csv', header, last_rows)

            self.show_tasks('d2')
            self.show_all_tasks.setChecked(False)

        elif tool_type == 'd22':  # если надо отменить выполнение задачи из ежедневника
            item = self.tasks_diary.currentItem()
            if item is None:
                QMessageBox.warning(self, 'Выполнение', 'Задача не выбрана!')
                return

            header, rdr = self.diary_file[0], self.diary_file[1:]
            updated_task = [x for x in rdr if x and x[0] == item.text()]  # задача, которую нужно обновить
            updated_task[0][1] = ''
            last_rows = [x for x in rdr if x and x[0] != item.text()]  # предыдущие строки, чтобы они не утерялись

            last_rows.append(*updated_task)
            self.write_file('diary.csv', header, last_rows)
            self.show_tasks('d2')
            self.show_all_tasks.setChecked(False)

        elif tool_type == 'sch':  # если это планировщик
            item = self.tasks_schedule.currentItem()
            if item is None:
                QMessageBox.warning(self, 'Выполнение', 'Задача не выбрана!')
                return
            header_res, rdr_res = self.read_file('graph1.csv')
            header_schedule, rdr_schedule = self.schedule_file[0], self.schedule_file[1:]
            item_name = ' '.join(item.text().split('\n')[:-1])
            task = [x for x in rdr_schedule if x and x[0] == item_name]

            if self.todays <= QDate.fromString(task[0][1], 'dd-MM-yyyy'):
                summa = sum(int(n) for n in task[0][3:] if n)
                QMessageBox.information(self, 'Выполнение', f"Задача {task[0][0]} выполнена! Начислено: {summa}")
            else:
                summa = sum(int(n) for n in task[0][3:] if n) // 2
                QMessageBox.information(self, 'Выполнение', f'У задачи истёк дедлайн, поэтому '
                                                            f'за её выполнение вы получили в два раза меньше суммы баллов:'
                                                            f' {summa}')

            new_rows = [row for row in rdr_schedule if row[0] != item_name]

            updated_res = []  # обновление graph1
            today = False
            for row in rdr_res:
                if row[0] == self.qtoday:
                    updated_res.append([row[0], str(int(row[1]) + summa)])
                    today = True
                else:
                    updated_res.append(row)
            if not today:
                updated_res.append([self.qtoday, str(summa)])

            self.write_file('graph1.csv', header_res, updated_res)  # пишем файл для первого графика
            self.write_file('schedule.csv', header_schedule, new_rows)  # пишем файл для задачника

            self.show_tasks('sch2')
            self.crits_schedule.clear()
            self.current_graph = self.make_graph(self.general, 0, 90, 487, 348)

    # ----------------------------Графики--------------------------------------

    #def load_graph(self):
        #"""Достаёт данные для графиков"""
        #rdr = self.read_file('results')
        #points = []
        #for row in rdr:
        #    date = QDate.fromString(row[0], 'dd-MM-yyyy')  # берём дату
        #    val = int(row[1])  # баллы за дату
         #   points.append((date, val))
        #return points

    #def draw_graph(self, figure):
       # """Отрисовка данных"""
        #figure.clear()
        #ax = figure.add_subplot(111)
       # points = self.load_graph()
       # dates = [d.toString('dd-MM') for d, _ in points]  # даты
       # values = [v for _, v in points]  # баллы
       # ax.plot(dates, values, marker='o', linewidth=2, color='steelblue')
       # ax.fill_between(range(len(values)), values, alpha=0.15, color='steelblue')
       # ax.set_title('Успеваемость по дням', fontsize=10)
        #ax.set_ylabel('Баллы', fontsize=9)
       # ax.grid(True, alpha=0.3)
      #  ax.tick_params(axis='x', rotation=45, labelsize=7)
        #ax.tick_params(axis='y', labelsize=7)
        #figure.tight_layout()

    #def make_graph(self, parent, x, y, w, h):
        #"""Создать график"""
       # fig = Figure(figsize=(w // 100, h // 100), dpi=100)
        #canvas = FigureCanvas(fig)
        #canvas.setParent(parent)
        #canvas.move(x, y)
        #canvas.resize(w, h)
        #canvas.raise_()
       # self.draw_graph(fig)
       # canvas.draw()
        #return canvas


if __name__ == '__main__':
    app = QApplication(argv)
    om = OmniTracker()

    nr = om.cur.execute('SELECT quote FROM phylosophy ORDER BY random() LIMIT 1').fetchone()
    r = ''.join(nr) if nr else ''
    om.phylosophy_browser.setHtml(f'<div style="text-align: center;"><h1>{r}</h1></div>')

    om.open('g')
    om.show()
    exit(app.exec())
