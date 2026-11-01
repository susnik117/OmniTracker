import sys
from io import StringIO
import datetime as dt
from PyQt6.QtWidgets import QMainWindow, QApplication, QMenuBar, QLineEdit, QMessageBox
from PyQt6 import uic
import csv


# TODO: сделать так, чтобы панели, на которых выбираются уже существующие задачи выдвигались только тогда, когда
# TODO: соответствующие checkbox'ы нажаты

# TODO: сделать так, чтобы на вкладках с инструментами можно было переключаться между стандартной вкладкой и вкладкой +

# TODO: сейчас у меня так, что когда я перехожу между вкладками, то листы, на которых есть критерии, перезаполняются
#  Надо сделать проверку, что лист уже заполнен и в зависимости от результата заполнять или не заполнять

# TODO: сейчас у меня так, что open() постоянно делает то, что нужно сделать только при старте (например, сортирует файл
#  Нужно перекинуть это в if __name__ == '__main__'

class TooManyCritsError(Exception):
    """Вызывается тогда, когда слишком много критериев"""
    pass


class WrongValue(Exception):
    """Вызывается тогда, когда в числовые значения критериев ввели неправильные критерии"""
    pass


class IdenticalNames(Exception):
    """Вызывается тогда, когда у создаваемой задачи то же имя, что и у уже существующей"""
    pass


