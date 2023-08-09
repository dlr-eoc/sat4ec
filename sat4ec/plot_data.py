import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import matplotlib.dates as mdates

pd.options.display.width = 1200
pd.options.display.max_colwidth = 100
pd.options.display.max_columns = 100


class Plot:
    def __init__(self, data=None):
        if isinstance(data, (str, Path)):
            if data.is_file() and data.suffix == ".csv":
                self._get_dataframe(data)

            elif data.is_dir():
                data = list(data.glob("*.csv"))[-1]  # get latest dataset
                self._get_dataframe(data)

            self.filename = data
            self._get_orbit()

        elif isinstance(data, pd.DataFrame):
            self.dataframe = data

        self.fig = None

        self._prepare_dataframe()

    def _get_dataframe(self, data):
        self.dataframe = pd.read_csv(data)

    def _get_orbit(self):
        # TODO: also get orbit from dataframe if not file was provided
        self.asc = True if self.filename.stem.split("_")[2] == "asc" else False

    def _prepare_dataframe(self):
        self.dataframe["interval_from"] = pd.to_datetime(self.dataframe["interval_from"])  # transform to datetime
        self.dataframe["month_short"] = self.dataframe["interval_from"].dt.month_name().str[:3]  # get month shortname

    def plot_dataframe(self):
        """
        Plot unaggregated data.
        """
        self.fig, ax1 = plt.subplots()
        self.dataframe.plot.line(
            ax=ax1,
            x="interval_from",
            y=["B0_mean", "B0_min", "B0_max", "B0_stDev"],
            ylabel="S1 backscatter [dB]",
            x_compat=True  # suppress tick resolution adjustment, e.g. aggregation
        )
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))  # set xtick to every 2nd month
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b"))  # only display month
        ax1.xaxis.set_label_text(label="")  # remove label of x axis

        ax2 = ax1.secondary_xaxis(-0.15)  # get a 2nd x axis to have the years displayed
        ax2.xaxis.set_major_locator(mdates.YearLocator())  # set xtick to year
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))  # only display year

    def plot_monthly_aggregated(self):
        sns.lineplot(x="month_short", y="B0_mean", data=self.dataframe)
        sns.lineplot(x="month_short", y="B0_min", data=self.dataframe)
        sns.lineplot(x="month_short", y="B0_max", data=self.dataframe)
        sns.lineplot(x="month_short", y="B0_stDev", data=self.dataframe)

    def save_plot(self):
        orbit = "asc" if self.asc else "des"
        self.fig.savefig(Path.cwd().joinpath(f"{orbit}.jpg"))


if __name__ == "__main__":
    plotter = Plot(data=Path(r"/mnt/data1/gitlab/sat4ec/results/2023_08_09/indicator_1_asc_2023_08_09_10_07_47.csv"))
    plotter.plot_dataframe()
    plotter.save_plot()
    # plotter.plot_monthly_aggregated()

    plt.show()
