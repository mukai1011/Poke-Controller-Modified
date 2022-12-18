import cv2
import os
import sys
import tkinter.ttk as ttk
import tkinter.messagebox as tkmsg
from logging import StreamHandler, getLogger, DEBUG, NullHandler
import subprocess
import platform

import Settings
import Utility as util
from Camera import Camera
from CommandLoader import CommandLoader
from Commands import McuCommandBase, PythonCommandBase, Sender
import PokeConLogger
from Commands.Keys import KeyPress
from GuiAssets import CaptureArea, ControllerGUI
from Keyboard import SwitchKeyboardController

from KeyConfig import PokeKeycon
from LineNotify import Line_Notify
from get_pokestatistics import GetFromHomeGUI

#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
#=#=#=#=#= AUTO-GENERATED #=#=#=#=#=#
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
import pathlib
import tkinter as tk
import pygubu
PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "poke_controller.ui"
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
#=#=#=#=#= /AUTO-GENERATED =#=#=#=#=#
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
from typing import cast

# from get_pokestatistics import GetFromHomeGUI

NAME = "Poke-Controller"
VERSION = "v3.0.2.7.0a Modified"  # based on 1.0-beta3(custom by @dragonite303)

'''
Todo:
・デバッグ用にPoke-Controller本体にコントローラーを接続して動かしたい

・keyboardからHatを動かせないから、Hatを動かせるようにしたい
→モンハンのメニューの選択はHatで選ばれる
---> Done

・画像認識の時の枠を設定でON/OFFできると嬉しい
'''


