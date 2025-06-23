from display_manager import ScreenUI
from wifi_manager    import WiFiManager
from config_server   import ConfigServer
import time

def main():
    ui = ScreenUI()
    wm = WiFiManager(ui)
    srv = ConfigServer(wm, ui)

    ui.msg("Booting...")
    if not wm.connect_saved():
        wm.start_ap()
    srv.start()
    srv._show_ips()

    while True:
        srv.poll()
        wm.watchdog()
        time.sleep(0.1)

if __name__ == "__main__":
    main()
