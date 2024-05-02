from src.gui import TestApp
from src.scrapper import Scrapper

if __name__ == "__main__":
    steam_scrapper = Scrapper()
    df = steam_scrapper.run(delay_in_hours=4)

    app = TestApp(df=df)
    app.mainloop()
