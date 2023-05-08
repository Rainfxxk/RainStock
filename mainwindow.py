import sys
import threading

from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt5.QtGui import QPainter, QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets
import mplfinance as mplf
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd
import database
from stock import Stock

MousePos = {
    'NONE': 0,
    'LEFT': 1,
    'TOP': 2,
    'RIGHT': 4,
    'BOTTOM': 8,
    'TOP_LEFT': 3,
    'TOP_RIGHT': 6,
    'BOTTOM_LEFT': 9,
    'BOTTOM_RIGHT': 12
}


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('img/stock.png'))
        # 处理鼠标点击，移动事件
        self.setMouseTracking(True)
        self.start_x = None
        self.start_y = None
        self.mouse_pressed = False
        self.mouse_state = MousePos['NONE']
        # 隐藏窗体标题栏，设置背景透明
        self.setWindowFlags(Qt.FramelessWindowHint)  # 隐藏边框并在其他边框之上
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置背景透明
        self.setMinimumSize(1000, 750)

        # 设置窗体主界面
        self.baseLayout = QVBoxLayout()
        self.setLayout(self.baseLayout)
        self.baseLayout.setContentsMargins(10, 10, 10, 10)
        self.centralWidget = QWidget(self)
        self.centralWidget.setObjectName('centralWidget')
        self.centralWidget.setStyleSheet('#centralWidget'
                                         '{background-color: rgba(255, 255, 255, 0);'
                                         'border-radius: 5px}')
        self.baseLayout.addWidget(self.centralWidget)

        # 设置窗体阴影
        self.effect_shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.effect_shadow.setOffset(0, 0)  # 偏移
        self.effect_shadow.setBlurRadius(15)  # 阴影半径
        self.effect_shadow.setColor(Qt.black)  # 阴影颜色
        self.centralWidget.setGraphicsEffect(self.effect_shadow)  # 将设置套用到widget窗口中

        self.centralLayout = QHBoxLayout(self.centralWidget)
        self.centralLayout.setSpacing(0)
        self.centralLayout.setContentsMargins(0, 0, 0, 0)

        # 设置侧边栏
        self.sideBar = SideBar(self)
        self.sideBar.setStyleSheet('SideBar'
                                   '{background-color: rgba(51, 199, 236, 255);'
                                   'border-top-left-radius: 5px;'
                                   'border-bottom-left-radius: 5px}')
        self.addButton = QPushButton('添加股票')
        self.addButton.setFixedSize(80, 30)
        self.addButton.setStyleSheet('QPushButton{background-color:none;'
                                     'color:white;'
                                     'font: 9pt "Microsoft YaHei UI";'
                                     'border: 1px, solid, black;'
                                     'border-radius: 5px}'
                                     'QPushButton:hover{'
                                     'background-color:white;'
                                     'color:grey}'
                                     'QPushButton:pressed{'
                                     'background-color: rgb(200, 200, 200);'
                                     'color:black}')
        self.addButton.clicked.connect(self.showAddDialog)
        self.sideBar.layout.addWidget(self.addButton, 1, alignment=Qt.AlignCenter)
        self.centralLayout.addWidget(self.sideBar, 1)

        self.mainWidget = QWidget()
        QPushButton(self.mainWidget)
        self.mainWidget.setStyleSheet('background-color: rgba(239, 246, 249, 255);'
                                      'border-top-right-radius: 5px;'
                                      'border-bottom-right-radius: 5px}'
                                      )
        self.centralLayout.addWidget(self.mainWidget, 3)

        self.mainLayout = QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(0, 0, 0, 40)
        # 设置标题栏
        self.titleBar = QWidget()
        self.titleBar.setFixedHeight(40)
        self.titleLayout = QHBoxLayout()
        self.titleLayout.setContentsMargins(0, 0, 0, 0)
        self.titleBar.setLayout(self.titleLayout)
        self.mainLayout.addWidget(self.titleBar, 1, alignment=Qt.AlignTop)
        # 关闭，最大化，隐藏窗口按钮
        self.titleLayout.addStretch(12)
        self.minButton = QPushButton()
        self.minButton.setIcon(QIcon('img/min.png'))
        self.minButton.setIconSize(QSize(20, 20))
        self.minButton.setFixedSize(40, 40)
        self.minButton.setStyleSheet('QPushButton:hover{background-color: rgb(200, 200, 200);border-radius:none}')
        self.minButton.clicked.connect(self.showMinimized)
        self.titleLayout.addWidget(self.minButton, 1, alignment=Qt.AlignRight)
        self.maxButton = QPushButton()
        self.maxButton.setIcon(QIcon('img/max.png'))
        self.maxButton.setIconSize(QSize(20, 20))
        self.maxButton.setFixedSize(40, 40)
        self.maxButton.setStyleSheet('QPushButton:hover{background-color: rgb(200, 200, 200);border-radius:none}')
        self.maxButton.clicked.connect(self.showMaximized)
        self.titleLayout.addWidget(self.maxButton, 1, alignment=Qt.AlignRight)
        self.closeButton = QPushButton()
        self.closeButton.setIcon(QIcon('img/close.png'))
        self.closeButton.setIconSize(QSize(20, 20))
        self.closeButton.setFixedSize(40, 40)
        self.closeButton.setStyleSheet('QPushButton:hover{background-color: rgb(210, 0, 0);'
                                       'border-top-right-radius:5px;'
                                       'border-bottom-right-radius:nonw}')
        self.closeButton.clicked.connect(self.close)
        self.titleLayout.addWidget(self.closeButton, 1, alignment=Qt.AlignRight)
        self.loadStockButton();

        # 设置主展示模块
        self.data = None
        self.showWidget = ShowWidget()
        self.mainLayout.addWidget(self.showWidget, 5)
        self.sideBar.clicked.connect(self.updateData)

        # 添加弹窗
        self.addDialog = AddDialog()
        self.addDialog.submitButton.clicked.connect(self.addStock)

    def updateData(self, id):
        if id == -1:
            if self.showWidget.selected == 0:
                self.showWidget.tableButtonSelected()
            elif self.showWidget.selected == 1:
                self.showWidget.kLineButtonSelected()
            self.showWidget.deleteWidget()
            return

        result = database.executesql('select date, `open`, `close` , max , min, rate ,`change` ,volume ,turnover ,amplitude ,tunoverrate  '
                                     'from data where id = %(id)s order by date desc', id=id)
        print(result)
        self.showWidget.updateDate(result)


    def loadStockButton(self):
        result = database.executesql('select * from company')
        if not result:
            self.sideBar.addEmptyLabel()
        else:
            for row in result:
                self.sideBar.isnodata = True
                self.sideBar.addbutton(StockButton(id =row[0], text=row[1]))


    def showAddDialog(self):
        self.addDialog.show()

    def addStock(self):
        print(self.sideBar.isnodata)
        if not self.sideBar.isnodata:
            self.sideBar.deleteEmptyLabel()
        url = self.addDialog.urlInputLine.input.text();
        name = self.addDialog.nameInputLine.input.text();
        stock = None
        if name == '':
            stock = Stock(url)
        else:
            stock = Stock(url)
            stock.name = name
        result = database.executesql('insert into company values (null, %(company)s, %(url)s)', company=stock.name, url=stock.url)
        result = database.executesql('select id from company where companyName = %(company)s', company=stock.name)
        id = result[0][0]
        self.sideBar.addbutton(StockButton(id, stock.name))
        for row in stock.data:
            database.executesql('insert into data values(%(id)s, %(date)s, %(open)s, %(close)s, %(max)s, %(min)s,'
                                '%(rate)s, %(change)s, %(volume)s, %(turnover)s, %(amplitude)s, %(tunoverrate)s)',
                                id=id, date=row[0], open=row[1], close=row[2], max=row[3], min=row[4], rate=row[5],
                                change=row[6], volume=row[7], turnover=row[8], amplitude=row[9], tunoverrate=row[10])
        self.addDialog.cancel()

    def mousePressEvent(self, QMouseEvent):
        if QMouseEvent.button() == Qt.LeftButton:
            super().mousePressEvent(QMouseEvent)
            self.start_x = QMouseEvent.globalX()
            self.start_y = QMouseEvent.globalY()
            self.mouse_pressed = True

    def mouseReleaseEvent(self, QMouseEvent):
        self.unsetCursor()
        self.start_x = None
        self.start_y = None
        self.mouse_pressed = False

    def mouseMoveEvent(self, QMouseEvent):
        if QMouseEvent.buttons() == Qt.NoButton:
            self.mouse_pressed = False
        if not self.mouse_pressed:
            self.mouse_state = MousePos['NONE']
            if not self.isMaximized() and abs(QMouseEvent.globalX() - self.centralWidget.pos().x()) < 5:
                self.mouse_state += MousePos['LEFT']
            elif not self.isMaximized() and abs(QMouseEvent.globalX() - self.centralWidget.pos().x() - self.width()) < 5:
                self.mouse_state += MousePos['RIGHT']
            if not self.isMaximized() and abs(QMouseEvent.globalY() - self.centralWidget.pos().y()) < 5:
                self.mouse_state += MousePos['TOP']
            elif not self.isMaximized() and abs(QMouseEvent.globalY() - self.centralWidget.pos().y() - self.height()) < 5:
                self.mouse_state += MousePos["BOTTOM"]
            if self.mouse_state == MousePos["LEFT"] or self.mouse_state == MousePos["RIGHT"]:
                self.setCursor(Qt.SizeHorCursor)
            elif self.mouse_state == MousePos['TOP'] or self.mouse_state == MousePos["BOTTOM"]:
                self.setCursor(Qt.SizeVerCursor)
            elif self.mouse_state == MousePos['TOP_LEFT'] or self.mouse_state == MousePos['BOTTOM_RIGHT']:
                self.setCursor(Qt.SizeFDiagCursor)
            elif self.mouse_state == MousePos['TOP_RIGHT'] or self.mouse_state == MousePos['BOTTOM_LEFT']:
                self.setCursor(Qt.SizeBDiagCursor)
            else:
                self.unsetCursor()

        else:
            if self.mouse_state == 0:
                if not self.isMaximized():
                    move_x = QMouseEvent.globalX() - self.start_x
                    move_y = QMouseEvent.globalY() - self.start_y
                    self.move(self.x() + move_x, self.y() + move_y)
            else:
                if self.mouse_state & MousePos['LEFT']:
                    self.move(self.x() + QMouseEvent.globalX() - self.start_x, self.y())
                    self.resize(self.width() - QMouseEvent.globalX() + self.start_x, self.height())
                if self.mouse_state & MousePos['TOP']:
                    self.move(self.x(), self.y() + QMouseEvent.globalY() - self.start_y)
                    self.resize(self.width(), self.height() - QMouseEvent.globalY() + self.start_y)
                if self.mouse_state & MousePos['RIGHT']:
                    self.resize(self.width() + QMouseEvent.globalX() - self.start_x, self.height())
                if self.mouse_state & MousePos['BOTTOM']:
                    self.resize(self.width(), self.height() + QMouseEvent.globalY() - self.start_y)
            self.start_x = QMouseEvent.globalX()
            self.start_y = QMouseEvent.globalY()


class ShowWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.data = None
        self.selected = None
        # 设置基础布局
        self.baseLayout = QVBoxLayout()
        self.baseLayout.setContentsMargins(40, 0, 40, 0)
        self.baseLayout.setSpacing(0)
        self.setLayout(self.baseLayout)
        # 设置按钮视窗、布局
        self.buttonWidget = QWidget()
        self.buttonWidget.setFixedSize(200, 40)
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setSpacing(0)
        self.buttonWidget.setLayout(self.buttonLayout)
        self.baseLayout.addWidget(self.buttonWidget, 1)
        self.tableButton = QPushButton('Table')
        self.tableButton.setStyleSheet('font:12pt, "Adobe 黑体 Std";'
                                       'background-color: rgb(197, 211, 215);'
                                       'border: none;'
                                       'border-radius: none')
        self.tableButton.setFixedSize(100, 40)
        self.tableButton.clicked.connect(self.tableButtonSelected)
        self.buttonLayout.addWidget(self.tableButton, 1, alignment=Qt.AlignLeft)
        self.kLineButton = QPushButton('K-Line')
        self.kLineButton.setStyleSheet('font:12pt, "Adobe 黑体 Std";'
                                       'background-color: rgb(197, 211, 215);'
                                       'border: none;'
                                       'border-radius: none')
        self.kLineButton.setFixedSize(100, 40)
        self.kLineButton.clicked.connect(self.kLineButtonSelected)
        self.buttonLayout.addWidget(self.kLineButton, 1, alignment=Qt.AlignLeft)
        self.buttonLayout.addStretch(4)
        #设置数据展示视窗
        self.showWidget = QWidget()
        self.showWidget.setStyleSheet('background-color: rgb(255, 255, 255)')
        self.showLayout = QStackedLayout()
        self.showLayout.setContentsMargins(0, 0, 0, 0)
        self.showLayout.setSpacing(0)
        self.showWidget.setLayout(self.showLayout)
        self.emptyWidget = QWidget()
        self.showLayout.addWidget(self.emptyWidget)
        self.tableWidget = None
        self.tableModel = None
        self.kLineWidget = None
        self.baseLayout.addWidget(self.showWidget, 10)

    def updateDate(self, data):
        if self.data is not None:
            self.tableWidget.deleteLater()
            self.tableModel.deleteLater()
            self.kLineWidget.deleteLater()
        self.data = data
        self.tableWidget = QTreeView()
        self.tableModel = QStandardItemModel()
        self.tableModel.setHorizontalHeaderLabels(['日期', '开盘', '收盘', '最高', '最低',
                                                   '涨跌幅', '涨跌额', '成交量', '成交额', '振幅', '换手率'])
        for row_num, row in enumerate(data):
            for col_num, col in enumerate(row):
                if col_num == 0:
                    continue
                item = QStandardItem(str(col))
                item.setEditable(False)
                self.tableModel.setItem(row_num, col_num - 1, item)
        self.tableWidget.header().setDefaultAlignment(Qt.AlignCenter)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setModel(self.tableModel)
        self.showLayout.addWidget(self.tableWidget)
        data_df = pd.DataFrame(data, columns=['Date', 'Open', 'Close', 'High', 'Low', 'Rate', 'Change',
                                              'Volume', 'Turnover', 'Amplitude', 'TurnoverRate'])
        data_df.index = pd.DatetimeIndex(data_df['Date'])
        fig, axlist = mplf.plot(data_df[0:30], type='candle', mav=(2, 5, 10), volume=True, returnfig=True)
        self.kLineWidget = FigureCanvas(fig)
        self.showLayout.addWidget(self.kLineWidget)

    def deleteWidget(self):
        del self.data
        self.data = None
        self.tableWidget.deleteLater()
        self.tableModel.deleteLater()
        self.kLineWidget.deleteLater()

    def exchangeWidget(self, index):
        self.showLayout.setCurrentIndex(index)

    def tableButtonSelected(self):
        if self.selected is None:
            self.tableButton.setStyleSheet('font:12pt, "Adobe 黑体 Std";'
                                           'background-color: rgb(255, 255, 255);'
                                           'border: none;'
                                           'border-radius: none')
            self.selected = 0
            self.exchangeWidget(1)
        elif self.selected == 0:
            self.tableButton.setStyleSheet('font:12pt, "Adobe 黑体 Std";'
                                           'background-color: rgb(197, 211, 215);'
                                           'border: none;'
                                           'border-radius: none')
            self.selected = None
            self.exchangeWidget(0)
        elif self.selected == 1:
            self.kLineButton.setStyleSheet('font:12pt, "Adobe 黑体 Std";'
                                           'background-color: rgb(197, 211, 215);'
                                           'border: none;'
                                           'border-radius: none')
            self.tableButton.setStyleSheet('font:12pt, "Adobe 黑体 Std";'
                                           'background-color: rgb(255, 255, 255);'
                                           'border: none;'
                                           'border-radius: none')
            self.selected = 0
            self.exchangeWidget(1)

    def kLineButtonSelected(self):
        if self.selected is None:
            self.kLineButton.setStyleSheet('font:12pt, "Adobe 黑体 Std";'
                                           'background-color: rgb(255, 255, 255);'
                                           'border: none;'
                                           'border-radius: none')
            self.selected = 1
            self.exchangeWidget(2)
        elif self.selected == 1:
            self.kLineButton.setStyleSheet('font:12pt, "Adobe 黑体 Std";'
                                           'background-color: rgb(197, 211, 215);'
                                           'border: none;'
                                           'border-radius: none')
            self.selected = None
            self.exchangeWidget(0)
        elif self.selected == 0:
            self.tableButton.setStyleSheet('font:12pt, "Adobe 黑体 Std";'
                                           'background-color: rgb(197, 211, 215);'
                                           'border: none;'
                                           'border-radius: none')
            self.kLineButton.setStyleSheet('font:12pt, "Adobe 黑体 Std";'
                                           'background-color: rgb(255, 255, 255);'
                                           'border: none;'
                                           'border-radius: none')
            self.selected = 1
            self.exchangeWidget(2)


