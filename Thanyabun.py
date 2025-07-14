import os
import pandas as pd
import seaborn as sns
import serial.tools.list_ports
import matplotlib.pyplot as plt
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt

console = Console()
sns.set_style({'font.family': 'Times New Roman'})

class detectSerial:
    def __init__(self):
        self.serialList = []

    def get_serial_list(self):
        for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
            self.serialList.append(port)
        if len(self.serialList) > 1:
            console.print("Serial ports found:", style="bold green")
            for i in range(len(self.serialList)):
                console.print(str(i + 1) + ": " + self.serialList[i])
            return Prompt.ask("[bold cyan]Select serial port[/bold cyan] ")
        elif len(self.serialList) == 1:
            return self.serialList[0]
        else:
            console.print("No serial ports found.", style="bold red")
            exit()

class ReadLine:
    def __init__(self, s):
        self.buf = bytearray()
        self.s = s

    def readline(self):
        i = self.buf.find(b"\n")
        if i >= 0:
            r = self.buf[:i+1]
            self.buf = self.buf[i+1:]
            return r
        while True:
            i = max(1, min(2048, self.s.in_waiting))
            data = self.s.read(i)
            i = data.find(b"\n")
            if i >= 0:
                r = self.buf + data[:i+1]
                self.buf[0:] = data[i+1:]
                return r
            else:
                self.buf.extend(data)

class plot:
    def __init__(self, data, timeNow, name, roundLoop):
        self.data = data
        self.time = int(datetime.timestamp(timeNow))
        self.roundLoop = roundLoop
        self.address = "./data/" + name + "/images/" + str(self.time) + str(self.roundLoop) + ".png"

    def processPlot(self):
        frame = [float(x) for x in self.data.split(',')]
        frame2D = []
        for h in range(24):
            frame2D.append([])
            for w in range(32):
                t = frame[h * 32 + w]
                frame2D[h].append(t)
        sns.heatmap(frame2D, annot=True, cmap="coolwarm", linewidths=.1, annot_kws={"size":6}, yticklabels=False, xticklabels=False, vmin=25, vmax=30)
        plt.title("Heatmap of MLX90640 data: " + str(self.time) + str(self.roundLoop))
        plt.savefig(self.address)
        plt.close()

class csvWrite:
    def __init__(self, data, timeNow, address):
        self.data = data
        self.timeNow = pd.Timestamp(timeNow).strftime('%Y-%m-%d %X')
        self.address = address

    def processRaw(self):
        ls = [self.timeNow]
        for data in self.data.split(','):
            ls.append(float(data.strip()))

        with open(self.address, 'a') as f:
            for item in ls:
                f.write("%s," % item)
            f.write("\n")
        # frame = [float(x) for x in self.data.split(',')]
        # df = pd.DataFrame([self.timeNow, frame])
        # df.T.to_csv(self.address, mode="a", header=False, index=False)


    def processCount(self):
        a = 0
        b = 0
        c = 0
        d = 0
        e = 0
        f = 0
        g = 0
        h = 0
        error = 0
        total = 0
        for i in self.data.split(','):
            count = float(i)
            if count >= 38 and count < 40:
                a += 1
            elif count >= 36 and count < 38:
                b += 1
            elif count >= 34 and count < 36:
                c += 1
            elif count >= 32 and count < 34:
                d += 1
            elif count >= 30 and count < 32:
                e += 1
            elif count >= 28 and count < 30:
                f += 1
            elif count >= 26 and count < 28:
                g += 1
            elif count >= 24 and count < 26:
                h += 1
            else:
                error += 1
            total += 1
        df = pd.DataFrame([[a, b, c, d, e, f, g, h, error, total]])
        df.to_csv(self.address, mode="a", header=False, index=False, sep="\t")

class scraping:
    def __init__(self):
        self.port = detectSerial().get_serial_list()

    def process(self):
        serialRead = ReadLine(serial.Serial(self.port, 115200))
        while True:
            name = Prompt.ask("[bold cyan]Enter name of file[/bold cyan] ")
            if name in os.listdir("data"):
                console.print("File already exists.", style="bold red")
                continue
            else:
                os.mkdir("./data/" + name)
                os.mkdir("./data/" + name + "/images")
                df = pd.DataFrame([["38-39", "36-37", "34-35", "32-33", "30-31", "28-29", "26-27", "24-25", "Error", "Total"]])
                df.to_csv("./data/" + name + "/count.csv", mode="a", header=False, index=False, sep="\t")
                break
        number = int(Prompt.ask("[bold cyan]Enter number of frames[/bold cyan] [bold green][DEFAULT[/bold green] [bold red]1000[/bold red] [bold green]FRAME][/bold green] ", default=1000))
        roundLoop = 1
        i=0
        with console.status("[bold cyan]Scraping on tasks...", spinner="bouncingBar") as status:    
            while (i <= number):
                try:
                    data = str(serialRead.readline())
                    data = data.replace("bytearray(b'[", "")
                    data = data.replace("]\\r\\n')", "")
                    timeNow = datetime.now()
                    plot(data, timeNow, name, roundLoop).processPlot()
                    roundLoop += 1
                    csvWrite(data, timeNow, address="./data/" + name + "/raw.csv").processRaw()
                    csvWrite(data, timeNow, address="./data/" + name + "/count.csv").processCount()
                    i += 1 
                    console.log("Frame [green]" + str(i) + "[/green] of [bold green]" + str(number) + "[/bold green] processed.")
                except:
                    continue

if __name__ == '__main__':
    try:
        scraping().process()
    except:
        console.print("Error", style="bold red")
        scraping().process()