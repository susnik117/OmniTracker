from sys import argv, exit
from io import StringIO
from PyQt6.QtWidgets import QMainWindow, QListWidgetItem, QApplication, QMenuBar, QLineEdit, QMessageBox
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import QTime, QDate
from PyQt6 import uic
from csv import reader, writer
from random import choice
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

class WrongValue(Exception):
    """Вызывается тогда, когда в числовые значения критериев ввели неправильные критерии"""
    pass


class IncompleteInput(Exception):
    """Вызывается тогда, когда заполнены не все критерии/дни"""
    pass


class EmptyName(Exception):
    """Вызывается тогда, когда имени у задачи нет"""
    pass


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
        # всех кнопок-критериев

        y_move = 100
        for crit in self.crits:
            crit.resize(80, 20)
            crit.move(400, y_move)
            crit.hide()
            y_move += 53

        # здесь будут записываться данные с файлов, чтобы читать их и не нужно было при каждой операции открывать файлы
        self.todo_file = []
        self.diary_file = []
        self.schedule_file = []

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

        self.current_graph = self.make_graph(self.general, 0, 90, 487, 348)

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

                for task in self.schedule_file[1:]:  # задачи из планировщика
                    # проверяем на то, что сегодня -- тот день, в которую должна высвечиваться задача
                    if self.todays == QDate.fromString(task[1], 'dd-MM-yyyy'):
                        t = QListWidgetItem(task[0])
                        font = t.font()
                        font.setPointSize(12)  # размер в пунктах
                        font.setBold(True)  # полужирный
                        t.setFont(font)
                        self.today_list.addItem(t)

                for task in self.diary_file[1:]:  # задачи из ежедневника
                    days_active = task[2:]
                    # проверяем на то, что сегодня -- тот день недели, в которую должна высвечиваться задача
                    if self.today_weekday in days_active and task[1] != self.todays:
                        self.today_list.addItem(task[0])

            case 't':
                self.todo.show()
                _, rdr = self.read_file('criterions.csv')

                self.tasks_criterions_todo.clear()
                for i, crit in zip(rdr, self.crits):
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
                _, rdr = self.read_file('criterions.csv')
                self.tasks_criterions_schedule.clear()
                for line, crit in zip(rdr, self.crits):
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
        try:
            fnum = self.criterion1.text().strip()
            snum = self.criterion2.text().strip()
            tnum = self.criterion3.text().strip()
            frnum = self.criterion4.text().strip()
            fvnum = self.criterion5.text().strip()

            if not all(not x or x.isdigit() for x in [fnum, snum, tnum, frnum, fvnum]):
                raise WrongValue

            if not self.name_todo.text().strip():
                raise EmptyName

            ready = [c for c in self.crits if not c.isHidden()]  # действительные в данный момент критерии
            if any(not c.text().strip() for c in ready):
                raise IncompleteInput

            header, rn = self.todo_file[0], self.todo_file[1:]
            ident = next((row for row in rn if row and row[0] == self.name_todo.text().strip()), None)

            if ident:
                reply = QMessageBox.question(
                    self, 'Изменение',
                    "Задача с таким именем уже существует. Вы хотите переписать её?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return
                else:
                    rn = [row for row in rn if row[0] != ident[0]]
            if self.tasks_todo.currentItem():
                rn = [row for row in rn if row[0] != self.name_todo.text().strip()
                      and row[0] != self.tasks_todo.currentItem().text()]
            elif self.exist_tasks_todo.currentItem():
                rn = [row for row in rn if row[0] != self.name_todo.text().strip()
                      and row[0] != self.exist_tasks_todo.currentItem().text()]
            else:
                rn = [row for row in rn if row[0] != self.name_todo.text().strip()]

            new_row = [
                self.name_todo.text().strip(), fnum if True else '0', snum if True else '0', tnum if True else '0',
                frnum if True else '0', fvnum if True else '0', ]
            rn.append(new_row)
            self.write_file('todo.csv', header, rn)

            self.name_todo.clear()
            for crit in ready:
                crit.clear()

        except WrongValue:
            QMessageBox.warning(self, 'Ошибка ввода', 'В вводе критериев обнаружены не-цифры!')
        except IncompleteInput:
            QMessageBox.warning(self, 'Ошибка ввода', 'Заполнены не все критерии!')
        except EmptyName:
            QMessageBox.warning(self, 'Ошибка ввода', 'Имя не введено!')

    def diary_add(self):
        """Добавить задачу в ежедневник"""
        try:
            if not self.name_diary.text():
                raise EmptyName

            if not any(x for x in self.days if x.isChecked()):
                raise IncompleteInput

            header, rdr = self.diary_file[0], self.diary_file[1:]

            # ищем совпадения
            ident = next((row for row in rdr if row and row[0] == self.name_diary.text().strip()), None)

            if ident:
                reply = QMessageBox.question(
                    self, 'Изменение',
                    "Задача с таким именем уже существует. Вы хотите переписать её?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return
                else:
                    rdr = [row for row in rdr if row[0] != ident[0]]

            if self.tasks_diary.currentItem():
                rdr = [row for row in rdr if row[0] != self.name_diary.text().strip()
                       and row[0] != self.tasks_diary.currentItem().text()]
            elif self.exist_tasks_diary.currentItem():
                rdr = [row for row in rdr if row[0] != self.name_diary.text().strip()
                       and row[0] != self.exist_tasks_diary.currentItem().text()]
            else:
                rdr = [row for row in rdr if row[0] != self.name_diary.text().strip()]

            new_row = [
                self.name_diary.text().strip(),
                ";",
                '1' if self.monday.isChecked() else '0',
                '2' if self.tuesday.isChecked() else '0',
                '3' if self.wednesday.isChecked() else '0',
                '4' if self.thursday.isChecked() else '0',
                '5' if self.friday.isChecked() else '0',
                '6' if self.saturday.isChecked() else '0',
                '7' if self.sunday.isChecked() else '0'
            ]

            rdr.append(new_row)
            self.write_file('diary.csv', header, rdr)

            self.name_diary.clear()
            for i in self.days:
                i.setChecked(False)
            self.show_tasks('d')

        except EmptyName:
            QMessageBox.warning(self, 'Добавление', 'Имя не введено!')
        except IncompleteInput:
            QMessageBox.warning(self, 'Добавление', "Выберите хоть один день!")

    def schedule_add(self):
        """Добавить задачу в планировщк"""
        try:
            fnum = self.criterion1.text().strip()
            snum = self.criterion2.text().strip()
            tnum = self.criterion3.text().strip()
            frnum = self.criterion4.text().strip()
            fvnum = self.criterion5.text().strip()

            if not all(not x or x.isdigit() for x in [fnum, snum, tnum, frnum, fvnum]):
                raise WrongValue

            if not self.name_schedule.text().strip():
                raise EmptyName

            ready = [c for c in self.crits if not c.isHidden()]  # действительные в данный момент критерии
            if any(not c.text().strip() for c in ready):
                raise IncompleteInput
            date = self.calendarWidget.selectedDate().toString('dd-MM-yyyy')
            time = self.timeEdit.time().toString('HH:mm')
            if self.todays > self.calendarWidget.selectedDate():  # проверяем, назначается задача ли в прошлое
                reply = QMessageBox.question(self, 'Добавление', 'Задача назначается в прошлое. '
                                                                 'За её выполнение дастся только половина'
                                                                 ' от изначальной суммы баллов. Назначить всё равно?',
                                             QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return
            header, rn = self.schedule_file[0], self.schedule_file[1:]
            ident = next((row for row in rn if row and row[0] == self.name_schedule.text().strip()), None)

            if ident:
                reply = QMessageBox.question(
                    self, 'Изменение',
                    "Задача с таким именем уже существует. Вы хотите переписать её?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return
                else:
                    rn = [row for row in rn if row[0] != ident[0]]

            if self.tasks_schedule.currentItem():
                rn = [row for row in rn if row[0] != self.name_schedule.text().strip()
                      and row[0] != self.tasks_schedule.currentItem().text()]
            elif self.exist_tasks_schedule.currentItem():
                rn = [row for row in rn if row[0] != self.name_schedule.text().strip()
                      and row[0] != self.exist_tasks_schedule.currentItem().text()]
            else:
                rn = [row for row in rn if row[0] != self.name_schedule.text().strip()]

            new_row = [
                self.name_schedule.text().strip(),
                date,
                time,
                fnum if True else '0',
                snum if True else '0',
                tnum if True else '0',
                frnum if True else '0',
                fvnum if True else '0',
            ]
            rn.append(new_row)
            self.write_file('schedule.csv', header, rn)

            self.name_schedule.clear()
            for crit in ready:
                crit.clear()
            self.timeEdit.setTime(QTime(0, 0))

        except WrongValue:
            QMessageBox.warning(self, 'Ошибка ввода', 'В вводе критериев обнаружены не-цифры!')
        except IncompleteInput:
            QMessageBox.warning(self, 'Ошибка ввода', 'Заполнены не все критерии!')
        except EmptyName:
            QMessageBox.warning(self, 'Ошибка ввода', 'Имя не введено!')

    # ------------------------------Работа с задачами----------------------------------------------------

    def show_tasks(self, tool_type):
        """Показать уже существующие задачи"""
        if 't' in tool_type:  # если выбран задачник
            rdr_todo = self.todo_file[1:]
            if tool_type == 't':
                if self.cb_todo.isChecked():
                    self.exist_tasks_todo.clear()
                    for task in rdr_todo:
                        self.exist_tasks_todo.addItem(task[0])
                else:
                    for crit in self.crits:
                        crit.setText('')
                    self.name_todo.setText('')
                    self.exist_tasks_todo.clear()

            elif tool_type == 't2':
                self.tasks_todo.clear()
                for task in rdr_todo:
                    self.tasks_todo.addItem(task[0])

        elif 'd' in tool_type:  # если выбран ежедневник
            rdr_diary = self.diary_file[1:]

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
            rdr_schedule = self.schedule_file[1:]

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
                    if QDate.fromString(task[1], 'dd-MM-yyyy') == selected:
                        self.tasks_schedule.addItem(f'{task[0]}\n{task[2]}')

    def show_crits(self, tool_type: str):
        """Показывает критерии (для задачника и планировщика) и дни (для ежедневника)"""
        if 't' in tool_type:
            _, rdr_c = self.read_file('criterions.csv')
            rdr_t = self.todo_file[1:]
            task = []
            if tool_type == 't':
                for i in rdr_t:
                    if i[0] == self.exist_tasks_todo.currentItem().text():
                        task = i
                        break
                self.name_todo.setText(task[0])
                for crit, num in zip(self.crits, task[1:]):
                    crit.setText(num)

            if tool_type == 't2':
                cur = self.tasks_todo.currentItem()
                self.crits_todo.clear()
                if cur is None:
                    return
                for i in rdr_t:
                    if i[0] == cur.text():
                        task = i
                        break
                if not task:
                    return
                self.crits_todo.clear()
                for i, num in zip(rdr_c, task[1:]):
                    self.crits_todo.addItem(f'{i[0]}:\n   {num}')

        elif 'd' in tool_type:
            rdr = self.diary_file[1:]
            if tool_type == 'd':
                for i in rdr:
                    if i[0] == self.exist_tasks_diary.currentItem().text():
                        task = i
                        break
                self.name_diary.setText(task[0])
                for day in self.days:
                    day.setChecked(False)
                days = task[2:]
                if '1' in days:
                    self.monday.setChecked(True)
                if '2' in days:
                    self.tuesday.setChecked(True)
                if '3' in days:
                    self.wednesday.setChecked(True)
                if '4' in days:
                    self.thursday.setChecked(True)
                if '5' in days:
                    self.friday.setChecked(True)
                if '6' in days:
                    self.saturday.setChecked(True)
                if '7' in days:
                    self.sunday.setChecked(True)

            elif tool_type == 'd2':
                for i in rdr:
                    if i[0] == self.tasks_diary.currentItem().text():
                        task = i
                        break
                days = task[2:]
                self.days_diary.clear()
                if '1' in days:
                    self.days_diary.addItem('Понедельник')
                if '2' in days:
                    self.days_diary.addItem('Вторник')
                if '3' in days:
                    self.days_diary.addItem('Среда')
                if '4' in days:
                    self.days_diary.addItem('Четверг')
                if '5' in days:
                    self.days_diary.addItem('Пятница')
                if '6' in days:
                    self.days_diary.addItem('Суббота')
                if '7' in days:
                    self.days_diary.addItem('Воскресенье')

        if 'sch' in tool_type:
            _, rdr_c = self.read_file('criterions.csv')
            rdr_sch = self.schedule_file[1:]
            task = []
            if tool_type == 'sch':
                for i in rdr_sch:
                    if i[0] == self.exist_tasks_schedule.currentItem().text():
                        task = i
                        break
                self.name_schedule.setText(task[0])
                for crit, num in zip(self.crits, task[3:]):
                    crit.setText(num)

            if tool_type == 'sch2':
                self.crits_schedule.clear()
                cur = self.tasks_schedule.currentItem()
                for i in rdr_sch:
                    task_name = ' '.join(cur.text().split('\n')[:-1]).strip()
                    task = []
                    if i[0] == task_name:
                        task = i
                        break
                for i, num in zip(rdr_c, task[3:]):
                    self.crits_schedule.addItem(f'{i[0]}:\n   {num}')

    def delete_tasks(self, tool_type):
        """Удалить уже существующие задачи"""
        if 't' in tool_type:
            item_todo = self.exist_tasks_todo.currentItem() if tool_type == 't' else self.tasks_todo.currentItem()
            if item_todo is None:
                QMessageBox.warning(self, 'Удаление', 'Задача не выбрана!')
                return
            reply = QMessageBox.question(self, 'Удаление',
                                         f'Вы точно хотите удалить задачу {item_todo.text()}?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
            header_todo, reader_todo = self.todo_file[0], self.todo_file[1:]
            new_rows = [row for row in reader_todo if row[0] != item_todo.text()]

            self.write_file('todo.csv', header_todo, new_rows)

            if tool_type == 't':
                self.exist_tasks_todo.takeItem(self.exist_tasks_todo.row(item_todo))
                self.crits_todo.clear()
                self.show_tasks('t')
            elif tool_type == 't2':
                self.tasks_todo.takeItem(self.tasks_todo.row(item_todo))
                self.show_tasks('t2')

        elif 'd' in tool_type:
            item_diary = self.exist_tasks_diary.currentItem() if tool_type == 'd' else self.tasks_diary.currentItem()
            if item_diary is None:
                QMessageBox.warning(self, 'Удаление', 'Задача не выбрана!')
                return
            reply = QMessageBox.question(self, 'Удаление', f'Вы точно хотите удалить задачу {item_diary}?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
            header_diary, rdr_diary = self.diary_file[0], self.diary_file[1:]
            new_rows = [row for row in rdr_diary if row[0] != item_diary.text()]

            self.write_file('diary.csv', header_diary, new_rows)
            if tool_type == 'd':
                self.exist_tasks_diary.takeItem(self.exist_tasks_diary.row(item_diary))

                self.show_tasks('d')
            elif tool_type == 'd2':
                self.tasks_diary.takeItem(self.tasks_diary.row(item_diary))
                self.days_diary.clear()
                self.show_tasks('d2')

        if 'sch' in tool_type:
            item_schedule = self.exist_tasks_schedule.currentItem() if tool_type == 'sch' else self.tasks_schedule.currentItem()
            if item_schedule is None:
                QMessageBox.warning(self, 'Удаление', 'Задача не выбрана!')
                return

            reply = QMessageBox.question(self, 'Удаление', f'Вы точно хотите удалить задачу?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return

            task_name = ' '.join(item_schedule.text().split('\n')[:-1]).strip()

            header_schedule, reader_schedule = self.schedule_file[0], self.schedule_file[1:]
            new_rows = [row for row in reader_schedule if row[0] != task_name]

            self.write_file('schedule.csv', header_schedule, new_rows)

            if tool_type == 'sch':
                self.exist_tasks_schedule.takeItem(self.exist_tasks_schedule.row(item_schedule))
                self.crits_schedule.clear()
                self.show_tasks('sch')
            elif tool_type == 'sch2':
                self.tasks_schedule.takeItem(self.tasks_schedule.row(item_schedule))
                self.crits_schedule.clear()
                self.show_tasks('sch2')

    def redo(self, tool_type, task):  # изменяет задачу, направляя её во вкладку "+"
        if task is None:
            QMessageBox.warning(self, 'Изменение', 'Задача не выбрана!')
            return

        if 't' in tool_type:
            self.open('t')
            self.name_todo.setText(task)

            rdr = self.todo_file[1:]
            for i in rdr:
                if i[0] == task:
                    for crit, num in zip(self.crits, i[1:]):
                        crit.setText(str(num))
                    break

        elif 'd' in tool_type:
            self.open('d')
            self.name_diary.setText(task)

            rdr = self.diary_file[1:]

            for day in self.days:
                day.setChecked(False)

                for i in rdr:
                    if i[0] == task:
                        days = i[2:]
                        if '1' in days:
                            self.monday.setChecked(True)
                        if '2' in days:
                            self.tuesday.setChecked(True)
                        if '3' in days:
                            self.wednesday.setChecked(True)
                        if '4' in days:
                            self.thursday.setChecked(True)
                        if '5' in days:
                            self.friday.setChecked(True)
                        if '6' in days:
                            self.saturday.setChecked(True)
                        if '7' in days:
                            self.sunday.setChecked(True)

        elif 'sch' in tool_type:
            self.open('sch')
            n_task = task.split('\n')[0]
            self.name_schedule.setText(n_task)
            dt_task = [x for x in self.schedule_file if x[0].strip() == n_task]  # для того, чтобы найти время и дату
            rdr = self.schedule_file[1:]
            t_str = dt_task[0][2].strip()
            d_str = dt_task[0][1].strip()
            self.calendarWidget.setSelectedDate(QDate.fromString(d_str, 'dd-MM-yyyy'))
            self.timeEdit.setTime(QTime.fromString(t_str, 'HH:mm'))
            for i in rdr:
                if i[0] == n_task:
                    for crit, num in zip(self.crits, i[3:]):
                        crit.setText(str(num))
                    break

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

    # ----------------------------------Чтение файлов-----------------------------------

    def read_file(self, file):
        """читает файл, а также избавляется от лишних пробелов, отступов и прочих символов"""
        with open(file, 'r', encoding='utf8') as f:
            rdr = reader(f, delimiter=';')
            header = next(rdr)
            nr = [
                [field.strip() for field in row if field.strip()]
                for row in rdr
                if any(field.strip() for field in row)  # пропускаем пустые строки
            ]
            return header, nr

    def write_file(self, file, header, write):
        """пишет файл, после чего сразу же перезаписывает соответствующую инструменту переменную для хранения данных"""
        with open(file, 'w', encoding='utf8') as f:
            wrt = writer(f, delimiter=';')
            wrt.writerow(header)
            wrt.writerows(write)
        if file == 'todo.csv':
            self.todo_file = [header] + write
        elif file == 'diary.csv':
            self.diary_file = [header] + write
        elif file == 'schedule.csv':
            self.schedule_file = [header] + write

    # ----------------------------Графики--------------------------------------

    def load_graph(self):
        """Достаёт данные для графиков"""
        _, rdr = self.read_file('graph1.csv')
        points = []
        for row in rdr:
            date = QDate.fromString(row[0], 'dd-MM-yyyy')  # берём дату
            val = int(row[1])  # баллы за дату
            points.append((date, val))
        return points

    def draw_graph(self, figure):
        """Отрисовка данных"""
        figure.clear()
        ax = figure.add_subplot(111)
        points = self.load_graph()
        dates = [d.toString('dd-MM') for d, _ in points]  # даты
        values = [v for _, v in points]  # баллы
        ax.plot(dates, values, marker='o', linewidth=2, color='steelblue')
        ax.fill_between(range(len(values)), values, alpha=0.15, color='steelblue')
        ax.set_title('Успеваемость по дням', fontsize=10)
        ax.set_ylabel('Баллы', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45, labelsize=7)
        ax.tick_params(axis='y', labelsize=7)
        figure.tight_layout()

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


if __name__ == '__main__':
    app = QApplication(argv)
    om = OmniTracker()

    _, nr = om.read_file('phylosophy.txt')
    chitata = choice(nr)  # добавляем цитату
    ch = ' '.join(chitata)
    om.phylosophy_browser.setHtml(f'<div style="text-align: center;"><h1>{ch}</h1></div>')

    head, rdr = om.read_file('todo.csv')
    om.todo_file = [head] + rdr
    om.write_file('todo.csv', head, rdr)

    head_diary, rdr_diary = om.read_file('diary.csv')
    om.diary_file = [head_diary] + rdr_diary
    om.write_file('diary.csv', head_diary, rdr_diary)

    head_schedule, rdr_schedule = om.read_file('schedule.csv')
    om.schedule_file = [head_schedule] + rdr_schedule
    om.write_file('schedule.csv', head_schedule, rdr_schedule)

    headd, rdrr = om.read_file('graph1.csv')
    om.write_file('graph1.csv', headd, rdrr)
    om.open('g')
    om.show()
    exit(app.exec())
