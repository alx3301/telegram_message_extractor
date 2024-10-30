import re
from os import listdir
from asyncio import sleep
from sys import argv, exit
from pyrogram.types import User
from PyQt6 import QtWidgets, uic
from pyrogram import Client, errors
from PyQt6.QtWidgets import QComboBox, QPushButton, QLineEdit, QTextEdit, QApplication


class BaseForm(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.working = 0
        self.start_button: QPushButton = self.findChild(QPushButton, 'start')
        self.stop_button: QPushButton = self.findChild(QPushButton, 'stop')
        self.current_form = None
        self.client: Client = Client
        self.sessions: QComboBox = self.findChild(QComboBox, 'sessions')
        self.next: QPushButton = self.findChild(QPushButton, 'next')
        self.api_id: QLineEdit = self.findChild(QLineEdit, 'api_id')
        self.api_hash: QLineEdit = self.findChild(QLineEdit, 'api_hash')
        self.phone_number: QLineEdit = self.findChild(QLineEdit, 'phone_number')
        self.password: QLineEdit = self.findChild(QLineEdit, 'password')
        self.new_session: QPushButton = self.findChild(QPushButton, 'new_session')
        self.exception_msg: QTextEdit = self.findChild(QTextEdit, 'exception_msg')
        self.okay: QPushButton = self.findChild(QPushButton, 'okay')
        self.target_group: QLineEdit = self.findChild(QLineEdit, 'target_group')
        self.keywords: QTextEdit = self.findChild(QTextEdit, 'keywords')

    def display_form(self, form, hold=False):
        self.current_form = form
        self.current_form.show()
        if not hold:
            self.close()


class ExceptionForm(BaseForm):
    def __init__(self, text):
        super().__init__()
        uic.loadUi('uic/exception.ui', self)
        self.exception_msg.setPlainText(text)
        self.okay.clicked.connect(self.exit)

    def exit(self):
        self.close()


class MainForm(BaseForm):
    def __init__(self, client, session_files):
        super().__init__()
        uic.loadUi('uic/main.ui', self)
        self.client: Client = client
        self.sessions.addItems(session_files)
        self.new_session.clicked.connect(self.new_session_clicked)
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.stop)
        self.stop_button.setDisabled(True)
        self.working = 0
        self.sessions.currentTextChanged.connect(self.current_session_changed)

    def new_session_clicked(self):
        self.display_form(NewSessionForm(), hold=True)

    def start(self):
        if all([self.target_group.text(), self.keywords.toPlainText()]):
            self.working = 1
            self.start_button.setDisabled(True)
            self.stop_button.setEnabled(True)
            self.client.loop.run_until_complete(self.search())

    def stop(self):
        if self.working:
            self.working = 0
            self.start_button.setEnabled(True)
            self.stop_button.setDisabled(True)

    def current_session_changed(self):
        self.client = Client(
            workdir='sessions',
            name=self.sessions.currentText().split('.')[0],
        )

    async def search(self):
        try:
            async with self.client:
                async for message in self.client.get_chat_history(self.target_group.text()):
                    if not self.working:
                        break
                    if message.text:
                        keywords = self.keywords.toPlainText().split(',')
                        for keyword in keywords:
                            pattern = r'\b' + re.escape(keyword.strip()) + r'\b'
                            if re.search(pattern, message.text.lower()):
                                await self.client.forward_messages("me", self.target_group.text(), message.id)
                                break
                    await sleep(0.01)
                    QApplication.processEvents()
        except Exception as e:
            exception_form = ExceptionForm(str(e))
            self.display_form(exception_form)


class NewSessionForm(BaseForm):
    def __init__(self):
        super().__init__()
        uic.loadUi('uic/new_session.ui', self)
        self.next.clicked.connect(self.next_clicked)

    def next_clicked(self):
        if all([self.api_id.text(), self.api_hash.text(), self.phone_number.text(), self.password.text()]):
            confirmation_form = ConfirmationForm()
            self.display_form(confirmation_form)


class ConfirmationForm(BaseForm):
    def __init__(self):
        super().__init__()
        uic.loadUi('uic/confirmation.ui', self)


if __name__ == "__main__":
    app = QtWidgets.QApplication(argv)
    session_files = [f for f in listdir('sessions') if f.endswith('.session')]
    if session_files:
        form = MainForm(
            Client(
                name=session_files[0].split('.')[0],
                workdir='sessions'), session_files
        )
    else:
        form = NewSessionForm()
    form.show()
    exit(app.exec())