class InputLine(QWidget):
    def __init__(self, text):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(50, 0, 50, 0)
        self.label = QLabel(text)
        self.label.setStyleSheet('font: 12pt "Microsoft YaHei UI";color:black')
        self.layout.addWidget(self.label,1, alignment=Qt.AlignLeft)
        self.input = QLineEdit()
        self.input.setAlignment(Qt.AlignCenter)
        self.input.setStyleSheet('QLineEdit'
                                 '{border-style: solid;'
                                 'border-width: 0 0 1px 0;'
                                 'border-radius: 0;'
                                 'font: 10pt "Microsoft YaHei UI"}')
        self.layout.addWidget(self.input, 3)


class AddDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet('background-color:white;border-radius:5px')
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.layout)
        self.centralWidget = QWidget(self)
        self.centralWidget.setFixedSize(400, 300)
        self.layout.addWidget(self.centralWidget)
        self.baseLayout = QVBoxLayout()
        self.centralWidget.setLayout(self.baseLayout)
        self.inputWidget = QWidget()
        self.baseLayout.addWidget(self.inputWidget, 2)
        self.inputLayout = QVBoxLayout()
        self.inputWidget.setLayout(self.inputLayout)
        self.urlInputLine = InputLine('URL')
        self.inputLayout.addWidget(self.urlInputLine)
        self.nameInputLine = InputLine('Name')
        self.inputLayout.addWidget(self.nameInputLine)
        self.buttonWidget = QWidget()
        self.baseLayout.addWidget(self.buttonWidget, 1, alignment=Qt.AlignBottom)
        self.buttonLayout = QHBoxLayout()
        self.buttonWidget.setLayout(self.buttonLayout)
        self.submitButton = QPushButton('提交')
        self.submitButton.setStyleSheet('QPushButton'
                                        '{background-color: rgb(35, 188, 232);'
                                        'font: 10pt "Microsoft YaHei UI";'
                                        'color: white;'
                                        'border-radius: 5px}'
                                        'QPushButton:hover'
                                        '{background-color: rgb(0, 143, 204);}'
                                        'QPushButton:pressed'
                                        '{background-color: rgb(0, 143, 204);}')
        self.submitButton.setFixedHeight(40)
        self.buttonLayout.addWidget(self.submitButton, 2)
        self.buttonLayout.addStretch(1)
        self.cancelButton = QPushButton('取消')
        self.cancelButton.setStyleSheet('QPushButton'
                                        '{background-color: rgb(35, 188, 232);'
                                        'font: 10pt "Microsoft YaHei UI";'
                                        'color: white;'
                                        'border-radius: 5px}'
                                        'QPushButton:hover'
                                        '{background-color: rgb(0, 143, 204);}'
                                        'QPushButton:pressed'
                                        '{background-color: rgb(0, 143, 204);}')
        self.cancelButton.setFixedHeight(40)
        self.cancelButton.clicked.connect(self.cancel)
        self.buttonLayout.addWidget(self.cancelButton, 2)
        # 鼠标移动
        self.setMouseTracking(True)
        self.start_x = None
        self.start_y = None
        self.mouse_pressed = False
        # 设置窗体阴影
        self.effect_shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.effect_shadow.setOffset(0, 0)  # 偏移
        self.effect_shadow.setBlurRadius(15)  # 阴影半径
        self.effect_shadow.setColor(Qt.black)  # 阴影颜色
        self.centralWidget.setGraphicsEffect(self.effect_shadow)  # 将设置套用到widget窗口中

    def cancel(self):
        self.urlInputLine.input.setText('')
        self.nameInputLine.input.setText('')
        self.close()

    def mousePressEvent(self, QMouseEvent):
        if QMouseEvent.button() == Qt.LeftButton:
            super().mousePressEvent(QMouseEvent)
            self.start_x = QMouseEvent.globalX()
            self.start_y = QMouseEvent.globalY()
            self.mouse_pressed = True

    def mouseReleaseEvent(self, QMouseEvent):
        self.unsetCursor()
        self.start_x = None
        self.start_y = None
        self.mouse_pressed = False

    def mouseMoveEvent(self, QMouseEvent):
        if QMouseEvent.buttons() == Qt.LeftButton:
            move_x = QMouseEvent.globalX() - self.start_x
            move_y = QMouseEvent.globalY() - self.start_y
            self.move(self.x() + move_x, self.y() + move_y)
            self.start_x = QMouseEvent.globalX()
            self.start_y = QMouseEvent.globalY()