class IncompleteInput(Exception):
    """Вызывается тогда, когда заполнены не все критерии"""
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
        self.setFixedHeight(642)
        self.setFixedWidth(791)
        self.setWindowTitle('OmniTracker')
        self.todays = dt.datetime.strftime(dt.date.today(), '%d-%m-%Y')
        self.date.setText(f'{self.todays}')

        self.todo_plus.hide()
        self.diary_plus.hide()
        self.schedule_plus.hide()

        self.windows = [self.general, self.todo, self.todo_2, self.diary, self.diary_2, self.schedule, self.schedule_2,
                        self.results, self.settings]
        # все окна в один лист, чтобы можно было легко их открывать/перемещать

        for wind in self.windows:
            wind.move(0, 0)

        self.criterion1 = QLineEdit(self)
        self.criterion2 = QLineEdit(self)
        self.criterion3 = QLineEdit(self)
        self.criterion4 = QLineEdit(self)
        self.criterion5 = QLineEdit(self)

        self.crits = [self.criterion1, self.criterion2, self.criterion3, self.criterion4, self.criterion5]  # список
        # всех кнопок-критериев

        y_move = 170
        for crit in self.crits:
            crit.resize(80, 20)
            crit.move(400, y_move)
            crit.hide()
            y_move += 53

        self.criterions = {  # численные значения критериев
            'criterion1': 0,
            'criterion2': 0,
            'criterion3': 0,
            'criterion4': 0,
            'criterion5': 0
        }

        self.old_task_todo = []  # строка csv с именем и критериями задачи

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

        self.plus_btn.clicked.connect(lambda: self.open('p'))  # для кнопки "+" на глав. панеле
        self.todo_plus.clicked.connect(lambda: self.open('t'))
        self.diary_plus.clicked.connect(lambda: self.open('d'))
        self.schedule_plus.clicked.connect(lambda: self.open('sch'))

        self.addbtn_todo.clicked.connect(self.todo_add)  # для добавления задач в инструменты

        self.cb_todo.stateChanged.connect(lambda: self.show_tasks('t'))
        self.cb_diary.stateChanged.connect(lambda: self.show_tasks('d'))
        self.cb_schedule.stateChanged.connect(lambda: self.show_tasks('sch'))

        self.delbtn_todo.clicked.connect(lambda: self.delete_tasks('t'))
        self.delbtn_todo_2.clicked.connect(lambda: self.delete_tasks('t2'))

        self.complete_todo.clicked.connect(lambda: self.complete('t'))

        self.changebtn_todo.clicked.connect(
            lambda: self.redo('t', self.tasks_todo.currentItem().text())
            if self.tasks_todo.currentItem() is not None
            else QMessageBox.warning(self, 'Изменение', 'Задача не выбрана!')
        )

        self.tasks_todo.itemClicked.connect(lambda: self.show_crits('t'))

        self.open('g')

    # =========================== ФУНКЦИИ ==========================================

    def open(self, window):  # открывает вкладки
        for wind in self.windows:
            wind.hide()

        for crit in self.crits:
            crit.hide()

        self.cb_todo.setChecked(False)
        self.cb_schedule.setChecked(False)
        self.cb_diary.setChecked(False)

        self.exist_tasks_todo.clear()
        self.exist_tasks_diary.clear()
        self.exist_tasks_schedule.clear()

        self.todo_plus.hide()
        self.diary_plus.hide()
        self.schedule_plus.hide()

        match window:
            case 'g':
                self.general.show()
            case 't':
                self.todo.show()
                with open('criterions.csv', 'r', encoding='utf8') as f:
                    reader = csv.reader(f, delimiter=';')
                    next(reader)
                    rdr = list(reader)

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
            case 'd2':
                self.diary_2.show()
            case 'sch':
                self.schedule.show()
                with open('criterions.csv', 'r', encoding='utf8') as f:  # открытие критериев
                    reader = csv.reader(f, delimiter=';')
                    next(reader)
                    rdr = list(reader)
                    self.tasks_criterions_schedule.clear()
                    for line, crit in zip(rdr, self.crits):
                        self.tasks_criterions_schedule.addItem(line[0])
                        crit.show()
                        self.tasks_criterions_schedule.addItem('\n')
            case 'sch2':
                self.schedule_2.show()
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

            with open('todo.csv', 'r', encoding='utf8', newline='') as f_todo:  # читаем строки
                reader_names = csv.reader(f_todo, delimiter=';')
                header = next(reader_names)
                rn = list(reader_names)

            ident = next((row for row in rn if row and row[0] == self.name_todo.text().strip()), None)

            if self.old_task_todo:
                rn = [row for row in rn if row != self.old_task_todo]

                if ident is not None and ident != self.old_task_todo:
                    reply = QMessageBox.question(
                        self, 'Изменение',
                        "Задача с таким именем уже существует. Вы хотите переписать её?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply != QMessageBox.StandardButton.Yes:
                        return
                    rn = [row for row in rn if row[0] != self.self.name_todo.text().strip()]

                elif ident is not None:
                    reply = QMessageBox.question(
                        self, 'Изменение',
                        "Задача с таким именем уже существует. Вы хотите переписать её?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply != QMessageBox.StandardButton.Yes:
                        return
                    rn = [row for row in rn if row[0] != self.name_todo.text().strip()]

            new_row = [
                self.name_todo.text().strip(),
                fnum if True else '0',
                snum if True else '0',
                tnum if True else '0',
                frnum if True else '0',
                fvnum if True else '0',
            ]
            rn.append(new_row)

            with open('todo.csv', 'w', encoding='utf8', newline='') as f_write:
                writer = csv.writer(f_write, delimiter=';')
                writer.writerow(header)
                writer.writerows(rn)

            self.name_todo.clear()
            for crit in ready:
                crit.clear()
            self.old_task_todo = []

        except WrongValue:
            QMessageBox.warning(self, 'Ошибка ввода', 'В вводе критериев обнаружены не-цифры!')
        except IncompleteInput:
            QMessageBox.warning(self, 'Ошибка ввода', 'Заполнены не все критерии!')
        except EmptyName:
            QMessageBox.warning(self, 'Ошибка ввода', 'Имя не введено!')

    # ------------------------------Остальные функции----------------------------------------------------

    def show_tasks(self, type):
        """Показать уже существующие задачи"""
        if 't' in type:
            with open('todo.csv', 'r', encoding='utf8') as f:
                # TODO: надо придумать, как показывать текущие критерии у задачи
                reader = csv.reader(f, delimiter=';')
                next(reader)
                rdr = list(reader)

                if type == 't':
                    if self.cb_todo.isChecked():
                        self.exist_tasks_todo.clear()
                        for task in rdr:
                            self.exist_tasks_todo.addItem(task[0])
                    else:
                        self.exist_tasks_todo.clear()
                elif type == 't2':
                    self.tasks_todo.clear()
                    for task in rdr:
                        self.tasks_todo.addItem(task[0])
        elif 'd' in type:
            with open('diary.csv', 'r', encoding='utf8') as f:
                ...
        elif 'sch' in type:
            with open('schedule.csv', 'r', encoding='utf8') as f:
                ...

    def show_crits(self, type):
        match type:
            case 't':
                with open('criterions.csv', 'r', encoding='utf8') as f_crits, \
                        open('todo.csv', 'r', encoding='utf8') as f_todo:
                    reader_c = csv.reader(f_crits, delimiter=';')  # ридер для критериев
                    next(reader_c)
                    rdr_c = list(reader_c)

                    reader_t = csv.reader(f_todo, delimiter=';')  # ридер для задач
                    next(reader_t)
                    rdr_t = reader_t

                    task = []
                    for i in rdr_t:
                        if i[0] == self.tasks_todo.currentItem().text():
                            task = i
                            break
                    self.crits_todo.clear()
                    for i, num in zip(rdr_c, task[1:]):
                        self.crits_todo.addItem(f'{i[0]}:\n   {num}')

    def delete_tasks(self, type):
        """Удалить уже существующие задачи"""
        if type == 't':
            item = self.exist_tasks_todo.currentItem()
        elif type == 't2':
            item = self.tasks_todo.currentItem()

        if item is None:
            QMessageBox.warning(self, 'Удаление', 'Задача не выбрана!')
            return

        name_to_delete = item.text()

        with open('todo.csv', 'r', encoding='utf8') as f:
            reader = csv.reader(f, delimiter=';')
            header = next(reader)
            rows = list(reader)
        new_rows = [row for row in rows if row[0] != name_to_delete]

        with open('todo.csv', 'w', encoding='utf8', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(header)
            writer.writerows(new_rows)
        if type == 't':
            self.exist_tasks_todo.takeItem(self.exist_tasks_todo.row(item))
        elif type == 't2':
            self.tasks_todo.takeItem(self.tasks_todo.row(item))

    def redo(self, type, task):  # изменяет задачу, направляя её во вкладку "+"
        if task is None:
            QMessageBox.warning(self, 'Изменение', 'Задача не выбрана!')
            return
        if 't' in type:
            self.open('t')
            self.name_todo.setText(task)

            with open('todo.csv', 'r', encoding='utf8') as f:
                reader = csv.reader(f, delimiter=';')
                next(reader)
                rdr = list(reader)

                for i in rdr:
                    if i[0] == task:
                        self.old_task_todo = i
                        for crit, num in zip(self.crits, i[1:]):
                            crit.setText(str(num))
                        break

    def complete(self, type):
        if type == 't':
            item = self.tasks_todo.currentItem()
            if item is None:
                QMessageBox.warning(self, 'Выполнение', 'Задача не выбрана!')
                return

            try:
                with open('graph1.csv', 'r', encoding='utf8') as f_read_res, \
                        open('todo.csv', 'r', encoding='utf8') as f_read_todo:
                    reader_res = csv.reader(f_read_res, delimiter=';')
                    reader_todo = csv.reader(f_read_todo, delimiter=';')
                    header_res = next(reader_res, None)
                    header_todo = next(reader_todo, None)
                    if header_res is None or header_todo is None:
                        QMessageBox.warning(self, 'Выполнение', 'Файл пуст!')
                        return
                    rdr_res = list(reader_res)  # ридер для результатов
                    rdr_todo = list(reader_todo)  # ридер для задач
            except FileNotFoundError as e:
                QMessageBox.warning(self, 'Выполнение', f'Файл не найден!')
                return

            task = [x for x in rdr_todo if x and x[0] == item.text()]
            if not task:
                QMessageBox.warning(self, 'Выполнение', 'Задача не найдена в файле!')
                return
            summa = sum(int(n) for n in task[0][1:] if n)

            new_rows = [row for row in rdr_todo if row[0] != item.text()]

            updated_res = []  # обновление graph1
            today = False
            for row in rdr_res:
                if row[0] == self.todays:
                    updated_res.append([row[0], str(int(row[1]) + summa)])
                    today = True
                else:
                    updated_res.append(row)
            if not today:
                updated_res.append([self.todays, str(summa)])

            with open('graph1.csv', 'w', encoding='utf8', newline='') as f_write_res, \
                    open('todo.csv', 'w', encoding='utf8', newline='') as f_write_todo:
                writer_res = csv.writer(f_write_res, delimiter=';')
                writer_todo = csv.writer(f_write_todo, delimiter=';')

                writer_todo.writerow(header_todo)
                for i in new_rows:
                    writer_todo.writerow(i)

                writer_res.writerow(header_res)
                for i in updated_res:
                    writer_res.writerow(i)

            self.show_tasks('t2')
            self.show_crits('t')


if __name__ == '__main__':
    with open('todo.csv', 'r', encoding='utf8') as f_read:  # освобождаем файл от лишних пробелов и строк
        reader = f_read.readlines()
        rdr = list(reader)
        nr = [string.strip('\n') for string in rdr if string.strip('\n n')]
        with open('todo.csv', 'w', encoding='utf8') as f_write:
            for i in nr:
                print(i, file=f_write)

    app = QApplication(sys.argv)
    om = OmniTracker()
    om.show()
    sys.exit(app.exec())
