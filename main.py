from pathlib import Path

import nonebot

nonebot.adapters.__path__.append(
    str((Path(__file__).parent / "nonebot" / "adapters").resolve())
)

from nonebot.adapters.club255 import Adapter as Club255_Adapter

nonebot.init()

app = nonebot.get_app()

driver = nonebot.get_driver()
driver.register_adapter(Club255_Adapter)

nonebot.load_plugins("plugins")

if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")
