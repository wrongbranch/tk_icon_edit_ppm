#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''tk_icon_edit_ppm
P3: ascii
P6: binary
'''

import sys, os
import colorsys
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import messagebox

PPM_TEST = '_test_p6_16x16.ppm'

def hsv2rgb(hsv):
  '''hsv: tuple(1.0, 1.0, 1.0) to rgb: tuple(255, 255, 255)'''
  return (np.array(colorsys.hsv_to_rgb(*hsv)) * 255.0).astype(np.uint8)

def rgb2hsv(rgb):
  '''rgb: tuple(255, 255, 255) to hsv: tuple(1.0, 1.0, 1.0)'''
  return colorsys.rgb_to_hsv(*(np.array(rgb).astype(np.float32) / 255.0))

class CircleHSV(object):
  def __init__(self):
    self.imgTk = {}

  def restore_pix(self, tag, pnl, shape, pix):
    pnl.delete(tag)
    sz = (shape[1], shape[0])
    im = Image.fromarray(pix).resize(sz, Image.LANCZOS)
    self.imgTk[tag] = ImageTk.PhotoImage(im)
    pnl.create_image(sz[0] / 2, sz[1] / 2, image=self.imgTk[tag], tag=tag)

  def create_circle(self, shape):
    pix = np.zeros(shape, dtype=np.uint8)
    for h in range(pix.shape[0]):
      for w in range(pix.shape[1]):
        x = -1.0 + 2.0 * w / (pix.shape[1] - 1)
        y = -1.0 + 2.0 * h / (pix.shape[0] - 1)
        r = np.sqrt(x ** 2 + y ** 2)
        hue = ((int(180 * np.arctan2(y, x) / np.pi) + 180) % 360) / 360.0
        sat = r if r <= 1.0 else 0.0
        val = 1.0
        pix[h][w] = hsv2rgb((hue, sat, val))
    return pix

  def create_bar(self, shape, col):
    hsv = rgb2hsv(col)
    pix = np.zeros(shape, dtype=np.uint8)
    for h in range(pix.shape[0]):
      hue = hsv[0]
      sat = hsv[1]
      val = 1.0 - h / (pix.shape[0] - 1)
      rgb = hsv2rgb((hue, sat, val))
      for w in range(pix.shape[1]):
        pix[h][w] = rgb
    return pix

class ArrayPPM(object):
  def __init__(self):
    self.imgTk = None

  def restore_image(self, pnl, shape, pix):
    pnl.delete('img')
    sz = (shape[1], shape[0])
    im = Image.fromarray(pix).resize(sz, Image.BOX) # .LANCZOS .NEAREST
    self.imgTk = ImageTk.PhotoImage(im)
    pnl.create_image(sz[0] / 2, sz[1] / 2, image=self.imgTk, tag='img')

  def load_dummy(self, shape):
    pix = np.zeros(shape, dtype=np.uint8)
    for h in range(pix.shape[0]):
      for w in range(pix.shape[1]):
        pix[h][w] = (h * 16, w * 16, 255 - h * w) # RGB
    return pix

  def load_PPM(self, fn):
    pix = None
    with open(fn, 'rb') as ppm:
      readl = lambda fp: fp.readline().rstrip().decode('utf-8')
      pfmt = readl(ppm)
      w, h = tuple(map(int, readl(ppm).split(' ')))
      maxv = int(readl(ppm))
      print(f'{pfmt:s} ({w:d}, {h:d}) {maxv:d}')
      if pfmt != 'P6': return pix
      pix = np.ndarray((h, w, 3), dtype=np.uint8, buffer=ppm.read()).copy()
    return pix

  def save_PPM(self, fn, pix):
    with open(fn, 'wb') as ppm:
      header = f'P6\n{pix.shape[1]:d} {pix.shape[0]:d}\n255\n'
      ppm.write(header.encode('utf-8'))
      ppm.write(pix.ravel())
    print(f'save: [{fn}]')

class IconEditPPM(tk.Frame):
  def __init__(self, rt, fn):
    super().__init__(rt)
    rt.title('tk_icon_edit_ppm')
    rt.geometry('640x480+160+120')
    rt['bg'] = 'lightgray' # rt.configure(bg='lightgray')

    fnt = ('Arial', 9)
    self.lblfn = tk.Label(rt, text=fn, bg='lightgray', font=fnt)
    self.lblfn.place(x=8, y=4)
    self.lblw = tk.Label(rt, text='16', bg='lightgray', font=fnt)
    self.lblw.place(x=40, y=22)
    self.lblh = tk.Label(rt, text='16', bg='lightgray', font=fnt)
    self.lblh.place(x=8, y=40)

    self.fg, self.bg = (255, 0, 255), (32, 32, 32)
    self.csp = (256, 256, 3)
    self.cpnl = tk.Canvas(rt, width=self.csp[1], height=self.csp[0], bg='gray')
    self.cpnl.place(x=360, y=40)
    self.bsp = (self.csp[0], 32, 3)
    self.cbar = tk.Canvas(rt, width=self.bsp[1], height=self.bsp[0], bg='gray')
    self.cbar.place(x=320, y=40)
    self.chsv = CircleHSV()
    self.chsv.restore_pix('hsv', self.cpnl, self.csp,
      self.chsv.create_circle(self.csp))
    self.chsv.restore_pix('bar', self.cbar, self.bsp,
      self.chsv.create_bar(self.bsp, self.fg))

    self.shp = (256, 256, 3)
    self.pnl = tk.Canvas(rt, width=self.shp[1], height=self.shp[0], bg='gray')
    self.pnl.place(x=40, y=40)
    self.ppm = ArrayPPM()
    self.after(0, self.onReset, None) # set self.pix and self.refresh() ev=None

    self.pnl.bind('<Button-1>', self.onClick)
    self.pnl.bind('<Button-3>', self.onClick)

    btn_reset = tk.Button(rt, text='reset', width=16) # height=25 ?
    btn_reset.bind('<ButtonRelease-1>', self.onReset)
    btn_reset.place(x=516, y=390)
    btn_load = tk.Button(rt, text='load', width=16) # height=25 ?
    btn_load.bind('<ButtonRelease-1>', self.onLoad)
    btn_load.place(x=516, y=420)
    btn_save = tk.Button(rt, text='save', width=16) # height=25 ?
    btn_save.bind('<ButtonRelease-1>', self.onSave)
    btn_save.place(x=516, y=450)

  def refresh(self):
    self.lblw['text'] = f'{self.pix.shape[1]}'
    self.lblh['text'] = f'{self.pix.shape[0]}'
    self.ppm.restore_image(self.pnl, self.shp, self.pix)

  def onClick(self, ev):
    x = int(self.pix.shape[1] * (ev.x / self.shp[1]))
    y = int(self.pix.shape[0] * (ev.y / self.shp[0]))
    print(f'{ev.num} ({x}, {y})')
    if x >= self.pix.shape[1] or y >= self.pix.shape[0]: return
    if ev.num == 1: self.pix[y][x] = self.fg
    elif ev.num == 3: self.pix[y][x] = self.bg
    self.refresh()

  def onReset(self, ev):
    self.pix = self.ppm.load_dummy((16, 16, 3))
    self.refresh()

  def onLoad(self, ev):
    ft = [('P6 PPM', '*.ppm')]
    fp = filedialog.askopenfilename(filetypes=ft, initialdir='.')
    if not len(fp): return
    pix = self.ppm.load_PPM(fp)
    if pix is None:
      # return self.onReset(ev)
      messagebox.showinfo('load_PPM', f'only support P6 format\n[{fp}]')
    else:
      self.pix = pix
      self.lblfn['text'] = os.path.basename(fp)
    self.refresh()

  def onSave(self, ev):
    self.ppm.save_PPM(self.lblfn['text'], self.pix)

def tk_icon_edit_ppm(fn):
  rt = tk.Tk()
  app = IconEditPPM(rt, fn)
  app.mainloop()

if __name__ == '__main__':
  tk_icon_edit_ppm(PPM_TEST)
