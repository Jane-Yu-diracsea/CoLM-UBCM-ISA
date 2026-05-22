#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import numpy as np
import os
import pandas as pd

# =============================================================================
# 绘图风格
# =============================================================================
plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 13,
    'axes.labelsize': 16,
    'axes.titlesize': 18,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'legend.fontsize': 10,
    'figure.dpi': 600,
    'savefig.dpi': 600,
    'axes.edgecolor': 'black',
    'axes.linewidth': 0.9,
    'axes.facecolor': 'white',
    'figure.facecolor': 'white',
    'legend.frameon': False,
})

# =============================================================================
# 文件路径
# =============================================================================
file_gaia = "/stu02/yuxr24/CoLM-UBCM-ISA/output/NL-Amsterdam_GAIA_hourly/history/NL-Amsterdam_GAIA_hourly_hist_2019.nc"
file_gisa = "/stu02/yuxr24/CoLM-UBCM-ISA/output/NL-Amsterdam_GISA_hourly/history/NL-Amsterdam_GISA_hourly_hist_2019.nc"
file_gisd = "/stu02/yuxr24/CoLM-UBCM-ISA/output/NL-Amsterdam_GISD_hourly/history/NL-Amsterdam_GISD_hourly_hist_2019.nc"
file_wsf  = "/stu02/yuxr24/CoLM-UBCM-ISA/output/NL-Amsterdam_WSF_hourly/history/NL-Amsterdam_WSF_hourly_hist_2019.nc"
file_orig = "/stu02/yuxr24/CoLM-UBCM-ISA/output/NL-Amsterdam_sitedata/history/NL-Amsterdam_sitedata_hist_2019.nc"

file_obs  = "/tera12/yuanhua/data/CoLMpointdata/Urban-PLUMBER2/Observation/NL-Amsterdam_clean_observations_v1.nc"

output_dir = "/stu02/yuxr24/CoLM-UBCM-ISA/pictures/NL-Amsterdam_compare"
os.makedirs(output_dir, exist_ok=True)

# =============================================================================
# 时差设置
# =============================================================================
TIME_SHIFT_HOURS = 2

# =============================================================================
# 数据集
# =============================================================================
datasets = {
    "GAIA": file_gaia,
    "GISA": file_gisa,
    "GISD30": file_gisd,
    "WSF Evolution": file_wsf,
    "SiteData": file_orig
}

colors = {
    "GAIA": "#00317F",
    "GISA": "#B5374E",
    "GISD30": "#DB9850",
    "WSF Evolution": "#85B7D9",
    "SiteData": "#6BB48F"
}

# =============================================================================
# 读取模拟数据
# =============================================================================
ds = {}

for name, path in datasets.items():

    if os.path.exists(path):

        try:
            ds[name] = xr.open_dataset(path, engine='netcdf4')
            print(f"[加载成功] {name}")

        except Exception as e:
            print(f"[失败] {name}: {e}")

if len(ds) == 0:
    raise SystemExit("❌ 无有效模拟数据")

# =============================================================================
# 读取 OBS
# =============================================================================
obs_ds = None

if os.path.exists(file_obs):
    obs_ds = xr.open_dataset(file_obs)
    print("加载 OBS")

# =============================================================================
# 时间转换（模拟 + OBS）
# =============================================================================
for name in ds:
    old_time = ds[name].time.values
    new_time = pd.DatetimeIndex(old_time) + pd.Timedelta(hours=TIME_SHIFT_HOURS)
    ds[name] = ds[name].assign_coords(time=new_time)

if obs_ds is not None:
    old_time = obs_ds.time.values
    new_time = pd.DatetimeIndex(old_time) + pd.Timedelta(hours=TIME_SHIFT_HOURS)
    obs_ds = obs_ds.assign_coords(time=new_time)

# =============================================================================
# 夏季筛选
# =============================================================================
for name in ds:
    ds[name] = ds[name].sel(
        time=slice("2019-06-01", "2019-08-31")
    )

if obs_ds is not None:
    obs_ds = obs_ds.sel(
        time=slice("2019-06-01", "2019-08-31")
    )

# =============================================================================
# 观测QC
# =============================================================================
if obs_ds is not None:

    if "Qh_qc" in obs_ds:
        obs_ds["Qh"] = obs_ds["Qh"].where((obs_ds["Qh_qc"] == 0) | (obs_ds["Qh_qc"] == 1))

    if "LWup_qc" in obs_ds:
        obs_ds["LWup"] = obs_ds["LWup"].where((obs_ds["LWup_qc"] == 0) | (obs_ds["LWup_qc"] == 1))

    if "Qh" in obs_ds:
        obs_ds["Qh"] = obs_ds["Qh"].where(obs_ds["Qh"] != -999)

    if "LWup" in obs_ds:
        obs_ds["LWup"] = obs_ds["LWup"].where(obs_ds["LWup"] != -999)

# =============================================================================
# 变量
# =============================================================================
target_vars = ["f_olrg", "fsen", "f_t_grnd"]

