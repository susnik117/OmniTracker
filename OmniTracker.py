from sys import argv, exit
from io import StringIO
from PyQt6.QtWidgets import QMainWindow, QListWidgetItem, QApplication, QMessageBox
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import QTime, QDate, Qt
from PyQt6 import uic
import sqlite3
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


# TODO: сделать так, чтобы если в планировщике в каком-либо дне есть задачи, то этот день будет окрашиваться в
#  выбранный пользователем цвет

# TODO: поправить дизайн (исправить графическую ошибку с расположением виджетов)

# TODO: расширить настройки: добавить возможность стирать информацию о днях в графике и экспортировать/импортировать
#  данные с графиков

# TODO: сделать так, чтобы можно было отключить рандомизацию цитат

# TODO: сделать так, чтобы дни у ежедневника съехали туда, где у двух других инструментов критерии

# TODO: добавить возможность добавления описания


class OmniTracker(QMainWindow):
    """Класс, выполняющий функционал приложения"""

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
        self.week_offset = 0  # для выбора недели в графиках
        self.is_plus_ready = False
        self.con = sqlite3.connect('tasks.sql')
        self.cur = self.con.cursor()  # курсор
        self.current_settings = self.cur.execute('SELECT * FROM settings').fetchone()
        self.ctrl_c_task = tuple()
        self.todo_plus.hide()
        self.diary_plus.hide()
        self.schedule_plus.hide()

        self.windows = [self.general, self.todo, self.todo_2, self.diary, self.diary_2, self.schedule, self.schedule_2,
                        self.settings, self.settings_crits, self.settings_quotes]
        # все окна в один лист, чтобы можно было легко их открывать/перемещать

        self.days = [self.monday, self.tuesday, self.wednesday, self.thursday, self.friday, self.saturday, self.sunday]
        # все дни из ежедневника в один лист

        for wind in self.windows:
            wind.move(0, 0)

        self.crits = [self.criterion1, self.criterion2, self.criterion3, self.criterion4, self.criterion5]  # список
        # всех полей для критериев

        for i, crit in enumerate(self.crits):
            crit.hide()

        # -------------Привязка меню---------------
        self.menu.aboutToShow.connect(lambda: self.menu_clicked('g'))
        self.menu_2.aboutToShow.connect(lambda: self.menu_clicked('t2'))
        self.menu_3.aboutToShow.connect(lambda: self.menu_clicked('d2'))
        self.menu_4.aboutToShow.connect(lambda: self.menu_clicked('sch2'))
        self.menu_5.aboutToShow.connect(lambda: self.menu_clicked('se'))

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

        self.confirm_settings.clicked.connect(self.update_settings)  # настройки
        self.redact_crits_btn.clicked.connect(lambda: self.open('se2'))
        self.add_crit_btn.clicked.connect(self.add_or_redo_crit)
        self.clear_crits.clicked.connect(lambda: self.fill_or_defill_lineedits_settings(0, 1))
        self.del_crit_btn.clicked.connect(self.del_crit)
        self.redact_quotes_btn.clicked.connect(lambda: self.open('se3'))
        self.add_quote_btn.clicked.connect(self.add_or_redo_quote)
        self.del_quote_btn.clicked.connect(self.del_quote)
        self.clear_quotes.clicked.connect(lambda: self.fill_or_defill_lineedits_settings(0, 0))

        self.exist_tasks_todo.itemClicked.connect(lambda: self.show_crits('t'))  # для регистрации нажатий по листам
        self.tasks_todo.itemClicked.connect(lambda: self.show_crits('t2'))
        self.exist_tasks_diary.itemClicked.connect(lambda: self.show_crits('d'))
        self.tasks_diary.itemClicked.connect(lambda: self.show_crits('d2'))
        self.exist_tasks_schedule.itemClicked.connect(lambda: self.show_crits('sch'))
        self.tasks_schedule.itemClicked.connect(lambda: self.show_crits('sch2'))
        self.criterions_redact.itemClicked.connect(lambda: self.fill_or_defill_lineedits_settings(1, 1))
        self.quotes_redact.itemClicked.connect(lambda: self.fill_or_defill_lineedits_settings(1, 0))
        # --------------------------Графики---------------------------------------

        if self.current_settings[2]:  # проверка на то, что графики включены
            self.current_graph = self.make_graph(self.general, 0, 90, 487, 348)
            self.prev_week_btn.setText('<-')
            self.prev_week_btn.clicked.connect(self.prev_week)
            self.next_week_btn.setText('->')
            self.next_week_btn.clicked.connect(self.next_week)
        else:
            self.prev_week_btn.hide()
            self.next_week_btn.hide()
            self.week_label.hide()

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

        self.status.clear()
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

                if not self.current_settings[1]:  # проверка на то, что цитаты выключены
                    self.phylosophy_browser.hide()
                else:
                    self.phylosophy_browser.show()
            case 't':
                self.todo.show()
                crits_db = self.cur.execute('SELECT name FROM criterions ORDER BY id')

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
                crits_db = self.cur.execute('SELECT name FROM criterions ORDER BY id')
                self.tasks_criterions_schedule.clear()
                for line, crit in zip(crits_db, self.crits):
                    self.tasks_criterions_schedule.addItem(line[0])
                    crit.show()
                    self.tasks_criterions_schedule.addItem('\n')
            case 'sch2':
                self.schedule_2.show()
                self.show_tasks('sch2')
            case 'se':
                self.settings.show()
                self.is_crits_on.setChecked(True) if self.current_settings[0] else self.is_crits_on.setChecked(False)
                self.redact_crits_btn.hide() if not self.is_crits_on.isChecked() else self.redact_crits_btn.show()

                self.is_quotes_on.setChecked(True) if self.current_settings[1] else self.is_quotes_on.setChecked(False)
                self.redact_quotes_btn.hide() if not self.is_quotes_on.isChecked() else self.redact_quotes_btn.show()

                self.is_graph_on.setChecked(True) if self.current_settings[2] else self.is_graph_on.setChecked(False)
            case 'se2':  # редактирование критериев
                self.settings_crits.show()
                self.criterions_redact.clear()
                crits = self.cur.execute("""SELECT * FROM criterions""").fetchall()
                for c in crits:
                    self.criterions_redact.addItem(f'{c[1]} ({c[2]} - {c[3]})')
            case 'se3':
                self.settings_quotes.show()
                self.quotes_redact.clear()
                quotes = self.cur.execute("SELECT * FROM phylosophy").fetchall()
                for i, q in enumerate(quotes):
                    qq = ' '.join(q)
                    self.quotes_redact.addItem(f'{i + 1}. {str(qq)[:23]}...')
            case 'p':
                self.open('g')
                if not self.is_plus_ready:
                    self.todo_plus.show()
                    self.diary_plus.show()
                    self.schedule_plus.show()
                    self.is_plus_ready = True
                else:
                    self.todo_plus.hide()
                    self.diary_plus.hide()
                    self.schedule_plus.hide()
                    self.is_plus_ready = False

    # -----------------------------Функции для добавления задач----------------------

    def todo_add(self):
        """Добавить задачу в задачник"""
        if not self.name_todo.text():
            QMessageBox.warning(self, 'Ошибка ввода', "У задачи нет имени!")
            return

        try:
            if self.current_settings[1]:
                fnum = int(self.criterion1.text().strip() or 0)
                snum = int(self.criterion2.text().strip() or 0)
                tnum = int(self.criterion3.text().strip() or 0)
                frnum = int(self.criterion4.text().strip() or 0)
                fvnum = int(self.criterion5.text().strip() or 0)

                if not all(not x or str(x).isdigit() for x in [fnum, snum, tnum, frnum, fvnum]):
                    QMessageBox.warning(self, 'Ошибка ввода', 'В вводе критериев обнаружены не-цифры!')
                    return

                if all(not x for x in [fnum, snum, tnum, frnum, fvnum]):
                    QMessageBox.warning(self, 'Ошибка ввода',
                                        'Хотя-бы один критерий должен быть равен положительному целому значению!')
                    return

                crits = self.cur.execute("""SELECT min, max FROM criterions ORDER BY id""").fetchall()
                for crit in crits:
                    if any(x for x in [fnum, snum, tnum, frnum, fvnum] if crit[0] > x or x > crit[1]):
                        QMessageBox.warning(self, 'Ошибка ввода',
                                            f'В критерии нужно вводить цифры в промежутке от {crit[0]} до {crit[1]}!')
                        return
                summa = fnum + snum + tnum + frnum + fvnum  # сумма всех баллов
                self.cur.execute("""INSERT INTO todo(name, crit1, crit2, crit3, crit4, crit5, summa)
            VALUES(?, ?, ?, ?, ?, ?, ?)""", (self.name_todo.text(), fnum, snum, tnum, frnum, fvnum, summa))
            else:
                self.cur.execute("""INSERT INTO todo(name) VALUES(?)""", (self.name_todo.text(),))

        except sqlite3.IntegrityError:
            if self.current_settings[2]:
                answer = QMessageBox.question(self, 'Добавление',
                                              f'Задача с именем {self.name_todo.text()} уже существует.'
                                              f' Вы хотите переписать её?',
                                              QMessageBox.StandardButton.Yes |
                                              QMessageBox.StandardButton.No)
                if answer != QMessageBox.StandardButton.Yes:
                    return
                self.cur.execute("""UPDATE todo SET crit1 = ?, crit2 = ?, crit3 = ?, crit4 = ?, crit5 = ?, sum = ?
                            WHERE name = ?""", (fnum, snum, tnum, frnum, fvnum, summa, self.name_todo.text()))
                self.con.commit()
        self.status.setText(f'Задача {self.name_todo.text()} добавлена!')
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
            answer = QMessageBox.question(self, 'Добавление',
                                          f'Задача с именем {self.name_diary.text()} уже существует.'
                                          f' Вы хотите переписать её?', QMessageBox.StandardButton.Yes |
                                          QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            self.cur.execute("""UPDATE diary SET days_of_week = ? WHERE name = ?""",
                             (days_active, self.name_diary.text()))
        self.status.setText(f'Задача {self.name_diary.text()} добавлена!')
        self.con.commit()
        self.name_diary.clear()
        for i in self.days:
            i.setChecked(False)

    def schedule_add(self):
        """Добавить задачу в планировщк"""
        if not self.name_schedule.text():
            QMessageBox.warning(self, 'Ошибка ввода', 'Имя не введено!')
            return

        if not self.calendarWidget.selectedDate():
            QMessageBox.warning(self, 'Ошибка ввода', 'Выберите дату для задачи!')
            return
        try:
            date = self.calendarWidget.selectedDate().toString('dd-MM-yyyy')
            time = self.timeEdit.time().toString('HH:mm')
            if self.current_settings[2]:
                fnum = int(self.criterion1.text().strip() or 0)
                snum = int(self.criterion2.text().strip() or 0)
                tnum = int(self.criterion3.text().strip() or 0)
                frnum = int(self.criterion4.text().strip() or 0)
                fvnum = int(self.criterion5.text().strip() or 0)

                crits = self.cur.execute("""SELECT min, max FROM criterions ORDER BY id""").fetchall()
                for crit in crits:
                    if any(x for x in [fnum, snum, tnum, frnum, fvnum] if crit[0] > x or x > crit[1]):
                        QMessageBox.warning(self, 'Ошибка ввода',
                                            f'В критерии нужно вводить цифры в промежутке от {crit[0]} до {crit[1]}!')
                        return

                if not all(not x or str(x).isdigit() for x in [fnum, snum, tnum, frnum, fvnum]):
                    QMessageBox.warning(self, 'Ошибка ввода', 'В вводе критериев обнаружены не-цифры!')
                    return

                if all(not x for x in [fnum, snum, tnum, frnum, fvnum]):
                    QMessageBox.warning(self, 'Ошибка ввода',
                                        'Хотя-бы один критерий должен быть равен положительному целому значению!')
                    return

                if self.todays > self.calendarWidget.selectedDate():  # проверяем, назначается задача ли в прошлое
                    reply = QMessageBox.question(self, 'Добавление', 'Задача назначается в прошлое. '
                                                                     'За её выполнение дастся только половина от изначальной суммы баллов. Назначить всё равно?',
                                                 QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                    if reply != QMessageBox.StandardButton.Yes:
                        return
                summa = fnum + snum + tnum + frnum + fvnum  # сумма всех баллов
                self.cur.execute("""INSERT INTO schedule(name, date, time, crit1, crit2, crit3, crit4, crit5, summa)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)""", (self.name_schedule.text(), date, time,
                                               fnum, snum, tnum, frnum, fvnum, summa))
            else:

                self.cur.execute("INSERT INTO schedule(name, date, time) VALUES(?, ?, ?)",
                                 (self.name_schedule.text(), date, time,))
        except sqlite3.IntegrityError:
            if self.current_settings[2]:
                answer = QMessageBox.question(self, 'Добавление',
                                              f'Задача с именем {self.name_schedule.text()} уже существует.'
                                              f' Вы хотите переписать её?', QMessageBox.StandardButton.Yes |
                                              QMessageBox.StandardButton.No)
                if answer != QMessageBox.StandardButton.Yes:
                    return
                self.cur.execute("""UPDATE schedule SET date = ?, time = ?, 
                                        crit1 = ?, crit2 = ?, crit3 = ?, crit4 = ?, crit5 = ? WHERE name = ?""",
                                 (date, time, fnum, snum, tnum, frnum, fvnum, self.name_schedule.text()))
        self.con.commit()
        self.status.setText(f'Задача {self.name_schedule.text()} добавлена!')
        self.name_schedule.clear()
        for crit in self.crits:
            crit.clear()
        self.timeEdit.setTime(QTime(0, 0))

    # ------------------------------Показать задачи/критерии----------------------------------------------------

    def show_tasks(self, tool_type):
        """Показать уже существующие задачи с их критериями"""
        if 't' in tool_type:  # если выбран задачник
            rdr_todo = self.cur.execute('''SELECT name, summa FROM todo''').fetchall()

            if tool_type == 't':
                if self.cb_todo.isChecked():
                    self.exist_tasks_todo.clear()
                    for task in rdr_todo:
                        name = ''.join(task[0])
                        summa = ''.join(task[1])
                        self.exist_tasks_todo.addItem(f'{name} ({summa})')
                else:
                    for crit in self.crits:
                        crit.setText('')
                    self.name_todo.setText('')
                    self.exist_tasks_todo.clear()

            elif tool_type == 't2':
                self.tasks_todo.clear()
                for task in rdr_todo:
                    name = ''.join(task[0])
                    summa = ''.join(str(task[1]))
                    self.tasks_todo.addItem(f'{name} ({summa})')

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
                            and str(QDate.currentDate().dayOfWeek()) in task[2]):  # выполнена
                        item = QListWidgetItem(task[0])
                        item.setForeground(QBrush(QColor("gray")))
                        font = item.font()
                        font.setPointSize(7)  # размер шрифта
                        item.setFont(font)

                        self.tasks_diary.addItem(item)
                    elif str(QDate.currentDate().dayOfWeek()) in task[2]:

                        self.tasks_diary.addItem(task[0])

            elif tool_type == 'd22':  # показать все задачи в основном окне
                self.tasks_diary.clear()
                if self.show_all_tasks.isChecked():
                    for task in rdr_diary:
                        if task[1] == self.qtoday or self.today_weekday not in task[2]:
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
                    self.show_tasks('d2')

        elif 'sch' in tool_type:  # если это планировщик
            rdr_schedule = self.cur.execute('''SELECT name, time, date, summa FROM schedule''').fetchall()

            if tool_type == 'sch':  # если это окно "+"
                if self.cb_schedule.isChecked():
                    self.exist_tasks_schedule.clear()
                    for task in rdr_schedule:
                        name = ''.join(task[0])
                        time = ''.join(task[1])
                        summa = ''.join(str(task[3]))
                        self.exist_tasks_schedule.addItem(f'{name} ({summa})\n  {time}')

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
                        name = ''.join(task[0])
                        time = ''.join(task[1])
                        summa = ''.join(str(task[3]))
                        self.tasks_schedule.addItem(f'{name} ({summa})\n{time}')

    def show_crits(self, tool_type: str):
        """Показывает критерии (для задачника и планировщика) и дни (для ежедневника)"""
        if 'd' in tool_type:
            if not (self.exist_tasks_diary.currentItem() or (self.tasks_diary.currentItem())):
                return
            task_name = self.exist_tasks_diary.currentItem().text() if 'd' == tool_type \
                else self.tasks_diary.currentItem().text()  # берём имя задачи
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

        if self.current_settings[2]:
            if 't' in tool_type:
                if not (self.exist_tasks_todo.currentItem() or (self.tasks_todo.currentItem())):
                    for i in self.crits:
                        i.clear()
                    self.crits_todo.clear()
                    return
                task_name = ''.join(self.exist_tasks_todo.currentItem().text().split()[:-1]) if 't' == tool_type \
                    else ''.join(self.tasks_todo.currentItem().text().split()[:-1])  # берём имя задачи
                tasks_crits = self.cur.execute(
                    """SELECT crit1, crit2, crit3, crit4, crit5 FROM todo WHERE name = ?""", (task_name,)).fetchone()
                if tool_type == 't':
                    name = self.cur.execute("""SELECT name FROM todo WHERE name = ?""",
                                            (task_name,)).fetchone()
                    self.name_todo.setText(*name)
                    for crit, num in zip(self.crits, tasks_crits):
                        crit.setText(str(num))

                if tool_type == 't2':
                    criterions = self.cur.execute("SELECT name FROM criterions ORDER BY id").fetchall()
                    summa = str(*(self.cur.execute("SELECT summa FROM todo WHERE name = ?",
                                                   (task_name,))).fetchone())
                    self.crits_todo.clear()
                    for i, num in zip(criterions, tasks_crits):
                        self.crits_todo.addItem(f'{i[0]}:\n   {num}')
                    self.crits_todo.addItem(f'Суммарно:\n   {summa}')

            if 'sch' in tool_type:
                if not (self.exist_tasks_schedule.currentItem() or (self.tasks_schedule.currentItem())):
                    for i in self.crits:
                        i.clear()
                    self.crits_schedule.clear()
                    return
                # берём только имя задачи
                task_name = ' '.join(self.exist_tasks_schedule.currentItem().text().split()[:-2]) if 'sch' == tool_type \
                    else ' '.join(self.tasks_schedule.currentItem().text().split()[:-2])
                date_time = self.cur.execute("""SELECT date, time FROM schedule WHERE name = ?""",
                                             (task_name,)).fetchone()
                # берём значения всех критериев
                tasks_crits = self.cur.execute("""SELECT crit1, crit2, crit3, crit4, crit5 FROM schedule
                                            WHERE name = ?""", (task_name,)).fetchone()
                if tool_type == 'sch':
                    # ставим день выбранной задачи
                    self.calendarWidget.setSelectedDate(QDate.fromString(date_time[0], 'dd-MM-yyyy'))
                    self.name_schedule.setText(task_name)  # имя
                    self.timeEdit.setTime(QTime.fromString(date_time[1], 'HH:mm'))  # и время
                    for crit, num in zip(self.crits, tasks_crits):
                        crit.setText(str(num))

                if tool_type == 'sch2':
                    criterions = self.cur.execute("SELECT name FROM criterions ORDER BY id").fetchall()
                    summa = str(*(self.cur.execute("SELECT summa FROM schedule "
                                                   "WHERE name = ?", (task_name,)).fetchone()))
                    self.crits_schedule.clear()
                    for i, num in zip(criterions, tasks_crits):
                        self.crits_schedule.addItem(f'{i[0]}:\n   {num}')
                    self.crits_schedule.addItem(f'Суммарно:\n   {summa}')

    # ---------------------------------------Работа с задачами---------------------------------------

    def delete_tasks(self, tool_type):
        """Удалить уже существующие задачи"""
        if 't' in tool_type:
            task = self.exist_tasks_todo.currentItem() if tool_type == 't' \
                else self.tasks_todo.currentItem()
            if task is None:
                QMessageBox.warning(self, 'Удаление', 'Задача не выбрана!')
                return
            task_name = ' '.join(task.text().split()[:-1])
            reply = QMessageBox.question(self, 'Удаление',
                                         f'Вы точно хотите удалить задачу {task_name.text()}?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
            self.status.setText(f'Задача {task_name} удалена!')
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
            task_name = self.exist_tasks_diary.currentItem() if tool_type == 'd' \
                else self.tasks_diary.currentItem()
            if task_name is None:
                QMessageBox.warning(self, 'Удаление', 'Задача не выбрана!')
                return
            reply = QMessageBox.question(self, 'Удаление', f'Вы точно хотите удалить задачу {task_name.text()}?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return

            self.status.setText(f'Задача {task_name} удалена!')
            self.cur.execute("""DELETE FROM diary WHERE name = ?""", (task_name.text(),))
            self.con.commit()

            if tool_type == 'd':
                self.name_diary.clear()
                for i in self.days:
                    i.setChecked(False)
                self.show_tasks('d')
            elif tool_type == 'd2':
                self.days_diary.clear()
                self.show_tasks('d2')

        if 'sch' in tool_type:
            item = self.exist_tasks_schedule.currentItem() if tool_type == 'sch' \
                else self.tasks_schedule.currentItem()
            if item is None:
                QMessageBox.warning(self, 'Удаление', 'Задача не выбрана!')
                return
            task_name = ' '.join(item.text().split('\n')[:-2])
            reply = QMessageBox.question(self, 'Удаление', f'Вы точно хотите удалить задачу {task_name}?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
            self.status.setText(f'Задача {task_name} удалена!')
            self.cur.execute("""DELETE FROM schedule WHERE name = ?""", (task_name,))
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
            task_name = task.split()[:-1]
            rdr = self.cur.execute("""SELECT name, crit1, crit2, crit3, crit4, crit5 FROM todo
                                    WHERE name = ?""", (task_name,)).fetchone()
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
            n_task = ' '.join(task.split('\n')[:-2])  # имя задачи
            self.name_schedule.setText(n_task)
            rdr = self.cur.execute("""SELECT name, date, time, crit1, crit2, crit3, crit4, crit5 FROM schedule
                                             WHERE name = ?""", (n_task,)).fetchone()
            self.calendarWidget.setSelectedDate(QDate.fromString(rdr[1], 'dd-MM-yyyy'))
            self.timeEdit.setTime(QTime.fromString(rdr[2], 'HH:mm'))

            for crit, num in zip(self.crits, rdr[3:]):
                crit.setText(str(num))

    def complete(self, tool_type):
        if tool_type == 't':  # если это задачник
            task = self.tasks_todo.currentItem()
            if task is None:
                QMessageBox.warning(self, 'Выполнение', 'Задача не выбрана!')
                return
            task_name = ' '.join(task.text().split()[:-1])
            if self.current_settings[2]:
                todo_points = int(*(self.cur.execute("""SELECT summa FROM todo WHERE name = ?""",
                                                     (task_name,)).fetchone()))
                days = self.cur.execute("SELECT date FROM results").fetchall()
                in_results = False
                for i in days:
                    if self.qtoday == ''.join(i):  # проверяем, что сегодняшняя дата есть в таблице
                        self.cur.execute("""UPDATE results SET points = points + ? 
                                                                WHERE date = ?""", (todo_points, self.qtoday))
                        in_results = True
                if in_results is False:
                    self.cur.execute("INSERT INTO results(date, points) VALUES(?, ?)",
                                     (self.qtoday, todo_points))
                QMessageBox.information(self, 'Выполнение',
                                        f"Задача {task_name} выполнена! Начислено: {todo_points}")

                self.cur.execute("""DELETE FROM todo WHERE name = ?""", (task_name,))
                self.update_graph()
            else:
                QMessageBox.information(self, 'Выполнение', f"Задача {task.text()} выполнена!")
                self.cur.execute("""DELETE FROM todo WHERE name = ?""", (task.text(),))

            self.con.commit()
            self.show_tasks('t2')
            self.show_crits('t2')

        elif tool_type == 'd':  # если это ежедневник
            task = self.tasks_diary.currentItem()
            if task is None:
                QMessageBox.warning(self, 'Выполнение', 'Задача не выбрана!')
                return
            self.cur.execute("UPDATE diary SET date_of_complete = ? WHERE name = ?",
                             (self.qtoday, task.text()))
            self.con.commit()
            self.show_all_tasks.setChecked(False)
            self.show_tasks('d2')

        elif tool_type == 'd22':  # если надо отменить выполнение задачи из ежедневника
            task = self.tasks_diary.currentItem()
            if task is None:
                QMessageBox.warning(self, 'Выполнение', 'Задача не выбрана!')
                return
            self.cur.execute("UPDATE diary SET date_of_complete = '' WHERE name = ?", (task.text(),))
            self.con.commit()
            self.show_all_tasks.setChecked(False)
            self.show_tasks('d2')

        elif tool_type == 'sch':  # если это планировщик
            task = self.tasks_schedule.currentItem()
            task_name = ' '.join(task.text().split()[:-2])

            if task is None:
                QMessageBox.warning(self, 'Выполнение', 'Задача не выбрана!')
                return
            if self.current_settings[2]:
                schedule_points = int(*(self.cur.execute("""SELECT summa FROM schedule WHERE name = ?""",
                                                         (task_name,)).fetchone()))
                days = self.cur.execute("SELECT date FROM results").fetchall()
                in_results = False
                for i in days:
                    if self.qtoday == ''.join(i):  # проверяем, что сегодняшней даты в таблице нет
                        self.cur.execute("""UPDATE results SET points = points + ? 
                                                                            WHERE date = ?""",
                                         (schedule_points, self.qtoday))
                        in_results = True
                if in_results is False:
                    self.cur.execute("INSERT INTO results(date, points) VALUES(?, ?)",
                                     (self.qtoday, schedule_points))
                QMessageBox.information(self, 'Выполнение', f"Задача {task_name} выполнена!"
                                                            f" Начислено: {schedule_points}")

                self.cur.execute("""DELETE FROM schedule WHERE name = ?""", (task_name,))
                self.update_graph()
            else:
                QMessageBox.information(self, 'Выполнение', "Задача {task_name} выполнена!")
                self.cur.execute("""DELETE FROM schedule WHERE name = ?""", (task_name,))

            self.con.commit()
            self.show_tasks('sch2')
            self.show_crits('sch2')

    # ----------------------------Графики--------------------------------------

    def draw_graph(self, figure):
        """Отрисовка данных"""
        figure.clear()
        ax = figure.add_subplot(111)
        results = self.cur.execute("""SELECT date, points FROM results
          ORDER BY substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)""").fetchall()

        monday = self.todays.addDays(-(int(self.today_weekday) - 1) + 7 * self.week_offset)
        sunday = monday.addDays(6)
        sunday_str = sunday.toString('dd-MM-yyyy')
        monday_str = monday.toString('dd-MM-yyyy')

        filtered = [(date_str, points) for date_str, points in results
                    if monday <= QDate.fromString(date_str, 'dd-MM-yyyy') <= sunday]

        dates = [r[0] for r in filtered]  # даты
        values = [r[1] for r in filtered]  # баллы
        if dates:
            ax.plot(dates, values, marker='o', linewidth=2, color='steelblue')
            ax.fill_between(dates, values, alpha=0.15, color='steelblue')
            ax.set_title(f'Успеваемость за неделю', fontsize=10)
            ax.set_ylabel('Баллы', fontsize=9)
            self.week_label.setText(f'{monday_str} - {sunday_str}')
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45, labelsize=7)
            ax.tick_params(axis='y', labelsize=7)
            figure.tight_layout()
        else:
            self.week_label.setText(f'{monday_str} - {sunday_str}')
            ax.text(0.5, 0.5, f'Нет данных за неделю',
                    ha='center', va='center', transform=ax.transAxes, fontsize=10, color='gray')

    def update_graph(self):
        """Перерисовывает уже существующий график"""
        if getattr(self, 'current_graph', None) is not None:
            self.draw_graph(self.current_graph.figure)
            self.current_graph.draw()

    def make_graph(self, parent, x, y, w, h):
        """Создать график"""
        fig = Figure(figsize=(w // 100, h // 100), dpi=100)
        canvas = FigureCanvas(fig)
        canvas.setParent(parent)
        canvas.move(x, y)
        canvas.resize(w, h)
        canvas.raise_()
        self.draw_graph(fig)
        canvas.draw()
        return canvas

    def prev_week(self):
        self.week_offset -= 1
        self.update_graph()

    def next_week(self):
        self.week_offset += 1
        self.update_graph()

    def menu_clicked(self, window_key):
        if QApplication.mouseButtons() & Qt.MouseButton.LeftButton:
            self.open(window_key)

    # -------------------------------------------Настройки-----------------------------
    def update_settings(self):
        """Обновить настройки"""
        is_crits_on = 1 if self.is_crits_on.isChecked() else 0
        is_quotes_on = 1 if self.is_quotes_on.isChecked() else 0
        is_graph_on = 1 if self.is_graph_on.isChecked() else 0
        self.cur.execute('UPDATE settings'
                         ' SET is_crits_on = ?, is_quotes_on = ?, is_graph_on = ?',
                         (is_crits_on, is_quotes_on, is_graph_on))
        self.status.setText(f'Настройки изменены!')
        self.con.commit()
        self.current_settings = self.cur.execute('SELECT * FROM settings').fetchone()
        self.open('se')

    def add_or_redo_crit(self):
        """Функция для добавления/изменения критериев"""
        number_of_existing_criterions = int(self.cur.execute('SELECT COUNT(*) FROM criterions').fetchall()[0][0]) + 1
        if number_of_existing_criterions > 5:
            QMessageBox.warning(self, 'Добавление', 'Критериев не может быть больше 5! Критерий не был добавлен')
            return
        try:
            if not self.max_crit.text() or not self.min_crit.text():
                QMessageBox.warning(self, 'Настройки', 'Заполните минимальное/максимальное значение критерия!')
                return
            name_crit = self.name_crit.text()
            min_crit = int(self.min_crit.text())
            max_crit = int(self.max_crit.text())
            if min_crit < 0:
                QMessageBox.warning(self, 'Настройка',
                                    'Минимальное значение критерия должно быть больше нуля и быть натуральным!')
                return
            if max_crit <= 0:
                QMessageBox.warning(self, 'Настройка',
                                    'Максимальное значение критерия может быть исключительно натуральным!')
                return
            if min_crit >= max_crit:
                QMessageBox.warning(self, 'Настройка',
                                    'Минимальное значение критерия не должно быть равно или больше максимального!')
                return
            if min_crit > 0:
                while min_crit > 0:
                    min_crit -= 1
                    max_crit -= 1
                QMessageBox.information(self, 'Настройка',
                                        f'Вы выбрали ненулевое значение минимального значения критерия. '
                                        f'Для правильного подсчёта результатов минимальное значение теперь будет равно {min_crit + 1}, '
                                        f'а максимальное значение будет равно {max_crit}')
            if not self.criterions_redact.currentItem():  # если не выбран критерий для изменения
                self.cur.execute('INSERT INTO criterions(name, min, max)'
                                 ' VALUES(?, ?, ?)', (name_crit, min_crit, max_crit,))
            else:
                answer = QMessageBox.question(self, 'Изменение',
                                              f'Вы точно хотите переписать критерий {name_crit}?',
                                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if answer != QMessageBox.StandardButton.Yes:
                    return
                self.cur.execute('UPDATE criterions SET min = ?, max = ? WHERE name = ?',
                                 (min_crit, max_crit, name_crit))

        except ValueError:
            QMessageBox.warning(self, 'Добавление', "Заполните минимальное/максимальное значения"
                                                    " критериев натуральными цифрами!")
            return
        except sqlite3.IntegrityError:
            answer = QMessageBox.question(self, 'Добавление',
                                          f'Критерий с именем {name_crit} уже существует. Вы хотите его переписать?',
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            self.cur.execute('UPDATE criterions SET min = ?, max = ? WHERE name = ?',
                             (min_crit, max_crit, name_crit))

        self.status.setText(f'Критерий {name_crit} добавлена!')
        self.name_crit.clear()
        self.min_crit.clear()
        self.max_crit.clear()
        self.open('se2')
        self.con.commit()

    def del_crit(self):
        """Удаляет критерий"""
        crit = self.criterions_redact.currentItem()
        if not crit:
            QMessageBox.warning(self, 'Удаление', 'Выберите критерий!')
            return
        crit_name = crit.text().split()[0]
        answer = QMessageBox.question(self, 'Удаление', f'Вы действительно хотите удалить критерий {crit_name}?',
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.cur.execute('DELETE FROM criterions WHERE name = ?', (crit_name,))

        self.status.setText(f'Задача {crit_name} удалена!')
        self.name_crit.clear()
        self.min_crit.clear()
        self.max_crit.clear()
        self.open('se2')
        self.con.commit()

    def fill_or_defill_lineedits_settings(self, fill, crits):
        """Заполняет или очищает QLineEdit в настройках"""
        if fill:
            if crits:  # если надо заполнять критерии
                name = ' '.join(self.criterions_redact.currentItem().text().split()[:-3])
                crit = self.cur.execute("SELECT * FROM criterions WHERE name = ?", (name,)).fetchone()
                self.name_crit.setText(crit[1])
                self.min_crit.setText(str(crit[2]))
                self.max_crit.setText(str(crit[3]))
            else:  # если надо заполнять цитаты
                name = ' '.join(self.quotes_redact.currentItem().text().split()[1:-1])
                quote = ' '.join(self.cur.execute("SELECT quote FROM phylosophy WHERE quote LIKE ? || '%'",
                                                  (name,)).fetchone())
                self.new_quote.setText(quote)
        if not fill:
            if crits:  # если надо очистить критерии
                self.criterions_redact.setCurrentItem(None)
                self.name_crit.setText('')
                self.min_crit.setText('')
                self.max_crit.setText('')
            else:  # если надо очистить цитаты
                self.quotes_redact.setCurrentItem(None)
                self.new_quote.setText('')

    def add_or_redo_quote(self):
        if not self.new_quote.text():
            QMessageBox.warning(self, 'Добавление', 'Поле ввода цитат пусто!')
            return
        if not self.quotes_redact.currentItem():  # добавление
            self.cur.execute("INSERT INTO phylosophy(quote) VALUES(?)", (self.new_quote.text(),))
            self.status.setText(f'Цитата {self.new_quote.text()[10:]}... добавлена!')
        else:  # изменение
            num = self.quotes_redact.currentItem().text().split()[0].strip('.')
            name = ' '.join(self.quotes_redact.currentItem().text().split()[1:-1])
            answer = QMessageBox.question(self, 'Изменение', f'Вы точно хотите изменить цитату под номером {num}?',
                                          QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            self.cur.execute("UPDATE phylosophy SET quote = ? "
                             "WHERE quote LIKE (SELECT quote FROM phylosophy WHERE quote LIKE ? || '%')",
                             (self.new_quote.text(), name))
            self.status.setText(f'Цитата {name[10:]}... изменена на {self.new_quote.text()[10:]}...!')
        nr = self.cur.execute('SELECT quote FROM phylosophy ORDER BY random() LIMIT 1').fetchone()
        r = ''.join(nr) if nr else ''
        self.phylosophy_browser.setHtml(f'<div style="text-align: center;"><h1>{r}</h1></div>')
        self.new_quote.clear()
        self.open('se3')
        self.con.commit()

    def del_quote(self):
        if not self.quotes_redact.currentItem():
            QMessageBox.warning(self, 'Удаление', "Выберите цитату!")
            return
        name = ' '.join(self.quotes_redact.currentItem().text().split()[1:-1])
        idishnik = ''.join(self.quotes_redact.currentItem().text().split()[:1]).strip('.')
        answer = QMessageBox.question(self, 'Удаление', f'Вы точно хотите удалить цитату под номером {idishnik}?',
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.cur.execute("DELETE FROM phylosophy WHERE quote LIKE ? || '%'",
                         (name,))
        self.status.setText(f'Цитата {name[10:]}... удалена!')
        self.open('se3')
        self.new_quote.clear()
        self.con.commit()


if __name__ == '__main__':
    app = QApplication(argv)
    om = OmniTracker()

    nr = om.cur.execute('SELECT quote FROM phylosophy ORDER BY random() LIMIT 1').fetchone()
    r = ''.join(nr) if nr else ''
    om.phylosophy_browser.setHtml(f'<div style="text-align: center;"><h1>{r}</h1></div>')

    om.clipboard = QApplication.clipboard()

    om.open('g')
    om.show()
    exit(app.exec())