class StockButton(QWidget):
    clicked = pyqtSignal()
    def __init__(self, id, text):
        super().__init__()
        self.id = id
        self.isSelect = False
        self.setAttribute(Qt.WA_StyledBackground)
        self.setFixedHeight(60)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.selectSign = QWidget()
        self.selectSign.setFixedSize(13, 60)
        self.layout.addWidget(self.selectSign, 1, Qt.AlignLeft)
        self.textLabel = QLabel(text)
        self.textLabel.setStyleSheet('font: 15pt "Microsoft YaHei UI";color: rgb(255, 255, 255);')
        self.layout.addWidget(self.textLabel, 2, Qt.AlignCenter)
        self.layout.addStretch(1)

    def mousePressEvent(self, QMouseEvent):
            if QMouseEvent.buttons() == Qt.LeftButton:
                self.isSelect = not self.isSelect
                self.clicked.emit()

    def selected(self):
        self.isSelect = True
        self.setStyleSheet('background-color: rgb(0, 143, 204)')
        self.selectSign.setStyleSheet('background-color: rgba(255, 255, 255, 255)')

    def unselected(self):
        self.isSelect = False
        self.setStyleSheet('background-color: none')
        self.selectSign.setStyleSheet('background-color: rgba(255, 255, 255, 0);border-radius: 8px')


