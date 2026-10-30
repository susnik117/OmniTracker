import sys
from io import StringIO
import datetime as dt
from PyQt6.QtWidgets import QMainWindow, QApplication, QMenuBar, QLineEdit, QMessageBox
from PyQt6 import uic
import csv


# TODO: сделать так, чтобы панели, на которых выбираются уже существующие задачи выдвигались только тогда, когда
# TODO: соответствующие checkbox'ы нажаты

class TooManyCritsError(Exception):
    """Вызывается тогда, когда слишком много критериев"""
    pass


class WrongValue(Exception):
    """Вызывается тогда, когда в числовые значения критериев ввели неправильные критерии"""
    pass


class NoCritsError(Exception):
    """Вызывается тогда, когда критериев нет"""
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
        self.todays_date = dt.date.today()

        self.todo_plus.hide()
        self.diary_plus.hide()
        self.schedule_plus.hide()

        self.todo.move(0, 0)
        self.todo_2.move(0, 0)
        self.diary.move(0, 0)
        self.diary_2.move(0, 0)
        self.schedule.move(0, 0)
        self.schedule_2.move(0, 0)
        self.results.move(0, 0)
        self.settings.move(0, 0)

        self.criterion1 = QLineEdit(self)
        self.criterion1.resize(80, 20)
        self.criterion1.move(400, 170)
        self.criterion1.hide()

        self.criterion2 = QLineEdit(self)
        self.criterion2.resize(80, 20)
        self.criterion2.move(400, 206)
        self.criterion2.hide()

        self.criterion3 = QLineEdit(self)
        self.criterion3.resize(80, 20)
        self.criterion3.move(400, 242)
        self.criterion3.hide()

        self.criterion4 = QLineEdit(self)
        self.criterion4.resize(80, 20)
        self.criterion4.move(400, 278)
        self.criterion4.hide()

        self.criterion5 = QLineEdit(self)
        self.criterion5.resize(80, 20)
        self.criterion5.move(400, 314)
        self.criterion5.hide()

        self.crits = [self.criterion1, self.criterion2, self.criterion3, self.criterion4, self.criterion5]  # список
        # всех кнопок-критериев

        self.criterions = {  # численные значения критериев
            'criterion1': 0,
            'criterion2': 0,
            'criterion3': 0,
            'criterion4': 0,
            'criterion5': 0
        }

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
        self.diarybtn_todo.clicked.connect(self.diary_open_plus)  # для перемещения между инструментами в вкладках "+"
        self.diarybtn_schedule.clicked.connect(self.diary_open_plus)
        self.todobtn_diary.clicked.connect(self.todo_open_plus)
        self.todobtn_schedule.clicked.connect(self.todo_open_plus)
        self.schedulebtn_todo.clicked.connect(self.schedule_open_plus)
        self.schedulebtn_diary.clicked.connect(self.schedule_open_plus)

        self.plus_btn.clicked.connect(self.plus)  # для кнопки "+" на глав. панеле
        self.todo_plus.clicked.connect(self.todo_open_plus)
        self.diary_plus.clicked.connect(self.diary_open_plus)
        self.schedule_plus.clicked.connect(self.schedule_open_plus)

        self.addbtn_todo.clicked.connect(self.todo_add)  # для добавления задач в инструменты

        self.cb_todo.stateChanged.connect(self.show_tasks)
        self.cb_diary.stateChanged.connect(self.show_tasks)
        self.cb_schedule.stateChanged.connect(self.show_tasks)

        self.delbtn_todo.clicked.connect(self.delete_tasks)

        self.general_open()

    # =========================== ФУНКЦИИ ==========================================
    # ---------------------------Функции открывашки--------------------------------
    # TODO: сделать так, чтобы открывали другие вкладки, а не те, которые для "+" предназначены
    def general_open(self):
        """Открывает главную страницу"""
        self.general.show()  # показываем только главную страницу
        self.todo.hide()
        self.todo_2.hide()
        self.diary.hide()
        self.diary_2.hide()
        self.schedule.hide()
        self.schedule_2.hide()
        self.results.hide()
        self.settings.hide()

        self.todo_plus.hide()
        self.diary_plus.hide()
        self.schedule_plus.hide()

        self.criterion1.hide()
        self.criterion2.hide()
        self.criterion3.hide()
        self.criterion4.hide()
        self.criterion5.hide()

        self.cb_todo.setChecked(False)
        self.cb_schedule.setChecked(False)
        self.cb_diary.setChecked(False)

        self.date.setText(f'{self.todays_date}')

    def todo_open(self):
        """Открывает вкладку задачника"""
        # TODO: сейчас у меня так, что задаваемые критерии показываются в параметрах задачи.
        #  Нужно сделать так, чтобы, показывались в левой панели
        self.general.hide()
        self.todo.hide()
        self.todo_2.show()  # показываем только задачник (основная вкладка)
        self.diary.hide()
        self.diary_2.hide()
        self.schedule.hide()
        self.schedule_2.hide()
        self.results.hide()
        self.settings.hide()

        self.exist_tasks_todo.clear()
        self.exist_tasks_diary.clear()
        self.exist_tasks_schedule.clear()

        self.criterion1.hide()
        self.criterion2.hide()
        self.criterion3.hide()
        self.criterion4.hide()
        self.criterion5.hide()

    def diary_open(self):
        """Открывает вкладку ежедневника"""
        self.general.hide()
        self.todo.hide()
        self.todo_2.hide()
        self.diary.hide()
        self.diary_2.show()  # показываем только ежедневник (основная вкладка)
        self.schedule.hide()
        self.schedule_2.hide()
        self.results.hide()
        self.settings.hide()

        self.criterion1.hide()
        self.criterion2.hide()
        self.criterion3.hide()
        self.criterion4.hide()
        self.criterion5.hide()

    def schedule_open(self):
        """Открывает вкладку планировщика"""
        self.general.hide()
        self.todo.hide()
        self.todo_2.hide()
        self.diary.hide()
        self.diary_2.hide()
        self.schedule.hide()
        self.schedule_2.show()  # показываем только планировщик (основная вкладка)
        self.results.hide()
        self.settings.hide()

        self.criterion1.hide()
        self.criterion2.hide()
        self.criterion3.hide()
        self.criterion4.hide()
        self.criterion5.hide()

    def results_open(self):
        """Открывает вкладку с результатами"""
        self.general.hide()
        self.todo.hide()
        self.todo_2.hide()
        self.diary.hide()
        self.diary_2.hide()
        self.schedule.hide()
        self.schedule_2.hide()
        self.results.show()  # показываем только результаты
        self.settings.hide()

        self.criterion1.hide()
        self.criterion2.hide()
        self.criterion3.hide()
        self.criterion4.hide()
        self.criterion5.hide()

        self.cb_todo.setChecked(False)
        self.cb_schedule.setChecked(False)
        self.cb_diary.setChecked(False)

    def settings_open(self):
        """Открывает вкладку с настройками"""
        self.general.hide()
        self.todo.hide()
        self.todo_2.hide()
        self.diary.hide()
        self.diary_2.hide()
        self.schedule.hide()
        self.schedule_2.hide()
        self.results.hide()
        self.settings.show()  # показываем только настройки

        self.todo_plus.hide()
        self.diary_plus.hide()
        self.schedule_plus.hide()

        self.criterion1.hide()
        self.criterion2.hide()
        self.criterion3.hide()
        self.criterion4.hide()
        self.criterion5.hide()

        self.cb_todo.setChecked(False)
        self.cb_schedule.setChecked(False)
        self.cb_diary.setChecked(False)

    def plus(self):
        """Кнопка "+" """
        self.todo_plus.show()
        self.diary_plus.show()
        self.schedule_plus.show()

    def todo_open_plus(self):
        """Открывает вкладку "+" у задачника"""
        self.general.hide()
        self.todo.show()
        self.diary.hide()
        self.schedule.hide()

        self.cb_todo.setChecked(False)
        self.cb_schedule.setChecked(False)
        self.cb_diary.setChecked(False)

        with open('criterions.csv', 'r', encoding='utf8') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)
            rdr = list(reader)

            self.tasks_criterions_todo.clear()
            for i, crit in zip(rdr, self.crits):
                self.tasks_criterions_todo.addItem(i[0])
                self.tasks_criterions_todo.addItem('↑')
                crit.show()

    def diary_open_plus(self):
        """Открывает вкладку "+" у ежедневника"""
        self.general.hide()
        self.todo.hide()
        self.diary.show()
        self.schedule.hide()

        self.criterion1.hide()
        self.criterion2.hide()
        self.criterion3.hide()
        self.criterion4.hide()
        self.criterion5.hide()

        self.cb_todo.setChecked(False)
        self.cb_schedule.setChecked(False)
        self.cb_diary.setChecked(False)

    def schedule_open_plus(self):
        """Открывает вкладку "+" у планировщика"""
        self.general.hide()
        self.todo.hide()
        self.diary.hide()
        self.schedule.show()

        self.cb_todo.setChecked(False)
        self.cb_schedule.setChecked(False)
        self.cb_diary.setChecked(False)

        with open('criterions.csv', 'r', encoding='utf8') as f:  # открытие критериев
            reader = csv.reader(f, delimiter=';')
            next(reader)
            rdr = list(reader)
            self.tasks_criterions_schedule.clear()
            for line, crit in zip(rdr, self.crits):
                self.tasks_criterions_schedule.addItem(line[0])
                self.tasks_criterions_schedule.addItem('↑')
                crit.show()

    # -----------------------------Функции для добавления задач----------------------

    def todo_add(self):
        """Добавить задачу в задачник"""
        with open('todo.csv', 'a', encoding='utf8') as f_write, \
                open('todo.csv', 'r', encoding='utf8') as f_todo, \
                open('criterions.csv', 'r', encoding='utf8') as f_crits:
            for num, crit in zip(self.criterions, self.crits):
                if not crit.isHidden():
                    self.criterions[num] = crit.text()
            try:
                fnum = self.criterion1.text()
                snum = self.criterion2.text()
                tnum = self.criterion3.text()
                frnum = self.criterion4.text()
                fvnum = self.criterion5.text()

                if all(not x or x.isdigit() for x in [fnum, snum, tnum, frnum, fvnum]):
                    pass
                else:
                    raise WrongValue

                if not self.name_todo.text():
                    raise EmptyName

                reader_names = csv.reader(f_todo)
                next(reader_names)
                for name in reader_names:
                    if self.name_todo.text() in name[0]:
                        raise IdenticalNames

                reader_crits = csv.reader(f_crits)
                next(reader_crits)
                filled = [c for c in self.crits if not c.isHidden() and c.text().strip()]
                if len(filled) < len([c for c in self.crits if not c.isHidden()]):
                    raise IncompleteInput


            except WrongValue:
                QMessageBox.warning(
                    self,
                    'Ошибка ввода',
                    'В вводе критериев обнаружены не-цифры!'
                )
            except IdenticalNames:
                QMessageBox.warning(
                    self,
                    'Ошибка ввода',
                    'Существуют задачи с таким же именем!'
                )
            except IncompleteInput:
                QMessageBox.warning(
                    self,
                    'Ошибка ввода',
                    'Заполнены не все критерии!'
                )
            except EmptyName:
                QMessageBox.warning(
                    self,
                    'Ошибка ввода',
                    'Имя не введено!'
                )
            else:
                print(f'{self.name_todo.text()};'
                      f'{fnum if True else 0};'
                      f'{snum if True else 0};'
                      f'{tnum if True else 0};'
                      f'{frnum if True else 0};'
                      f'{fvnum if True else 0};', file=f_write)

    # ------------------------------Остальные функции----------------------------------------------------

    def show_tasks(self):
        """Показать уже существующие задачи"""
        with open('todo.csv', 'r', encoding='utf8') as f:
            # TODO: надо придумать, как показывать текущие критерии у задачи
            reader = csv.reader(f, delimiter=';')
            next(reader)
            rdr = list(reader)

            if self.cb_todo.isChecked():
                self.exist_tasks_todo.clear()
                for task in rdr:
                    self.exist_tasks_todo.addItem(task[0])
            else:
                self.exist_tasks_todo.clear()

    def delete_tasks(self):
        """Удалить уже существующие задачи"""
        item = self.exist_tasks_todo.currentItem()
        if item is None:
            QMessageBox.warning(
                self,
                'Удаление',
                'Задача не выбрана!'
            )
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
        self.exist_tasks_todo.takeItem(self.exist_tasks_todo.row(item))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    om = OmniTracker()
    om.show()
    sys.exit(app.exec())
