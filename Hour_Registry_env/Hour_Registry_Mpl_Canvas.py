
# Imports
from PyQt5.QtWidgets import QMainWindow
from PyQt5 import QtWidgets
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import pandas as pd
import datetime as dt
import numpy as np
import math
import matplotlib
import seaborn as sns
import datetime


# Ensure using PyQt5 backend
matplotlib.use('QT5Agg')


def addlabels(canvas, x, y, bot):
    for i in range(len(x)):
        if y[i] > 0:
            canvas.text(i, bot[i] + (0.5 * y[i]), y[i],
                                           ha='center',
                                           bbox=dict(facecolor='white', alpha=.5))

class MplCanvas(Canvas):
    def __init__(self):

        plotsize = QMainWindow()
        width = plotsize.frameGeometry().width()/55
        height = plotsize.frameGeometry().height()/100
        self.fig = Figure(figsize=(width, height))#layout= "constrained")


        Canvas.__init__(self, self.fig)
        Canvas.setSizePolicy(self, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        Canvas.updateGeometry(self)

# Matplotlib widget
class MplWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)   # Inherit from QWidget
        self.canvas = MplCanvas()                  # Create canvas object
        self.navi_toolbar = NavigationToolbar(self.canvas, self)
        self.vbl = QtWidgets.QVBoxLayout()         # Set box for plotting
        self.vbl.addWidget(self.canvas)

        self.setLayout(self.vbl)
        self.vbl.addWidget(self.navi_toolbar)


    def WeeklyPlot(self, df, year, week):
        self.WeeklyPlot_widget.canvas.fig.clf()
        ax =  self.WeeklyPlot_widget.canvas.fig.add_subplot(111)
        if not df.empty:
            idx_projects = df['Project_ID'].index.values
            name_projects = df['Project_ID'].values

            name_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            idx_days = []

            start_date = datetime.datetime.strptime(f"{year}-{week}-1", "%Y-%W-%w").date()
            end_date = datetime.datetime.strptime(f"{year}-{week}-0", "%Y-%W-%w").date()

            for (num, item) in enumerate(name_days):
                idx_days.append(num + 1)
            df_plot = pd.DataFrame({'Day':name_days})
            for name_pr, index_pr in zip(name_projects, idx_projects):
                df_plot[f'{name_pr}'] = ""
                for name_day in name_days:
                    df_plot.loc[df_plot['Day']== name_day, f'{name_pr}'] = float(df[[name_day]].iloc[index_pr].values)

            # create stacked bar chart
            # Plots first project
            ax.bar(df_plot['Day'], df_plot[f'{df_plot.columns[1]}'],
                                          edgecolor='black',
                                          label=f'{df_plot.columns[1]}')
            addlabels(ax, df_plot['Day'], df_plot[f'{df_plot.columns[1]}'], [0, 0, 0, 0, 0, 0 ,0])

            bot = df_plot[f'{df_plot.columns[1]}']

            # Plots all subsequent projects
            for item in range(2, len(df_plot.columns)):
                ax.bar(df_plot['Day'], df_plot[f'{df_plot.columns[item]}'],
                                              bottom=bot,
                                              edgecolor = 'black',
                                              label=f'{df_plot.columns[item]}')
                addlabels(ax, df_plot['Day'], df_plot[f'{df_plot.columns[item]}'], bot)
                bot = bot + df_plot[f'{df_plot.columns[item]}']

            ax.bar_label(ax.containers[-1], fmt="%.2f")
            ax.yaxis.grid(True, color='#EEEEEE')
            tick_list = list(map(lambda x: x, range(0, math.ceil(max(bot)) + 2, 1)))
            ax.yaxis.set_ticks(tick_list)
            ax.set_xticks(name_days)
            ax.set_xticklabels(name_days, rotation=22)
            ax.set_ylabel("Hours")
            ax.set_title(f"Hours Worked - {year} -W{week}")
            ax.text(2, max(bot)+0.5, f"from - {start_date} till {end_date} ")
            ax.legend(bbox_to_anchor=(0.7, 1), loc='upper left', ncol=1, fontsize=6, borderaxespad=1.)
            self.WeeklyPlot_widget.canvas.draw()

    def TotalPlot(self, df, df_kpi):
        self.TotalPlot_widget.canvas.fig.clf()
        ax =  self.TotalPlot_widget.canvas.fig.add_subplot(111)

        _Project_IDs = df["Project_ID"].unique()
        figure = sns.FacetGrid(data=df, hue='Project_ID', hue_order=_Project_IDs)

        figure.map(ax.step, 'Date', 'Hours', linewidth=5, alpha=0.6, marker=".", markersize=15, label=[_Project_IDs])
        #TODO: fix this week concat with date range (is the x date axis flexible or depicts it every week)
        min_week = min(df["Date"].dt.isocalendar().week)
        max_week = max(df["Date"].dt.isocalendar().week)
        week_list = list(map(lambda x: x, range(min_week, max_week+1, 1)))


        if sum(df["Hours"]) != 0:
            ax.yaxis.grid(True, color='#EEEEEE')

            #tick_list = list(map(lambda x: x, range(0, math.ceil(max(df["Hours"])) + 10, 5 )))
            #ax.yaxis.set_ticks(tick_list)
            ax.set_ylabel("Hours Worked")
            ax.set_ylim([0, max(df["Hours"]) + 1])
            ax.spines[["top"]].set_visible(False)

            # if len(tick_list) > 1:
            #     step = 100/ (len(tick_list)-1)
            # else:
            #     step = 20

            ax2 = ax.twinx()
            ax2.plot(df_kpi["Date"], df_kpi["Billable"].astype(float), marker="x", markersize=10, c="black", linestyle=":", label="Billability")
            ax2.set_ylim([0, 100])
            #ax2.yaxis.set_ticks(np.linspace(ax2.get_yticks()[0], ax2.get_yticks()[-1], len(ax.get_yticks()+1)))
            #ax2.yaxis.set_ticks(list(map(lambda x: x, range(0, 100, int(step)))))
            ax2.set_ylabel("Billability (%)")
            ax2.spines[["top"]].set_visible(False)

            handles1, labels1 = ax.get_legend_handles_labels()
            handles2, labels2 = ax2.get_legend_handles_labels()
            handles = handles1 + handles2
            labels= labels1 + labels2

            labels = pd.unique(labels)
            ids = list(map(lambda x: x, range(0, len(labels), 1)))

            handles = [handles[i] for i in ids]
            ax.legend(handles, labels, bbox_to_anchor=(0, 1.05), loc='center left', ncol=6, fontsize=5,
                                                  borderaxespad=0)


        self.TotalPlot_widget.canvas.draw()
