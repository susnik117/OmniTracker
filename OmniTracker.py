import sys
from io import StringIO
import datetime as dt
from PyQt6.QtWidgets import QMainWindow, QApplication, QMenuBar
from PyQt6 import uic


f = '''<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>800</width>
    <height>621</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>MainWindow</string>
  </property>
  <widget class="QWidget" name="centralwidget">
   <widget class="QWidget" name="verticalLayoutWidget">
    <property name="geometry">
     <rect>
      <x>20</x>
      <y>110</y>
      <width>251</width>
      <height>441</height>
     </rect>
    </property>
    <layout class="QVBoxLayout" name="verticalLayout">
     <item>
      <widget class="QLabel" name="graph1">
       <property name="text">
        <string>(возможно, здесь будут графики)</string>
       </property>
      </widget>
     </item>
     <item>
      <widget class="QLabel" name="graph3">
       <property name="text">
        <string>(возможно, здесь будут графики)</string>
       </property>
      </widget>
     </item>
    </layout>
   </widget>
   <widget class="QWidget" name="verticalLayoutWidget_2">
    <property name="geometry">
     <rect>
      <x>540</x>
      <y>110</y>
      <width>241</width>
      <height>441</height>
     </rect>
    </property>
    <layout class="QVBoxLayout" name="verticalLayout_2">
     <item>
      <widget class="QLabel" name="graph2">
       <property name="text">
        <string>(возможно, здесь будут графики)</string>
       </property>
      </widget>
     </item>
     <item>
      <widget class="QLabel" name="graph4">
       <property name="text">
        <string>(возможно, здесь будут графики)</string>
       </property>
      </widget>
     </item>
    </layout>
   </widget>
   <widget class="QTextBrowser" name="phylosophy_label">
    <property name="geometry">
     <rect>
      <x>20</x>
      <y>10</y>
      <width>761</width>
      <height>91</height>
     </rect>
    </property>
    <property name="html">
     <string>&lt;!DOCTYPE HTML PUBLIC &quot;-//W3C//DTD HTML 4.0//EN&quot; &quot;http://www.w3.org/TR/REC-html40/strict.dtd&quot;&gt;
&lt;html&gt;&lt;head&gt;&lt;meta name=&quot;qrichtext&quot; content=&quot;1&quot; /&gt;&lt;meta charset=&quot;utf-8&quot; /&gt;&lt;style type=&quot;text/css&quot;&gt;
p, li { white-space: pre-wrap; }
hr { height: 1px; border-width: 0; }
li.unchecked::marker { content: &quot;\2610&quot;; }
li.checked::marker { content: &quot;\2612&quot;; }
&lt;/style&gt;&lt;/head&gt;&lt;body style=&quot; font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;&quot;&gt;
&lt;p style=&quot; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:24pt; font-style:italic;&quot;&gt;Возможно, здесь будут философские цитаты&lt;/span&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</string>
    </property>
   </widget>
   <widget class="QListWidget" name="today_list">
    <property name="geometry">
     <rect>
      <x>280</x>
      <y>110</y>
      <width>241</width>
      <height>381</height>
     </rect>
    </property>
   </widget>
   <widget class="QPushButton" name="plus_btn">
    <property name="geometry">
     <rect>
      <x>370</x>
      <y>500</y>
      <width>61</width>
      <height>61</height>
     </rect>
    </property>
    <property name="font">
     <font>
      <pointsize>48</pointsize>
     </font>
    </property>
    <property name="autoFillBackground">
     <bool>false</bool>
    </property>
    <property name="text">
     <string>+</string>
    </property>
   </widget>
   <widget class="QLabel" name="label_5">
    <property name="geometry">
     <rect>
      <x>330</x>
      <y>120</y>
      <width>141</width>
      <height>16</height>
     </rect>
    </property>
    <property name="font">
     <font>
      <pointsize>12</pointsize>
     </font>
    </property>
    <property name="text">
     <string>Задачи на сегодня</string>
    </property>
   </widget>
   <widget class="QLabel" name="date">
    <property name="geometry">
     <rect>
      <x>380</x>
      <y>140</y>
      <width>31</width>
      <height>16</height>
     </rect>
    </property>
    <property name="text">
     <string>(дата)</string>
    </property>
   </widget>
  </widget>
  <widget class="QMenuBar" name="menubar">
   <property name="geometry">
    <rect>
     <x>0</x>
     <y>0</y>
     <width>800</width>
     <height>22</height>
    </rect>
   </property>
  </widget>
  <widget class="QStatusBar" name="statusbar"/>
 </widget>
 <resources/>
 <connections/>
</ui>

'''

class OmniTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(StringIO(f), self)
        self.setFixedHeight(615)
        self.setFixedWidth(800)
        self.setWindowTitle('OmniTracker')

        # -------------Создание меню---------------
        self.menu_bar = QMenuBar()

        self.main_menu = self.menu_bar.addMenu('Главная панель')
        self.todo_menu = self.menu_bar.addMenu('Задачник')
        self.diary_menu = self.menu_bar.addMenu('Ежедневник')
        self.schedule = self

        self.main_open()

    def main_open(self):
        ...

if __name__ == '__main__':
    app = QApplication(sys.argv)
    om = OmniTracker()
    om.show()
    sys.exit(app.exec())