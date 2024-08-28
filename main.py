import nonebot

from nonebot_adapter_club255 import Adapter as Club255_Adapter

nonebot.init()

app = nonebot.get_app()

driver = nonebot.get_driver()
driver.register_adapter(Club255_Adapter)

nonebot.load_plugins("plugins")

if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")
