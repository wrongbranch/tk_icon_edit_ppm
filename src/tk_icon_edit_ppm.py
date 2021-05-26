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

fmthsv = lambda hsv: f'hsv({hsv[0]:5.3f},{hsv[1]:5.3f},{int(hsv[2]):d})'
fmtfg = lambda fg: f'fg{fg}'
fmtbg = lambda bg: f'bg{bg}'

def hsv2rgb(hsv):
  '''hsv: tuple(1.0, 1.0, 1.0) to rgb: tuple(255, 255, 255)'''
  return (np.array(colorsys.hsv_to_rgb(*hsv)) * 255.0).astype(np.uint8)

def rgb2hsv(rgb):
  '''rgb: tuple(255, 255, 255) to hsv: tuple(1.0, 1.0, 1.0)'''
  return colorsys.rgb_to_hsv(*(np.array(rgb).astype(np.float32) / 255.0))

def hue_atan2(y, x):
  '''y, x: (-1.0 to 1.0) to hue: (0.0 to 1.0)'''
  return ((int(180 * np.arctan2(y, x) / np.pi) + 180) % 360) / 360.0

def hsv_atan2(y, x):
  '''y, x: (-1.0 to 1.0) to hsv: tuple(1.0, 1.0, 1.0)'''
  r = np.sqrt(x ** 2 + y ** 2)
  hue = hue_atan2(y, x)
  sat = r if r <= 1.0 else 0.0
  val = 1.0
  return (hue, sat, val)

def reg_yx(hw, shape):
  return (-1.0 + 2.0 * hw[_] / (shape[_] - 1) for _ in range(len(hw)))

class ArrayPix(object):
  def __init__(self, pairs):
    self.imgTk = {}
    for pair in pairs:
      pair[0].bind('<Button-1>', pair[1])
      pair[0].bind('<Button-3>', pair[1])

  def restore_pix(self, tag, pnl, shape, pix, md=Image.LANCZOS): # .NEAREST
    pnl.delete(tag)
    sz = (shape[1], shape[0])
    im = Image.fromarray(pix).resize(sz, md)
    self.imgTk[tag] = ImageTk.PhotoImage(im)
    # pnl.create_image(sz[0] / 2, sz[1] / 2, image=self.imgTk[tag], tag=tag)
    pnl.create_image(0, 0, anchor='nw', image=self.imgTk[tag], tag=tag)

  def create_pix(self, shape, col):
    pix = np.zeros(shape, dtype=np.uint8)
    for h in range(pix.shape[0]):
      for w in range(pix.shape[1]):
        pix[h][w] = col # RGB
    return pix

class ArrayPPM(ArrayPix):
  def __init__(self, pairs):
    super().__init__(pairs)

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

