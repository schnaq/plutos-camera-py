import os
import time
from datetime import datetime, timezone

import gphoto2 as gp
from loguru import logger as log

CAMERA = gp.check_result(gp.gp_camera_new())
gp.check_result(gp.gp_camera_init(CAMERA))


def time_measure(func):
    """
    Decorator which measures the time a function needs to execute.
    :param func:
    :return:
    """

    def inner(*args, **kwargs):
        tick = time.time()
        result = func(*args, **kwargs)
        tock = time.time()
        log.debug(f"[{func.__name__}]: Took {round(tock - tick, 4)} seconds")
        return result

    return inner


def utc_now() -> int:
    """
    :return: UTC Unix Timestamp in s.
    """
    return int(datetime.now(timezone.utc).timestamp())


def set_setting(camera_config, setting: str, value) -> None:
    """
    Set a setting in the camera configuration. Don't forget to store the new configuration with `set_config()`.
    :param camera_config:
    :param setting:
    :param value:
    :return:
    """
    split = setting.split("/")
    # filter not empty strings
    split = list(filter(None, split))

    if len(split) == 0:
        log.error(f"Einstellung {setting} ist nicht gültig.")
        return

    try:
        setting_selector = None
        for s in split:
            setting_selector = camera_config.get_child_by_name(s)
        setting_selector.set_value(value)
    except gp.GPhoto2Error as ex:
        log.warning(
            f"Konnte Einstellung {setting} nicht setzen. Vielleicht wird diese Einstellung von deiner Kamera nicht unterstützt oder der zugehörige Wert ist nicht gültig. gphoto2 Fehler: {ex}")


@time_measure
def autofokus():
    """
    Triggert den Autofokus der aktuell angeschlossenen Kamera.
    :return:
    """
    try:
        camera_config = CAMERA.get_config()
        set_setting(camera_config, "/main/actions/autofocusdrive", 1)
        CAMERA.set_config(camera_config)
        log.info("🎯 Autofokus durchgeführt")
    except gp.GPhoto2Error as ex:
        log.warning(
            f"🎯❌ Autofokus konnte nicht durchgeführt werden: {ex}")


@time_measure
def take_picture(camera: gp.Camera):
    """
    Directly takes a picture and saves it to the Pi.
    :return:
    """
    log.info("📸 Bild wird aufgenommen.")
    timestamp = utc_now()
    file_path = camera.capture(gp.GP_CAPTURE_IMAGE)
    target = os.path.join(".", f"{timestamp}.jpg")
    camera_file = camera.file_get(
        file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
    camera_file.save(target)
    camera.file_delete(file_path.folder, file_path.name)


def main():
    autofokus()
    take_picture(CAMERA)


if __name__ == '__main__':
    main()