class SideBar(QWidget):
    clicked = pyqtSignal(int)
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setContentsMargins(0, 0, 0, 0)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        menu = QIcon('img/menu.png')
        self.menuButton = QPushButton()
        self.menuButton.setIcon(menu)
        self.menuButton.setIconSize(QSize(30, 30))
        self.menuButton.setFixedSize(50, 50)
        self.menuButton.setStyleSheet('background: none;border: none')
        self.layout.addWidget(self.menuButton, 1, alignment=Qt.AlignLeft)
        self.layout.addStretch(1)
        self.mainWidget = QWidget(self)
        self.mainWidget.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.mainWidget, 11)
        self.mainlayout = QVBoxLayout()
        self.mainlayout.setContentsMargins(0, -1, 0, -1)
        self.mainlayout.setSpacing(1)
        self.mainWidget.setLayout(self.mainlayout)
        self.buttons = []
        self.last = None
        self.isnodata = False

    def addbutton(self, button):
        if not self.isnodata:
            self.isnodata = not self.isnodata
        self.mainlayout.addWidget(button, 0, alignment=Qt.AlignTop)
        self.buttons.append(button)
        button.clicked.connect(self.buttonclicked)

    def addEmptyLabel(self):
        self.nodataLabel = QLabel('没有数据？')
        self.nodataLabel.setStyleSheet('font: 9pt "Microsoft YaHei UI"; color: white;')
        self.mainlayout.addWidget(self.nodataLabel, alignment=Qt.AlignBottom | Qt.AlignCenter)

    def deleteEmptyLabel(self):
        self.nodataLabel.deleteLater()

    def buttonclicked(self):
        temp = None
        if self.last is not None:
            self.buttons[self.last].unselected()
        for index in range(len(self.buttons)):
            if self.buttons[index].isSelect:
                temp = index
                self.buttons[index].selected()
                self.clicked.emit(self.buttons[index].id)
        if temp is not None:
            self.last = temp
        else:
            self.last = None
            self.clicked.emit(-1)