class CircleHSV(ArrayPix):
  def __init__(self, pairs):
    super().__init__(pairs)

  def create_circle(self, shape):
    pix = np.zeros(shape, dtype=np.uint8)
    for h in range(pix.shape[0]):
      for w in range(pix.shape[1]):
        pix[h][w] = hsv2rgb(hsv_atan2(*reg_yx((h, w), pix.shape)))
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

    self.hsv = (0.0, 1.0, 1.0)
    self.fg, self.bg = hsv2rgb(self.hsv), (0, 0, 0)
    self.lblhsv = tk.Label(rt, text=fmthsv(self.hsv), bg='lightgray', font=fnt)
    self.lblhsv.place(x=320, y=22)
    self.lblfg = tk.Label(rt, text=fmtfg(self.fg), bg='lightgray', font=fnt)
    self.lblfg.place(x=440, y=22)
    self.lblbg = tk.Label(rt, text=fmtbg(self.bg), bg='lightgray', font=fnt)
    self.lblbg.place(x=540, y=22)
    self.psp = (14, 14, 3)
    self.fpnl = tk.Canvas(rt, width=self.psp[1], height=self.psp[0], bg='gray')
    self.fpnl.place(x=424, y=22)
    self.bpnl = tk.Canvas(rt, width=self.psp[1], height=self.psp[0], bg='gray')
    self.bpnl.place(x=524, y=22)
    self.fpx = ArrayPix([])
    self.refresh_fpx()
    self.bpx = ArrayPix([])
    self.refresh_bpx()

    self.csp = (256, 256, 3)
    self.cpnl = tk.Canvas(rt, width=self.csp[1], height=self.csp[0], bg='gray')
    self.cpnl.place(x=360, y=40)
    self.bsp = (self.csp[0], 32, 3)
    self.cbar = tk.Canvas(rt, width=self.bsp[1], height=self.bsp[0], bg='gray')
    self.cbar.place(x=320, y=40)
    self.chsv = CircleHSV([(self.cpnl, self.onCPnl), (self.cbar, self.onCBar)])
    self.chsv.restore_pix('hsv', self.cpnl, self.csp,
      self.chsv.create_circle(self.csp))
    self.refresh_chsv_cbar()

    self.shp = (256, 256, 3)
    self.pnl = tk.Canvas(rt, width=self.shp[1], height=self.shp[0], bg='gray')
    self.pnl.place(x=40, y=40)
    self.ppm = ArrayPPM([(self.pnl, self.onPnlClick)])
    self.after(0, self.onReset, None) # set self.pix and self.refresh() ev=None

    btn_reset = tk.Button(rt, text='reset', width=16) # height=25 ?
    btn_reset.bind('<ButtonRelease-1>', self.onReset)
    btn_reset.place(x=516, y=390)
    btn_load = tk.Button(rt, text='load', width=16) # height=25 ?
    btn_load.bind('<ButtonRelease-1>', self.onLoad)
    btn_load.place(x=516, y=420)
    btn_save = tk.Button(rt, text='save', width=16) # height=25 ?
    btn_save.bind('<ButtonRelease-1>', self.onSave)
    btn_save.place(x=516, y=450)

  def refresh_fpx(self):
    self.fpx.restore_pix('fg', self.fpnl, self.psp,
      self.fpx.create_pix(self.psp, self.fg))

  def refresh_bpx(self):
    self.bpx.restore_pix('bg', self.bpnl, self.psp,
      self.bpx.create_pix(self.psp, self.bg))

  def refresh_chsv_cbar(self):
    self.chsv.restore_pix('bar', self.cbar, self.bsp,
      self.chsv.create_bar(self.bsp, hsv2rgb(self.hsv)))

  def onCPnl(self, ev):
    # print(f'CPnl: {ev.num} ({ev.x}, {ev.y})')
    self.hsv = hsv_atan2(*reg_yx((ev.y, ev.x), self.csp))
    self.refresh_chsv_cbar()
    self.lblhsv['text'] = fmthsv(self.hsv)

  def onCBar(self, ev):
    # print(f'CBar: {ev.num} ({ev.x}, {ev.y})')
    rgb = hsv2rgb((self.hsv[0], self.hsv[1], 1.0 - ev.y / self.bsp[0]))
    if ev.num == 1: self.fg = rgb
    elif ev.num == 3: self.bg = rgb
    self.lblfg['text'] = fmtfg(self.fg)
    self.lblbg['text'] = fmtbg(self.bg)
    self.refresh_fpx()
    self.refresh_bpx()

  def refresh(self):
    self.lblw['text'] = f'{self.pix.shape[1]}'
    self.lblh['text'] = f'{self.pix.shape[0]}'
    self.ppm.restore_pix('img', self.pnl, self.shp, self.pix, Image.BOX)

  def onPnlClick(self, ev):
    x = int(self.pix.shape[1] * (ev.x / self.shp[1]))
    y = int(self.pix.shape[0] * (ev.y / self.shp[0]))
    # print(f'PnlClick: {ev.num} ({x}, {y})')
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