class PokeControllerApp:
    def __init__(self, master=None):

        self._logger = getLogger(__name__)
        self._logger.addHandler(NullHandler())

        self._logger.setLevel(DEBUG)
        self._logger.propagate = True

        # self.root.resizable(0, 0)
        self.controller = None
        self.poke_treeview = None
        self.keyPress = None
        self.keyboard = None

        self.camera_dic = None

        #=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
        #=#=#=#=#= AUTO-GENERATED #=#=#=#=#=#
        #=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow = cast(tk.Toplevel, builder.get_object("toplevel1", master))
        # Main menu
        _main_menu = builder.get_object("menubar", self.mainwindow)
        self.mainwindow.configure(menu=_main_menu)

        self.camera_id = tk.IntVar()
        self.is_show_realtime = tk.BooleanVar()
        self.fps = tk.StringVar()
        self.show_size = tk.StringVar()
        self.camera_name_fromDLL = tk.StringVar()
        self.com_port = tk.StringVar()
        self.baud_rate = tk.StringVar()
        self.is_show_serial = tk.BooleanVar()
        self.is_use_keyboard = tk.BooleanVar()
        self.is_use_left_stick_mouse = tk.BooleanVar()
        self.is_use_right_stick_mouse = tk.BooleanVar()
        self.py_name = tk.StringVar()
        self.mcu_name = tk.StringVar()
        builder.import_variables(self,
                                 ['camera_id',
                                  'is_show_realtime',
                                  'fps',
                                  'show_size',
                                  'camera_name_fromDLL',
                                  'com_port',
                                  'baud_rate',
                                  'is_show_serial',
                                  'is_use_keyboard',
                                  'is_use_left_stick_mouse',
                                  'is_use_right_stick_mouse',
                                  'py_name',
                                  'mcu_name'])

        builder.connect_callbacks(self)
        #=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
        #=#=#=#=#= /AUTO-GENERATED =#=#=#=#=#
        #=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
        self.mainwindow.title(NAME + ' ' + VERSION)
        # FIXME: Not using on GUI, declared anyway
        self.com_port_name = tk.StringVar()
        # FIXME: Monkey patch
        self.frame_1_2 = cast(ttk.Frame, builder.get_object("frame_1_2", master))
        self.logArea = cast(tk.Text, builder.get_object("logArea", master))
        self.fps_cb = cast(ttk.Combobox, builder.get_object("fps_cb", master))
        self.show_size_cb = cast(ttk.Combobox, builder.get_object("show_size_cb", master))
        self.camera_entry = cast(ttk.Entry, builder.get_object("camera_entry", master))
        self.Camera_Name = cast(ttk.Combobox, builder.get_object("Camera_Name", master))
        self.cb_use_keyboard = cast(ttk.Combobox, builder.get_object("cb_use_keyboard", master))
        self.camera_lf = cast(ttk.Labelframe, builder.get_object("camera_lf", master))
        self.Command_nb = cast(ttk.Notebook, builder.get_object("Command_nb", master))
        self.py_cb = cast(ttk.Combobox, builder.get_object("py_cb", master))
        self.mcu_cb = cast(ttk.Combobox, builder.get_object("mcu_cb", master))
        self.startButton = cast(ttk.Button, builder.get_object("startButton", master))
        self.reloadCommandButton = cast(ttk.Button, builder.get_object("reloadCommandButton", master))

        # 仮置フレームを削除
        self.frame_1_2.destroy()

        # 標準出力をログにリダイレクト
        sys.stdout = StdoutRedirector(self.logArea)
        # load settings file
        self.loadSettings()
        # 各tk変数に設定値をセット(コピペ簡単のため)
        self.is_show_realtime.set(self.settings.is_show_realtime.get())
        self.is_show_serial.set(self.settings.is_show_serial.get())
        self.is_use_keyboard.set(self.settings.is_use_keyboard.get())
        self.fps.set(self.settings.fps.get())
        self.show_size.set(self.settings.show_size.get())
        self.com_port.set(self.settings.com_port.get())
        self.com_port_name.set(self.settings.com_port_name.get())
        self.baud_rate.set(self.settings.baud_rate.get())
        self.camera_id.set(self.settings.camera_id.get())
        # 各コンボボックスを現在の設定値に合わせて表示
        self.fps_cb.current(self.fps_cb['values'].index(self.fps.get()))
        self.show_size_cb.current(
            self.show_size_cb['values'].index(self.show_size.get())
        )

        if platform.system() != 'Linux':
            try:
                self.locateCameraCmbbox()
                self.camera_entry.config(state='disable')
            except:
                # Locate an entry instead whenever dll is not imported successfully
                self.camera_name_fromDLL.set("An error occurred when displaying the camera name in the Win/Mac "
                                             "environment.")
                self._logger.warning("An error occurred when displaying the camera name in the Win/Mac environment.")
                self.Camera_Name.config(state='disable')
        elif platform.system() != 'Linux':
            self.camera_name_fromDLL.set("Linux environment. So that cannot show Camera name.")
            self.Camera_Name.config(state='disable')
            self.cb_use_keyboard.config(state='disable')
            return
        else:
            self.camera_name_fromDLL.set("Unknown environment. Cannot show Camera name.")
            self.Camera_Name.config(state='disable')
        # open up a camera
        self.camera = Camera(self.fps.get())
        self.openCamera()
        # activate serial communication
        self.ser = Sender.Sender(self.is_show_serial)
        self.activateSerial()
        self.activateKeyboard()
        self.preview = CaptureArea(self.camera,
                                   self.fps.get(),
                                   self.is_show_realtime,
                                   self.ser,
                                   self.is_use_left_stick_mouse,
                                   self.is_use_right_stick_mouse,
                                   self.camera_lf,
                                   *list(map(int, self.show_size.get().split("x")))
                                   )
        self.preview.config(cursor='crosshair')
        self.preview.grid(column='0', columnspan='7', row='2', padx='5', pady='5', sticky=tk.NSEW)
        self.loadCommands()

        self.show_size_tmp = self.show_size_cb['values'].index(self.show_size_cb.get())

        self.mainwindow.protocol("WM_DELETE_WINDOW", self.exit)
        self.preview.startCapture()

        # FIXME: Monkey patch - Menubar
        self.line = Line_Notify(self.camera)
        self.key_config = None

    def openCamera(self):
        self.camera.openCamera(self.camera_id.get())

    def assignCamera(self, event):
        if platform.system() != "Linux":
            self.camera_name_fromDLL.set(self.camera_dic[self.camera_id.get()])

    def locateCameraCmbbox(self):
        if platform.system() == 'Windows':
            import clr
            clr.AddReference(r"..\DirectShowLib\DirectShowLib-2005")
            from DirectShowLib import DsDevice, FilterCategory

            # Get names of detected camera devices
            captureDevices = DsDevice.GetDevicesOfCat(FilterCategory.VideoInputDevice)
            self.camera_dic = {cam_id: device.Name for cam_id, device in enumerate(captureDevices)}

            self.camera_dic[str(max(list(self.camera_dic.keys())) + 1)] = 'Disable'
            self.Camera_Name['values'] = [device for device in self.camera_dic.values()]
            self._logger.debug(f"Camera list: {[device for device in self.camera_dic.values()]}")
            dev_num = len(self.camera_dic)

        elif platform.system() == "Darwin":
            cmd = 'system_profiler SPCameraDataType | grep "^    [^ ]" | sed "s/    //" | sed "s/://" '
            res = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
            # 出力結果の加工
            ret = res.stdout.decode('utf-8')
            cam_list = list(filter(lambda a: a != "", ret.split('\n')))
            self.camera_dic = {cam_id: camera_name for cam_id, camera_name in enumerate(cam_list)}
            dev_num = len(self.Camera_Name['values'])
            self.camera_dic[str(max(list(self.camera_dic.keys())) + 1)] = 'Disable'
            self.Camera_Name['values'] = [device for device in self.camera_dic.values()]
        else:
            return False
        if self.camera_id.get() > dev_num - 1:
            print('Inappropriate camera ID! -> set to 0')
            self._logger.debug('Inappropriate camera ID! -> set to 0')
            self.camera_id.set(0)
            if dev_num == 0:
                print('No camera devices can be found.')
                self._logger.debug('No camera devices can be found.')
        #
        self.camera_entry.bind('<KeyRelease>', self.assignCamera)
        self.Camera_Name.current(self.camera_id.get())

    def saveCapture(self):
        self.camera.saveCapture()

    def OpenCaptureDir(self):
        directory = "Captures"
        self._logger.debug(f'Open folder: \'{directory}\'')
        if platform.system() == 'Windows':
            subprocess.call(f'explorer "{directory}"')
        elif platform.system() == 'Darwin':
            command = f'open "{directory}"'
            subprocess.run(command, shell=True)

    def OpenCommandDir(self):
        if self.Command_nb.index("current") == 0:
            directory = os.path.join("Commands", "PythonCommands")
        else:
            directory = os.path.join("Commands", "McuCommands")
        self._logger.debug(f'Open folder: \'{directory}\'')
        if platform.system() == 'Windows':
            subprocess.call(f'explorer "{directory}"')
        elif platform.system() == 'Darwin':
            command = f'open "{directory}"'
            subprocess.run(command, shell=True)

    def set_cameraid(self, event=None):
        keys = [k for k, v in self.camera_dic.items() if v == self.Camera_Name.get()]
        if keys:
            ret = keys[0]
        else:
            ret = None
        self.camera_id.set(ret)

    def applyFps(self, event=None):
        print('changed FPS to: ' + self.fps.get() + ' [fps]')
        self.preview.setFps(self.fps.get())

    def applyBaudRate(self, event=None):
        pass

    def applyWindowSize(self, event=None):
        width, height = map(int, self.show_size.get().split("x"))
        self.preview.setShowsize(height, width)
        if self.show_size_tmp != self.show_size_cb['values'].index(self.show_size_cb.get()):
            ret = tkmsg.askokcancel('確認', "この画面サイズに変更しますか？")
        else:
            return

        if ret:
            self.show_size_tmp = self.show_size_cb['values'].index(self.show_size_cb.get())
        else:
            self.show_size_cb.current(self.show_size_tmp)
            width_bef, height_bef = map(int, self.show_size.get().split("x"))
            self.preview.setShowsize(height_bef, width_bef)
            # self.show_size_tmp = self.show_size_cb['values'].index(self.show_size_cb.get())

    def activateSerial(self):
        if self.ser.isOpened():
            print('Port is already opened and being closed.')
            self.ser.closeSerial()
            self.keyPress = None
            self.activateSerial()
        else:
            if self.ser.openSerial(self.com_port.get(), self.com_port_name.get(), self.baud_rate.get()):
                print('COM Port ' + str(self.com_port.get()) + ' connected successfully')
                self._logger.debug('COM Port ' + str(self.com_port.get()) + ' connected successfully')
                self.keyPress = KeyPress(self.ser)
                self.settings.com_port.set(self.com_port.get())
                self.settings.baud_rate.set(self.baud_rate.get())
                self.settings.save()

    def inactivateSerial(self):
        if self.ser.isOpened():
            print('Port is already opened and being closed.')
            self.ser.closeSerial()
            self.keyPress = None

    def activateKeyboard(self):
        
        is_windows = platform.system() == 'Windows'

        if self.is_use_keyboard.get():
            # enable Keyboard as controller
            if self.keyboard is None:
                self.keyboard = SwitchKeyboardController(self.keyPress)
                self.keyboard.listen()

            # bind focus
            if not is_windows:
                return
            self.mainwindow.bind("<FocusIn>", self.onFocusInController)
            self.mainwindow.bind("<FocusOut>", self.onFocusOutController)

        else:
            if not is_windows:
                return
            if self.keyboard is not None:
                # stop listening to keyboard events
                self.keyboard.stop()
                self.keyboard = None

            self.mainwindow.bind("<FocusIn>", lambda _: None)
            self.mainwindow.bind("<FocusOut>", lambda _: None)

    def onFocusInController(self, event):
        # enable Keyboard as controller
        if event.widget == self.mainwindow and self.keyboard is None:
            self.keyboard = SwitchKeyboardController(self.keyPress)
            self.keyboard.listen()

    def onFocusOutController(self, event):
        # stop listening to keyboard events
        if event.widget == self.mainwindow and not self.keyboard is None:
            self.keyboard.stop()
            self.keyboard = None

    def createControllerWindow(self):
        if not self.controller is None:
            self.controller.focus_force()
            return

        window = ControllerGUI(self.mainwindow, self.ser)
        window.protocol("WM_DELETE_WINDOW", self.closingController)
        self.controller = window

    def activate_Left_stick_mouse(self):
        self.preview.ApplyLStickMouse()

    def activate_Right_stick_mouse(self):
        self.preview.ApplyRStickMouse()

    # def createGetFromHomeWindow(self):
    #     if self.poke_treeview is not None:
    #         self.poke_treeview.focus_force()
    #         return
    #
    #     window2 = GetFromHomeGUI(self.root, self.settings.season, self.settings.is_SingleBattle)
    #     window2.protocol("WM_DELETE_WINDOW", self.closingGetFromHome)
    #     self.poke_treeview = window2

    def loadCommands(self):
        self.py_loader = CommandLoader(util.ospath('Commands/PythonCommands'),
                                       PythonCommandBase.PythonCommand)  # コマンドの読み込み
        self.mcu_loader = CommandLoader(util.ospath('Commands/McuCommands'), McuCommandBase.McuCommand)
        self.py_classes = self.py_loader.load()
        self.mcu_classes = self.mcu_loader.load()
        self.setCommandItems()
        self.assignCommand()

    def setCommandItems(self):
        self.py_cb['values'] = [c.NAME for c in self.py_classes]
        self.py_cb.current(0)
        self.mcu_cb['values'] = [c.NAME for c in self.mcu_classes]
        self.mcu_cb.current(0)

    def assignCommand(self):
        # 選択されているコマンドを取得する
        self.mcu_cur_command = self.mcu_classes[self.mcu_cb.current()]()  # MCUコマンドについて

        # pythonコマンドは画像認識を使うかどうかで分岐している
        cmd_class = self.py_classes[self.py_cb.current()]
        if issubclass(cmd_class, PythonCommandBase.ImageProcPythonCommand):
            try:  # 画像認識の際に認識位置を表示する引数追加。互換性のため従来のはexceptに。
                self.py_cur_command = cmd_class(self.camera, self.preview)
            except TypeError:
                self.py_cur_command = cmd_class(self.camera)
            except:
                self.py_cur_command = cmd_class(self.camera)


        else:
            self.py_cur_command = cmd_class()

        if self.Command_nb.index(self.Command_nb.select()) == 0:
            self.cur_command = self.py_cur_command
        else:
            self.cur_command = self.mcu_cur_command

    def reloadCommands(self):
        # 表示しているタブを読み取って、どのコマンドを表示しているか取得、リロード後もそれが選択されるようにする
        oldval_mcu = self.mcu_cb.get()
        oldval_py = self.py_cb.get()

        self.py_classes = self.py_loader.reload()
        self.mcu_classes = self.mcu_loader.reload()

        # Restore the command selecting state if possible
        self.setCommandItems()
        if oldval_mcu in self.mcu_cb['values']:
            self.mcu_cb.set(oldval_mcu)
        if oldval_py in self.py_cb['values']:
            self.py_cb.set(oldval_py)
        self.assignCommand()
        print('Finished reloading command modules.')
        self._logger.info("Reloaded commands.")

    def startPlay(self, *event):
        if self.cur_command is None:
            print('No commands have been assigned yet.')
            self._logger.info('No commands have been assigned yet.')

        # set and init selected command
        self.assignCommand()

        print(self.startButton["text"] + ' ' + self.cur_command.NAME)
        self._logger.info(self.startButton["text"] + ' ' + self.cur_command.NAME)
        self.cur_command.start(self.ser, self.stopPlayPost)

        self.startButton["text"] = "Stop"
        self.startButton["command"] = self.stopPlay
        self.reloadCommandButton["state"] = "disabled"

    def stopPlay(self):
        print(self.startButton["text"] + ' ' + self.cur_command.NAME)
        self._logger.info(self.startButton["text"] + ' ' + self.cur_command.NAME)
        self.startButton["state"] = "disabled"
        self.cur_command.end(self.ser)

    def stopPlayPost(self):
        self.startButton["text"] = "Start"
        self.startButton["command"] = self.startPlay
        self.startButton["state"] = "normal"
        self.reloadCommandButton["state"] = "normal"

    def run(self):
        self._logger.debug("Start Poke-Controller")
        self.mainwindow.mainloop()

    def exit(self):
        ret = tkmsg.askyesno('確認', 'Poke Controllerを終了しますか？')
        if ret:
            if self.ser.isOpened():
                self.ser.closeSerial()
                print("Serial disconnected")
                # self._logger.info("Serial disconnected")

            # stop listening to keyboard events
            if not self.keyboard is None:
                self.keyboard.stop()
                self.keyboard = None

            # save settings
            self.settings.is_show_realtime.set(self.is_show_realtime.get())
            self.settings.is_show_serial.set(self.is_show_serial.get())
            self.settings.is_use_keyboard.set(self.is_use_keyboard.get())
            self.settings.fps.set(self.fps.get())
            self.settings.show_size.set(self.show_size.get())
            self.settings.com_port.set(self.com_port.get())
            self.settings.baud_rate.set(self.baud_rate.get())
            self.settings.camera_id.set(self.camera_id.get())

            self.settings.save()

            self.camera.destroy()
            cv2.destroyAllWindows()
            self._logger.debug("Stop Poke Controller")
            self.mainwindow.destroy()

    def closingController(self):
        self.controller.destroy()
        self.controller = None

    # def closingGetFromHome(self):
    #     self.poke_treeview.destroy()
    #     self.poke_treeview = None

    def loadSettings(self):
        self.settings = Settings.GuiSettings()
        self.settings.load()

    def ReloadCommandWithF5(self, *event):
        self.reloadCommands()

    def StartCommandWithF6(self, *event):
        if self.startButton["text"] == "Stop":
            print("Command is now working!")
            self._logger.debug("Command is now working!")
        elif self.startButton["text"] == "Start":
            self.startPlay()

    def StopCommandWithEsc(self, *event):
        if self.startButton["text"] == "Stop":
            self.stopPlay()

    def OpenPokeHomeCoop(self):
        self._logger.debug("Open Pokemon home cooperate window")
        if self.poke_treeview is not None:
            self.poke_treeview.focus_force()
            return

        window2 = GetFromHomeGUI(self.mainwindow, self.settings.season, self.settings.is_SingleBattle)
        window2.protocol("WM_DELETE_WINDOW", self.closingGetFromHome)
        self.poke_treeview = window2

    def closingGetFromHome(self):
        self._logger.debug("Close Pokemon home cooperate window")
        self.poke_treeview.destroy()
        self.poke_treeview = None

    def LineTokenSetting(self):
        self._logger.debug("Show line API")
        if self.line is None:
            self.line = Line_Notify(self.camera)
        print(self.line)
        self.line.getRateLimit()
        # LINE.send_text_n_image("CAPTURE")

    def OpenKeyConfig(self):
        self._logger.debug("Open KeyConfig window")
        if self.key_config is not None:
            self.key_config.focus_force()
            return

        kc_window = PokeKeycon(self.mainwindow)
        kc_window.protocol("WM_DELETE_WINDOW", self.closingKeyConfig)
        self.key_config = kc_window

    def closingKeyConfig(self):
        self._logger.debug("Close KeyConfig window")
        self.key_config.destroy()
        self.key_config = None

    def ResetWindowSize(self):
        self._logger.debug("Reset window size")
        self.preview.setShowsize(360, 640)
        self.show_size_cb.current(0)

    def exit_menu(self):
        self._logger.debug("Close Menubar")
        if self.ser.isOpened():
            self.ser.closeSerial()
            print("serial disconnected")

        # stop listening to keyboard events
        if self.keyboard is not None:
            self.keyboard.stop()
            self.keyboard = None

        # save settings
        self.settings.save()

        self.camera.destroy()
        cv2.destroyAllWindows()
        self.mainwindow.destroy()


class StdoutRedirector(object):
    """
    標準出力をtextウィジェットにリダイレクトするクラス
    重いので止めました →# update_idletasks()で出力のたびに随時更新(従来はfor loopのときなどにまとめて出力されることがあった)
    """

    def __init__(self, text_widget):
        self.text_space = text_widget

    def write(self, string):
        self.text_space.configure(state='normal')
        self.text_space.insert('end', string)
        self.text_space.see('end')
        # self.text_space.update_idletasks()
        self.text_space.configure(state='disabled')

    def flush(self):
        pass


if __name__ == '__main__':
    import tkinter as tk

    logger = PokeConLogger.root_logger()
    # logger.info('The root logger is created.')

    app = PokeControllerApp()
    app.run()
