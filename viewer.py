from tkinter import *
from random import randint

class Balls:

    def __init__(self, canvas):
        self.canvas = canvas
        self.screenWidth = canvas.winfo_screenwidth()
        self.screenHeight = canvas.winfo_screenheight()
        self.randValues()
        self.createBall()

    def randValues(self):
        self.radius = randint(50, 100)
        self.center_x = randint(self.radius, self.screenWidth - self.radius)
        self.center_y = randint(self.radius, self.screenHeight - self.radius)

    def createBall(self):
        self.ball = self.canvas.create_oval(
            self.center_x - self.radius, self.center_y - self.radius,
            self.center_x + self.radius, self.center_y + self.radius,
            fill="red")

class Screen:

    def __init__(self):
        self.root = Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.canvas = Canvas(self.root)
        self.canvas.pack(expand=1, fill="both")
        Balls(self.canvas)
        self.root.mainloop()

Screen()