import math

import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
from PIL import Image, ImageDraw
import os
import sys


class ImagePanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.image = wx.Image(5, 5)
        self.image.SetData(Image.new('RGB', (5, 5), color='black').tobytes())
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        if hasattr(self, 'image'):
            panel_width, panel_height = self.GetSize()
            image_width, image_height = self.image.GetSize()
            # 计算绘制图像的左上角坐标，使其位于面板的中心
            x = (panel_width - image_width) // 2
            y = (panel_height - image_height) // 2
            dc.DrawBitmap(self.image.ConvertToBitmap(), x, y)


class MyListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.LC_REPORT):
        super(MyListCtrl, self).__init__(parent, id, pos, size, style|wx.BORDER_SIMPLE)
        ListCtrlAutoWidthMixin.__init__(self)
        self.InsertColumn(0, "Image Files")
        self.image_paths = {}  # 新增字典来存储路径
        self.il = wx.ImageList(16, 16)
        self.idx = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN))
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

    def add_item(self, path):
        index = self.InsertItem(sys.maxsize, os.path.basename(path))
        self.image_paths[index] = path  # 使用字典存储路径
        self.SetItemImage(index, self.idx)

    def clear_item(self):
        self.image_paths = {}
        self.DeleteAllItems()


class ImageComposer(wx.Frame):
    def __init__(self):
        super().__init__(None, title='Image Composer', size=(800, 600))

        icon_size = (1024, 1024)
        background_color = (255, 255, 255, 0)  # 透明背景
        _icon = Image.new('RGBA', icon_size, background_color)
        draw = ImageDraw.Draw(_icon)
        rectangle_color = (0, 0, 0, 255)  # 黑色，不透明
        rectangle_position = (100, 100, 924, 924)  # 左上角坐标 (100, 100)，右下角坐标 (924, 924)
        draw.rectangle(rectangle_position, fill=rectangle_color)
        temp_icon_path = "temp_icon.ico"
        _icon.save(temp_icon_path)
        icon = wx.Icon(temp_icon_path, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        panel = wx.Panel(self)

        self.image_list_ctrl = MyListCtrl(panel)

        self.image_panel = ImagePanel(panel)
        self.image_panel.SetSize(402, 162)
        self.button_panel = wx.Panel(panel)
        self.output_panel = ImagePanel(panel)

        self.button_com = wx.Button(self.button_panel, pos=(5, 0), label='组合')
        self.button_sav = wx.Button(self.button_panel, pos=(5 + self.button_com.GetSize()[0] + 10, 0), label='保存')

        self.button_com.Bind(wx.EVT_BUTTON, self.on_combine_button_click)
        self.button_sav.Bind(wx.EVT_BUTTON, self.on_save_button_click)

        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_sizer.Add(self.image_list_ctrl, 1, wx.ALIGN_TOP | wx.ALL, 5)
        top_sizer.Add(self.image_panel, 1, wx.EXPAND | wx.ALL, 5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(top_sizer, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.button_panel, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.output_panel, 10, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)

        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        open_item = file_menu.Append(wx.ID_OPEN, '&Open', 'Open Images')
        menubar.Append(file_menu, '&File')
        self.SetMenuBar(menubar)
        
        self.Bind(wx.EVT_MENU, self.on_open, open_item)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.image_list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_preview_activated)
        self.image_list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_preview_selected)
        self.Show(True)

    def on_size(self, event):
        # self.combined_and_preview()
        self.image_panel.Refresh()
        event.Skip()

    def on_open(self, event):
        wildcard = "PNG files (*.png)|*.png"
        dialog = wx.FileDialog(self, "Choose a file", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_MULTIPLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.image_list_ctrl.clear_item()
            paths = dialog.GetPaths()
            for path in paths:
                self.image_list_ctrl.add_item(path)
                self.update_preview(None, self.image_panel)  # 刷新预览

    def on_preview_activated(self, event):
        item_index = event.GetIndex()
        if item_index != -1:
            path = self.image_list_ctrl.image_paths.get(item_index)
            if path:
                image = wx.Image(path)
                self.update_preview(image, self.image_panel)

    @staticmethod
    def on_preview_selected(event):
        item_index = event.GetIndex()

    @staticmethod
    def combine_images(images, cols=2, spacing=5):
        images_objects = [Image.open(img_path) for img_path in images]
        widths, heights = zip(*(i.size for i in images_objects))
        print(widths)
        print(heights)

        max_width = max(widths)
        total_width = (max_width + spacing) * cols + spacing
        max_height = max(heights)
        total_height = (max_height + spacing) * ((len(images) + cols - 1) // cols) + spacing
        print(total_height, total_width)
        combined_image = Image.new('RGB', (total_width, total_height), color='black')
        
        x_offset = y_offset = spacing
        for img in images_objects:
            combined_image.paste(img, (x_offset, y_offset))
            x_offset += max_width + spacing
            if x_offset >= total_width - spacing: 
                x_offset = spacing
                y_offset += max_height + spacing
        img = wx.Image(total_width, total_height)
        print(combined_image.size)
        img.SetData(combined_image.tobytes())
        print(img.GetSize())
        return img

    def combined_and_preview(self):
        selected_paths = []
        for item in range(self.image_list_ctrl.GetItemCount()):
            selected_paths.append(self.image_list_ctrl.image_paths[item])
        if selected_paths:
            combined_img = self.combine_images(selected_paths, round(math.sqrt(len(selected_paths))))
            self.update_preview(combined_img, self.output_panel)

    def on_save_button_click(self, event):
        if self.output_panel.image:
            filepath = "saved_image.jpg"
            self.output_panel.image.SaveFile(filepath)
            wx.MessageBox(f"Image saved to {filepath}", "Info", wx.OK | wx.ICON_INFORMATION)

    @staticmethod
    def update_preview(image, panel):
        if image:
            panel.image = image
            panel.Refresh()

    def on_combine_button_click(self, event):
        self.combined_and_preview()


if __name__ == "__main__":
    app = wx.App(False)
    frame = ImageComposer()
    app.MainLoop()
