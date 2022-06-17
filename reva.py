from bluepy.btle import Peripheral, DefaultDelegate, BTLEException
import time
import binascii
import struct
from tkinter import *
from PIL import ImageTk, Image

bleDevice = "E0:9F:2A:E4:99:14"

window = Tk()
window.geometry("480x800")
window.overrideredirect(1)
window.configure(background="black")

blank_canvas = Canvas(window, width=100, height=40, highlightthickness="0", bg="#000000")
blank_canvas.pack()

#add reva image
revaimg_canvas = Canvas(window, width=300, height=180, highlightthickness="0", bg="#000000")
revaimg_canvas.pack()

revaimg = ImageTk.PhotoImage(Image.open("graphics/reva_small.png"))
revaimg_canvas.create_image(0, 0, anchor="nw", image=revaimg)

current = Label(window, text="Current", font=("Helvetica", 28, "bold"), bg="#000000", fg="#ffffff")
current.pack(pady=10)

soc = Canvas(window, width = 480, height = 120, bg="black", highlightthickness="0")
soc.pack()

vAhFrame = Frame(window, width=300, height=20, borderwidth=0, bg="#000000")

totalVolts = Label(vAhFrame, text="Voltage", justify=LEFT, font=("Helvetica", 20, "bold"), bg="#000000", fg="#ffffff")
totalVolts.pack(side=LEFT)

remainingCapacity = Label(vAhFrame, text="Remaining", justify=RIGHT, font=("Helvetica", 20, "bold"), bg="#000000", fg="#ffffff")
remainingCapacity.pack(side=RIGHT)

vAhFrame.pack(padx=80, pady=0, fill="both")

gear = Label(window, text="BOOST", font=("Helvetica", 36, "bold"), bg="#000000", fg="#00ffee")
gear.pack(pady=30)

miscFrame = Frame(window, width=480, height=100, borderwidth=2, bg="#000000")
miscFrame.pack(padx=30, pady=0, fill="both")


cellTitle = Label(miscFrame, text="CELL LO - HI (V)", font=("Helvetica", 16), bg="#000000", fg="#ffffff")
cellTitle.place(x=0, y=10, anchor='w')

seperator = Canvas(miscFrame, width=480, height=3, bg="#666666", highlightthickness="0")
seperator.create_line(15,15,300,15)
seperator.place(x=0, y=25)

cellVoltages = Label(miscFrame, text="Cells", font=("Helvetica", 20, "bold"), bg="#000000", fg="#ffffff")
cellVoltages.place(x=0, y=50, anchor='w')

deltaTitle = Label(miscFrame, text="DELTAV", font=("Helvetica", 16), bg="#000000", fg="#ffffff")
deltaTitle.place(x=420, y=10, anchor='e')

delta = Label(miscFrame, text="Delta", font=("Helvetica", 20, "bold"), bg="#000000", fg="#ffffff")
delta.place(x=420, y=50, anchor='e')

temp = Label(miscFrame, text="T", font=("Helvetica", 20, "bold"), bg="#000000", fg="#ffffff")
temp.place(x=0, y=80, anchor='w')


def round_rectangle(x1, y1, x2, y2, radius=25, **kwargs):

    points = [x1+radius, y1,
              x1+radius, y1,
              x2-radius, y1,
              x2-radius, y1,
              x2, y1,
              x2, y1+radius,
              x2, y1+radius,
              x2, y2-radius,
              x2, y2-radius,
              x2, y2,
              x2-radius, y2,
              x2-radius, y2,
              x1+radius, y2,
              x1+radius, y2,
              x1, y2,
              x1, y2-radius,
              x1, y2-radius,
              x1, y1+radius,
              x1, y1+radius,
              x1, y1]

    return soc.create_polygon(points, **kwargs, smooth=True)




try:
    print('attempting to connect')
    bms = Peripheral(bleDevice,addrType="public")
except BTLEException as ex:
    time.sleep(10)
    print('2nd try connect')
    bms = Peripheral(bleDevice,addrType="public")
except BTLEException as ex:
    print('cannot connect')
    exit()
else:
    print('connected ',bleDevice)

global data

class MyDelegate(DefaultDelegate):		# handles notification responses
    def __init__(self):
        DefaultDelegate.__init__(self)
    def handleNotification(self, cHandle, data):
        checkData(data)

bms.setDelegate(MyDelegate())



