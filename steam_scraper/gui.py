from tkinter import Frame, BOTH
from pandastable import Table, TableModel


class TestApp(Frame):
    """Basic test frame for the table"""

    def __init__(self, df, parent=None):
        self.parent = parent
        Frame.__init__(self)
        self.main = self.master
        # self.main.state("zoomed")
        self.main.title("Table app")
        f = Frame(self.main)
        f.pack(fill=BOTH, expand=1)
        # df = TableModel.getSampleData()
        self.table = pt = Table(
            f,
            dataframe=df,
            showtoolbar=False,
            showstatusbar=False,
            editable=False,
            enable_menus=True,
            maxcellwidth=400,
        )

        pt.show()
        self.color_cells(df)

    def color_cells(self, df):
        self.table.adjustColumnWidths()
        selected_df = df[["Type (pk)", "Type (ar)", "Type (tr)"]].reset_index(drop=True)

        color_light, color_dark = "#E1FFEB", "#A7FFC4"
        index = list(selected_df.loc[selected_df["Type (pk)"] == "*"].index)
        self.table.setColumnColors(cols=[2, 3, 4], clr=color_light)
        self.table.setRowColors(rows=index, cols=[2], clr=color_dark)
        self.table.resizeColumn(2, 20)

        color_light, color_dark = "#DBE0FF", "#8192FF"
        index = list(selected_df.loc[selected_df["Type (ar)"] == "*"].index)
        self.table.setColumnColors(cols=[5, 6, 7], clr=color_light)
        self.table.setRowColors(rows=index, cols=[5], clr=color_dark)
        self.table.resizeColumn(5, 20)

        color_light, color_dark = "#FFE2E2", "#FF8181"
        index = list(selected_df.loc[selected_df["Type (tr)"] == "*"].index)
        self.table.setColumnColors(cols=[8, 9, 10], clr=color_light)
        self.table.setRowColors(rows=index, cols=[8], clr=color_dark)
        self.table.resizeColumn(8, 20)
