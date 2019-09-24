# -*-coding: utf-8 -*-
"""The sleep rhythm obtained with fitbit is displayed as a double plot actogram.
"""


import datetime
import glob
import json
import os

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd


def load_sleep_time(file_path_list):
    sleep_start_txt, sleep_end_txt = [], []
    # すべてのファイルから睡眠開始と終了時刻を取り込む
    for file_path in file_path_list:
        raw_data_sleep = json.load(open(file_path))
        for r_i in raw_data_sleep:
            sleep_start_txt.append(r_i.get("startTime"))
            sleep_end_txt.append(r_i.get("endTime"))
    # dataframe形式かつdatatime形式にする．
    sleep_pd = pd.DataFrame({"start": sleep_start_txt, "end": sleep_end_txt})
    for i in sleep_pd.columns:
        sleep_pd[i] = pd.to_datetime(sleep_pd[i], format="%Y-%m-%dT%H:%M:%S.000")
    sleep_pd = sleep_pd.sort_values(by=["start"], ascending=True)
    sleep_pd = sleep_pd.reset_index(drop=True)
    return sleep_pd


def make_sleep0_wake1(file_path_list, start="all", end="all"):
    sleep_point = load_sleep_time(file_path_list)
    # start と endを作成し，いらないデータを削除する．
    if start == "all":
        start = sleep_point.iloc[0]["start"]
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        sleep_point = sleep_point[sleep_point["start"] >= start]
    if end == "all":
        end = sleep_point.iloc[-1]["end"]
        end = end.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        sleep_point = sleep_point[
            sleep_point["end"] <= end + datetime.timedelta(days=1)
        ]
    # 睡眠時間をstartからの分で表記
    sleep_interval = sleep_point - start
    for i in sleep_interval.columns:
        sleep_interval[i] = sleep_interval[i].dt.total_seconds() // 60
    sleep_interval = sleep_interval.astype("uint64")
    # 睡眠時間を01のリストで表示．
    measure_m = int((end - start).days + 1) * 24 * 60
    sleep0_wake1 = np.zeros((measure_m), dtype=np.uint) + 1
    for _index, interval_i in sleep_interval.iterrows():
        sleep0_wake1[interval_i["start"] : interval_i["end"]] = 0
    return sleep0_wake1, start, end


def double_plot(file_path_list, start="all", end="all"):
    sleep0_wake1, start, end = make_sleep0_wake1(file_path_list, start=start, end=end)
    # 整形
    index = np.tile(np.arange((48 * 60), dtype="uint64"), ((end - start).days, 1))
    index = (index.T + np.arange(0, (end - start).days * 24 * 60, 24 * 60)).T.astype(
        "uint64"
    )
    plot01 = sleep0_wake1[index] * 255
    # plot開始
    fig, ax = plt.subplots()
    ax.imshow(plot01, aspect="auto", interpolation="none")
    # ax.pcolorfast(plot01)

    ax.set_xticks(np.arange(5) * 720)
    ax.set_xticklabels(np.arange(5) * 12)

    y_index = pd.date_range(start=start, end=end, freq="D").strftime("%y-%m-%d").values
    y_ticks = np.linspace(0, plot01.shape[0], 6).astype(np.uint64)
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_index[y_ticks])
    plt.tight_layout()
    if not os.path.exists("result"):
        os.makedirs("result")
    plt.savefig(os.path.join("result", y_index[0] + "_" + y_index[-1] + ".pdf"))

    plt.savefig(
        os.path.join("result", y_index[0] + "_" + y_index[-1] + ".png"),
        format="png",
        dpi=1000,
    )
    # plt.yticks()


file_path_list = glob.glob("test_data/sleep-*.json")
double_plot(file_path_list, start=datetime.datetime(2019, 1, 1), end="all")
