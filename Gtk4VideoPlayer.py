#!/usr/bin/env python3

import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, Adw, Gio, GLib
from subprocess import check_output, STDOUT

CSS = """
.title {
    font-size: 11pt;
}
#myplayer {
    background: #000;
}
"""


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(title="Video Player", *args, **kwargs)
        
        self.use_dark_theme = True
        sm.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        
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
        
        btn_url = Gtk.Button.new_from_icon_name("edit-paste-symbolic")
        btn_url.set_tooltip_text("Open URL from clipboard\nFile or Web or Youtube")
        btn_url.connect("clicked", self.open_url)
        self.header_bar.pack_end(btn_url)

        btn_open = Gtk.Button.new_from_icon_name("document-open-symbolic")
        btn_open.set_tooltip_text("Open File")
        btn_open.connect("clicked", self.open_file)
        self.header_bar.pack_end(btn_open)
        
        btn_theme = Gtk.Button.new_from_icon_name("preferences-desktop-theme-symbolic")
        btn_theme.set_tooltip_text("toggle theme\nDark / Light")
        btn_theme.connect("clicked", self.toggle_theme)
        self.header_bar.pack_end(btn_theme)

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
            "video/ogg"
        ]
        for vid in mime_types:
            self.file_filter_videos.add_mime_type(vid)
            
    def toggle_theme(self, *args):
        if self.use_dark_theme == False:
            sm.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            self.use_dark_theme = True
        else:
            sm.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            self.use_dark_theme = False

    def open_file(self, *args):
        print("open file")
        self.show_open_dialog()

    def open_url(self, *args):
        self.clipboard.read_text_async(None, self.on_paste_url)

    def on_paste_url(self, clipboard, result, *args):
        url = self.clipboard.read_text_finish(result)
        if url is not None:
            if url.startswith("http"):
                if ("youtube" in url[:22] or "youtu.be" in url[:22] 
                    or "mediathek" in url[:25] or "zdf.de" in url[:25]):
                    print("is youtube, grabbing video url")
                    url = self.get_yt_url(url).strip()
                    self.set_title("Youtube Video")
                    print(f"grabbed: {url}")
                else:
                    self.set_title("Web Video")
                    print(url)
                self.player.set_file(Gio.File.new_for_uri(url))
            else:
                print(url)
                self.player.set_file(Gio.File.new_for_path(url))
                name = url.split("/")[-1].split(".")[-2]
                self.set_title(name)
                
    def on_paste_url_startup(self, url, *args):
        if url is not None:
            if url.startswith("http"):
                if "youtube" in url[:22]:
                    print("is youtube, grabbing video url")
                    url = self.get_yt_url(url)
                    self.set_title("Youtube Video")
                    print(f"grabbed: {url}")
                else:
                    url = url
                    self.set_title("Web Video")
                    print(url)
                self.video_file = url
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
        if "mediathek" in url or "zdf.de" in url:
            cmd = f"yt-dlp --no-warnings -g -f 'bestvideo[height<=480]+bestaudio/best[height<=480]' {url}"
        else:
            cmd = f"yt-dlp --no-warnings -g -f 'worst/worstvideo+bestaudio' {url}"
        result = check_output(cmd, stderr=STDOUT, shell=True).decode().split("\n")[0]
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
        if keycode == ord('h'):
            self.toggle_headerbar()
                
    def on_activate(self, app, *args, **kwargs):
        self.win = MainWindow(application=app)
        self.win.present()
        keycont = Gtk.EventControllerKey()
        keycont.connect("key-pressed", self.lol, self.win)
        self.win.add_controller(keycont)   
     
    def toggle_headerbar(self):
        allocation = self.win.get_allocation()
        if self.win.header_bar.is_visible():
            self.win.header_bar.set_visible(False)
            self.win.set_default_size(allocation.width, allocation.height - 44)
        else:
            self.win.header_bar.set_visible(True)
            self.win.set_default_size(allocation.width, allocation.height + 44)


app = MyApp()
sm = app.get_style_manager()
app.run(sys.argv)