# =============================================================================
# 主循环
# =============================================================================
for var in target_vars:

    print(f"\n===== Processing: {var} =====")

    data_all = {}

    # =========================================================================
    # 模拟数据
    # =========================================================================
    for name, d in ds.items():

        try:

            if var == "fsen":

                comps = [
                    "f_fsengimp",
                    "f_fsengper",
                    "f_fsenurbl",
                    "f_fsenroof",
                    "f_fsenwsun",
                    "f_fsenwsha"
                ]

                comp_data = [
                    d[v].where(d[v] != -1.e36)
                    for v in comps if v in d
                ]

                if not comp_data:
                    continue

                data = xr.concat(comp_data, dim="c").sum(dim="c")

            else:

                if var not in d:
                    continue

                data = d[var].where(d[var] != -1.e36)

            if "patch" in data.dims:
                data = data.isel(patch=0)

            data_all[name] = data

        except Exception as e:
            print(f"[失败] {name} | {var}: {e}")

    # =========================================================================
    # OBS：
    # =========================================================================
    if obs_ds is not None:

        if var == "fsen" and "Qh" in obs_ds:
            data_all["OBS"] = obs_ds["Qh"]

        if var == "f_olrg" and "LWup" in obs_ds:
            data_all["OBS"] = obs_ds["LWup"]

        if var == "f_t_grnd":
            print("[信息] 地表温度无观测数据对比")

    if len(data_all) == 0:
        print(f"[跳过] {var}")
        continue

    hourly = {}

    for name, data in data_all.items():

        if name == "OBS":
            continue

        hourly[name] = data.groupby(data.time.dt.hour).mean()

    # =========================================================================
    # OBS：
    # =========================================================================
    obs_series = None

    if "OBS" in data_all:

        obs = data_all["OBS"]


        obs_hour = obs.time.dt.hour
        obs_min  = obs.time.dt.minute

        obs_half_hour = obs_hour + obs_min / 60.0


        df_obs = pd.DataFrame({
            "time": obs_half_hour.values,
            "value": obs.values
        })


        obs_series = None

        if "OBS" in data_all:

            obs = data_all["OBS"]

            hour = obs.time.dt.hour.values
            minute = obs.time.dt.minute.values

            # 只保留 :30
            mask = (minute == 30)

            df = pd.DataFrame({
                "hour": hour[mask],
                "value": obs.values[mask]
            }).dropna()

            # 多年平均（每个 hour 一个 :30 值）
            obs_clim = df.groupby("hour")["value"].mean()

            # x = 半小时位置（关键）
            x = obs_clim.index.values + 0.5
            y = obs_clim.values

            obs_series = (x, y)

        obs_clim = obs_clim.interpolate(limit_direction="both")

    # =========================================================================
    # 最大差异
    # =========================================================================
    max_diff = None
    max_hour = None
    max_dataset = None
    obs_value = None
    model_value = None

    if "SiteData" in hourly:

        ref = hourly["SiteData"].values

        for h in range(24):

            ref_val = ref[h]
            if np.isnan(ref_val):
                continue

            for name in ["GAIA", "GISA", "GISD30", "WSF Evolution"]:

                if name not in hourly:
                    continue

                m = hourly[name].values[h]
                if np.isnan(m):
                    continue

                diff = m - ref_val

                if max_diff is None or abs(diff) > abs(max_diff):
                    max_diff = diff
                    max_hour = h
                    max_dataset = name
                    obs_value = ref_val
                    model_value = m

    # =========================================================================
    # 绘图
    # =========================================================================
    fig, ax = plt.subplots(figsize=(4.5, 3))

    hours = np.arange(24)

    # =========================================================================
    # 模拟曲线：
    # =========================================================================
    for name in ["GAIA", "GISA", "GISD30", "WSF Evolution", "SiteData"]:

        if name not in hourly:
            continue

        ax.plot(
            hours + 0.5,
            hourly[name].values,
            color=colors[name],
            lw=1.3,
            label=name
        )

    # =========================================================================
    # OBS：
    # =========================================================================
    if obs_series is not None:

        ax.plot(
            obs_series[0],
            obs_series[1],
            color="black",
            linestyle="--",
            lw=1.2,
            label="OBS"
        )

    # =========================================================================
    # 最大差异箭头
    # =========================================================================
    if max_dataset is not None:

        if var == "f_t_grnd":
            arrow_offset = 0.5
        else:
            arrow_offset = 5

        ax.annotate(
            "",
            xy=(max_hour + 0.5, model_value + arrow_offset),
            xytext=(max_hour + 0.5, obs_value - arrow_offset),
            arrowprops=dict(
                arrowstyle="<->",
                color="red",
                lw=1.2,
                mutation_scale=12
            )
        )

        y_mid = 0.5 * (model_value + obs_value)
        y_range = ax.get_ylim()[1] - ax.get_ylim()[0]

        ax.text(
            max_hour + 1.5,
            y_mid + 0.01 * y_range,
            f"Δmax={max_diff:.1f}",
            ha="center",
            fontsize=13
        )

    # =========================================================================
    # 轴设置
    # =========================================================================
    if var == "f_olrg":
        ax.set_ylabel("LW↑")
        unit = r"W m$^{-2}$"
    elif var == "fsen":
        ax.set_ylabel("H")
        unit = r"W m$^{-2}$"
    else:
        ax.set_ylabel(r"$T_{ground}$")
        unit = "K"

    ax.text(-0.01, 1.01, unit, transform=ax.transAxes)

    ax.set_xlabel("Hour of Day")
    ax.set_xticks(np.arange(0, 24, 2))
    ax.set_xlim(0, 24)

    ax.set_title("NL-Amsterdam")

    ax.legend(loc="best", fontsize=10)

    fig.tight_layout()

    save_path = os.path.join(output_dir, f"{var}_diurnal_shifted.png")
    plt.savefig(save_path, dpi=1200, bbox_inches="tight")
    plt.close()

    print(f"[保存] {save_path}")

# =============================================================================
print("\n✅ 完成")