def checkData(data):
    hex_data = binascii.hexlify(data) 		# Given raw bytes, get an ASCII string representing the hex values
    text_string = hex_data.decode('utf-8')

    if text_string.find('dd03') != -1:
        i = 4  # Unpack into variables, skipping header bytes 0-3
        volts, amps, remain, capacity, cycles, mdate, balance1, balance2 = struct.unpack_from('>HhHHHHHH', data, i)
        volts = volts/100
        remain = remain/100
        amps = amps/100
        totalVolts.configure(text='%sV'%volts)
        remainingCapacity.configure(text='%sAh'%remain)
        current.configure(text='%sA'%amps)
        print(volts)
    elif text_string.find('dd04') != -1:
        global cells1
        i = 4
        cell1, cell2, cell3, cell4, cell5, cell6, cell7, cell8 = struct.unpack_from('>HHHHHHHH', data, i)
        cells1 = [cell1, cell2, cell3, cell4, cell5, cell6, cell7, cell8] 	# needed for max, min, delta calculations
        #print(cells1)
    elif text_string.find('77') != -1 and len(text_string) == 38:	 # x04
        i = 0
        cell9, cell10, cell11, cell12, cell13, cell14, cell15, cell16, b77 = struct.unpack_from('>HHHHHHHHB', data, i)
        cells2 = [cell9, cell10, cell11, cell12, cell13, cell14, cell15, cell16]	# adding cells min, max and delta	
        allcells = cells1 + cells2
        cellsmin = min(allcells)
        cellsmax = max(allcells)
        deltaV = (cellsmax-cellsmin)
        cellsmin = cellsmin/1000
        cellsmax = cellsmax/1000
        deltaV = deltaV/1000
        mincell = (str((allcells.index(min(allcells))+1)))
        maxcell = (str((allcells.index(max(allcells))+1)))
        cellVoltages.configure(text='%s (%s) - %s (%s)'%(cellsmin,mincell,cellsmax,maxcell))
        delta.configure(text=deltaV)
    elif text_string.find('77') != -1 and len(text_string) == 32:
        i = 0                          # unpack into variables, ignore end of message byte '77'
        protect,vers,percent,fet,cells,sensors,temp1,temp2,temp3,temp4,b77 = struct.unpack_from('>HBBBBBHHHHB', data, i)
        temp1 = (temp1-2731)/10
        temp2 = (temp2-2731)/10			# fet 0011 = 3 both on ; 0010 = 2 disch on ; 0001 = 1 chrg on ; 0000 = 0 both off
        temp3 = (temp3-2731)/10
        temp.configure(text="%s\xb0C"%temp1)

        #test data
        #percent=87

        #battery color
        fillColor = "#00FF00"
        if(percent <= 40 and percent > 20):
            fillColor = "#FFB700"
        elif(percent <= 20):
            fillColor = "#FF0000"

        if(percent > 99):
            fillHead = "#00FF00"
            percent_x_pos = 157
        elif(percent > 10 and percent <=99):
            fillHead = "#000000"
            percent_x_pos = 180
        else:
            fillHead = "#000000"
            percent_x_pos = 195
        # right coordinate
        x2 = (((396-84)/100)*percent) + 86

        #battery icon and fill up
        soc_border = round_rectangle(80, 10, 400, 100, radius=10, fill="#000000", width=4, outline="#FFFFFF")
        soc_batter_head = round_rectangle(400, 30, 410, 80, radius=8, fill=fillHead, width=4, outline="#FFFFFF")
        soc_mark = round_rectangle(82, 12, x2, 98, radius=0, fill=fillColor)

        #battery percentage
        percent_text = soc.create_text(percent_x_pos + 2, 32, anchor="nw", fill="#000000")
        soc.itemconfig(percent_text, text=("%s%%"%percent), font=("Helvetica", 50, "bold"))
        percent_text = soc.create_text(percent_x_pos, 28, anchor="nw", fill="#ffffff")
        soc.itemconfig(percent_text, text=("%s%%"%percent), font=("Helvetica", 50, "bold"))

while True:
    result = bms.writeCharacteristic(0x15,b'\xdd\xa5\x04\x00\xff\xfc\x77',False)		# write x04 w/o response cell voltages
    bms.waitForNotifications(5)
    result = bms.writeCharacteristic(0x15,b'\xdd\xa5\x03\x00\xff\xfd\x77',False)		# write x03 w/o response cell info
    bms.waitForNotifications(5)
    time.sleep(1)
    window.update()

window.mainloop()
