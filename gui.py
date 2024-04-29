# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\aaa.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1119, 884)
        font = QtGui.QFont()
        font.setFamily("黑体")
        font.setPointSize(14)
        font.setBold(False)
        font.setWeight(50)
        Dialog.setFont(font)
        self.input = QtWidgets.QTextEdit(Dialog)
        self.input.setGeometry(QtCore.QRect(40, 60, 561, 512))
        font = QtGui.QFont()
        font.setFamily("黑体")
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.input.setFont(font)
        self.input.viewport().setProperty("cursor", QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self.input.setAutoFormatting(QtWidgets.QTextEdit.AutoAll)
        self.input.setTabChangesFocus(False)
        self.input.setLineWrapColumnOrWidth(5)
        self.input.setTabStopWidth(80)
        self.input.setAcceptRichText(False)
        self.input.setObjectName("input")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(40, 30, 81, 21))
        font = QtGui.QFont()
        font.setFamily("黑体")
        font.setPointSize(18)
        font.setBold(False)
        font.setWeight(50)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.output = QtWidgets.QTextEdit(Dialog)
        self.output.setGeometry(QtCore.QRect(610, 60, 471, 511))
        font = QtGui.QFont()
        font.setFamily("黑体")
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.output.setFont(font)
        self.output.viewport().setProperty("cursor", QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self.output.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.output.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.output.setHtml("<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'黑体\',\'黑体\'; font-size:12pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>")
        self.output.setAcceptRichText(False)
        self.output.setObjectName("output")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(610, 30, 81, 21))
        font = QtGui.QFont()
        font.setFamily("黑体")
        font.setPointSize(18)
        font.setBold(False)
        font.setWeight(50)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.logtext = QtWidgets.QTextEdit(Dialog)
        self.logtext.setGeometry(QtCore.QRect(40, 580, 1041, 201))
        font = QtGui.QFont()
        font.setFamily("黑体")
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.logtext.setFont(font)
        self.logtext.viewport().setProperty("cursor", QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self.logtext.setLineWidth(1)
        self.logtext.setAcceptRichText(False)
        self.logtext.setObjectName("logtext")
        self.run = QtWidgets.QPushButton(Dialog)
        self.run.setGeometry(QtCore.QRect(880, 800, 91, 31))
        self.run.setObjectName("run")
        self.copy = QtWidgets.QPushButton(Dialog)
        self.copy.setGeometry(QtCore.QRect(990, 800, 91, 31))
        self.copy.setObjectName("copy")
        self.paste = QtWidgets.QPushButton(Dialog)
        self.paste.setGeometry(QtCore.QRect(770, 800, 91, 31))
        self.paste.setObjectName("paste")
        self.in_cost = QtWidgets.QLineEdit(Dialog)
        self.in_cost.setGeometry(QtCore.QRect(650, 800, 101, 31))
        self.in_cost.setObjectName("in_cost")
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setGeometry(QtCore.QRect(510, 800, 131, 31))
        self.label_3.setObjectName("label_3")
        self.progressBar = QtWidgets.QProgressBar(Dialog)
        self.progressBar.setGeometry(QtCore.QRect(40, 800, 421, 31))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setText(_translate("Dialog", "输入"))
        self.label_2.setText(_translate("Dialog", "输出"))
        self.logtext.setHtml(_translate("Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'黑体\',\'黑体\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.run.setText(_translate("Dialog", "运行"))
        self.copy.setText(_translate("Dialog", "复制"))
        self.paste.setText(_translate("Dialog", "粘贴"))
        self.label_3.setText(_translate("Dialog", "手动扣款金额："))
