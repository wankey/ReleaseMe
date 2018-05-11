# encoding=utf-8
from tkinter import *


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.create_widgets()
        master.title("Release Android APP")

    def create_widgets(self):
        self.helloLabel = Label(self, text='Hello!')
        self.helloLabel.pack()
        self.quitButton = Button(self, text='Quit', command=self.quit)
        self.quitButton.pack()


if __name__ == '__main__':
    app = Application()
    app.mainloop()
