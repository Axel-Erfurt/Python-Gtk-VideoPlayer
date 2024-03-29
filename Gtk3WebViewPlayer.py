#!/usr/bin/env python3

import sys
import gi

gi.require_version("WebKit2", "4.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, Gio, GLib, WebKit2 as WebKit
from subprocess import check_output, STDOUT

CSS = b"""
#myheaderbar, #myappwindow, #myview {
    background: black;
    color: lightgray;
    border: 0;
}
#btn_open:hover, #btn_paste:hover {
    background: #3c91c5;
}
"""

HTML ="""<!DOCTYPE html>
<html>
<body style="background-color:black;">

</body>
</html>"""

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(title="Video Player", *args, **kwargs)

        self.set_name("myappwindow")
        self.set_icon_name("multimedia-video-player")
        self.current_folder = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_VIDEOS)

        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        action = Gio.SimpleAction.new("Open", None)
        action.connect("activate", self.open_file)
        self.add_action(action)

        screen = Gdk.Screen.get_default()
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS)
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.header_bar = Gtk.HeaderBar.new()
        self.header_bar.set_name("myheaderbar")
        self.header_bar.set_has_subtitle(False)
        self.header_bar.set_show_close_button(True)
        self.set_titlebar(titlebar=self.header_bar)

        btn_url = Gtk.Button.new_from_icon_name("edit-paste", 2)
        btn_url.set_name("btn_paste")
        btn_url.set_tooltip_text("Open URL from clipboard\nFile or Web or Youtube")
        btn_url.connect("clicked", self.open_url)
        self.header_bar.pack_end(btn_url)
        
        btn_open = Gtk.Button.new_from_icon_name("document-open", 2)
        btn_open.set_name("btn_open")
        btn_open.set_tooltip_text("Open File")
        btn_open.connect("clicked", self.open_file)
        self.header_bar.pack_end(btn_open)

        self.view = WebKit.WebView(hexpand=True, vexpand=True)
        self.view.set_name("myview")
        self.video_url = ""
        self.view.load_html(HTML)
        self.set_title("Video Player")

        #self.view.load_uri(self.video_url)
        self.add(self.view)
        self.set_size_request(320, 200)
        self.set_default_size(640, 360)

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
            
        if len(sys.argv) > 1:
            url = sys.argv[1]
            self.on_paste_url(url)


    def open_file(self, *args):
        print("open file")
        self.show_open_dialog()

    def open_url(self, *args):
        url = self.clipboard.wait_for_text()
        if url != "":
            self.on_paste_url(url)

    def on_paste_url(self, url, *args):
        if url is not None:
            if url.startswith("http"):
                if "youtube" in url[:22] or "youtu.be" in url[:22]:
                    print("is youtube, grabbing video url")
                    url = self.get_yt_url(url)
                    self.set_title("Youtube Video")
                else:
                    url = url
                    self.set_title("Web Video")
                print(url)
                self.video_url = str(url)
                self.view.load_uri(self.video_url)              
            else:
                print(url)
                self.video_url = f"file://{url}"
                self.view.load_uri(self.video_url)
                name = self.video_url.split("/")[-1].split(".")[-2]
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
            filename = f"file://{dialog.get_file().get_path()}"
            print(f"loading {filename}")
            self.video_url = filename
            self.view.load_uri(self.video_url)
            name = filename.split("/")[-1].split(".")[-2]
            self.set_title(name)

        dialog.destroy()
        
    def get_yt_url(self, url, *args):
        cmd = f"yt-dlp -g -f worst {url}"
        result = check_output(cmd, stderr=STDOUT, shell=True).decode()
        result = f'http{result.split("http")[1]}'
        return result


class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("activate", self.on_activate)
        self.connect("open", self.on_activate)
        self.set_flags(Gio.ApplicationFlags.HANDLES_OPEN)
        self.win = None
                
    def on_activate(self, app, *args, **kwargs):
        self.win = MainWindow(application=app)
        self.win.show_all()


app = MyApp()
app.run(sys.argv)

