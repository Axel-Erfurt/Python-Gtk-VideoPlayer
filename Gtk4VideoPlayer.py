#!/usr/bin/env python3

import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, Adw, Gio, GLib
from subprocess import check_output, STDOUT

CSS = """
#myheaderbar, #myappwindow {
    background: black;
    color: lightgray;
    border-radius: 12px 12px 4px 4px;
}
"""


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(title="Video Player", *args, **kwargs)

        self.set_name("myappwindow")
        self.set_icon_name("multimedia-video-player")
        self.current_folder = Gio.File.new_for_path(
            GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_VIDEOS)
        )

        action = Gio.SimpleAction.new("Open", None)
        action.connect("activate", self.open_file)
        self.add_action(action)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(bytes(CSS.encode()))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.header_bar = Gtk.HeaderBar.new()
        self.header_bar.set_name("myheaderbar")
        self.set_titlebar(titlebar=self.header_bar)
        
        btn_url = Gtk.Button.new_from_icon_name("edit-paste")
        btn_url.set_tooltip_text("Open URL from clipboard\nFile or Web or Youtube")
        btn_url.connect("clicked", self.open_url)
        self.header_bar.pack_end(btn_url)

        btn_open = Gtk.Button.new_from_icon_name("document-open")
        btn_open.set_tooltip_text("Open File")
        btn_open.connect("clicked", self.open_file)
        self.header_bar.pack_end(btn_open)

        self.video_file = ""
        self.player = Gtk.Video.new()
        self.player.set_name("myplayer")
        self.player.set_autoplay(True)

        if len(sys.argv) > 1:
            self.video_file = sys.argv[1]
            self.on_paste_url_startup(self.video_file)
            
        self.set_child(self.player)
        self.set_size_request(320, 230)
        self.set_default_size(640, 406)
        cursor_def = Gdk.Cursor.new_from_name('default')
        self.set_cursor(cursor_def)

        self.clipboard = Gdk.Display.get_default().get_clipboard()

        self.file_filter_videos = Gtk.FileFilter()
        self.file_filter_videos.set_name("Video Files")
        mime_types = [
            "video/mp4",
            "video/quicktime",
            "video/webm",
            "video/mpeg",
            "video/x-msvideo",
            "video/3gpp",
        ]
        for vid in mime_types:
            self.file_filter_videos.add_mime_type(vid)

    def open_file(self, *args):
        print("open file")
        self.show_open_dialog()

    def open_url(self, *args):
        self.clipboard.read_text_async(None, self.on_paste_url)

    def on_paste_url(self, clipboard, result, *args):
        url = self.clipboard.read_text_finish(result)
        if url is not None:
            if url.startswith("http"):
                if "youtube" in url[:22]:
                    print("is youtube, grabbing video url")
                    url = self.get_yt_url(url)
                    self.set_title("Youtube Video")
                else:
                    url = url
                    self.set_title("Web Video")
                print(url)
                self.video_file = str(url)
                self.player.set_file(Gio.File.new_for_uri(self.video_file))               
            else:
                print(url)
                self.video_file = str(url)
                self.player.set_file(Gio.File.new_for_path(self.video_file))
                name = self.video_file.split("/")[-1].split(".")[-2]
                self.set_title(name)
                
    def on_paste_url_startup(self, url, *args):
        if url is not None:
            if url.startswith("http"):
                if "youtube" in url[:22]:
                    print("is youtube, grabbing video url")
                    url = self.get_yt_url(url)
                    self.set_title("Youtube Video")
                else:
                    url = url
                    self.set_title("Web Video")
                print(url)
                self.video_file = str(url)
                self.player.set_file(Gio.File.new_for_uri(self.video_file))               
            else:
                print(url)
                self.video_file = str(url)
                self.player.set_file(Gio.File.new_for_path(self.video_file))
                name = self.video_file.split("/")[-1].split(".")[-2]
                self.set_title(name)

    def show_open_dialog(self):
        self.dialog = Gtk.FileChooserNative.new("Open", self, Gtk.FileChooserAction.OPEN, "Open", "Cancel")
        self.dialog.set_current_folder(self.current_folder)
        self.dialog.add_filter(self.file_filter_videos)
        self.dialog.set_transient_for(self)
        self.dialog.connect("response", self.on_open_dialog_response)
        self.dialog.show()

    def on_open_dialog_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.ACCEPT:
            filename = str(dialog.get_file().get_path())
            print(f"loading {filename}")
            self.video_file = filename
            self.player.set_file(Gio.File.new_for_path(self.video_file))
            name = filename.split("/")[-1].split(".")[-2]
            self.set_title(name)

        dialog.destroy()
        
    def get_yt_url(self, url, *args):
        cmd = f"yt-dlp -g -f worst {url}"
        result = check_output(cmd, stderr=STDOUT, shell=True).decode()
        return result


class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("activate", self.on_activate)
        self.connect("open", self.on_activate)
        self.set_flags(Gio.ApplicationFlags.HANDLES_OPEN)
        self.win = None

    def lol(self, keyval, keycode, state, user_data, win):
        if keycode == ord("q"):
            win.close()
        if keycode == ord("f"):
            if win.is_fullscreen():
                win.unfullscreen()
            else:
                win.fullscreen()
        if keycode == ord('m'):
            cursor = self.win.get_cursor()
            cursor_def = Gdk.Cursor.new_from_name('default')
            cursor_blank = Gdk.Cursor.new_from_name('none')
            if cursor.get_name() == "default":
                self.win.set_cursor(cursor_blank)
            else:
                self.win.set_cursor(cursor_def)
                
    def on_activate(self, app, *args, **kwargs):
        self.win = MainWindow(application=app)
        self.win.present()
        keycont = Gtk.EventControllerKey()
        keycont.connect("key-pressed", self.lol, self.win)
        self.win.add_controller(keycont)      


app = MyApp()
app.run(sys.argv)

