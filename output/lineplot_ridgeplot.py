#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量绘制各站点 runoff 极端值 KDE（固定阈值 >15 mm/h）
- 同一站点同一数据源下可能有多个年份文件 -> 自动按 time 拼接
- 支持数据源：GAIA, GISA, GISD, WSF, ORIG（ORIG 作为 SiteData）
- 对每个站点：
    1) 读取并拼接每个数据源的所有文件
    2) 对存在的 data source 求时间交集
    3) 在交集时间段内提取 f_rnof, 转换为 mm/h
    4) 只保留 f_rnof > fixed_threshold
    5) 即使为空，也保留 Y 轴（不绘制 KDE）
"""

import os
import glob
import re
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde


plt.rcParams.update({
    'font.size': 13,
    'axes.labelsize': 16,
    'axes.titlesize': 18,
    'xtick.labelsize': 13,
    'ytick.labelsize': 13,
    'legend.fontsize': 12
})


base_dir = "/stu02/yuxr24/CoLM-UBCM-ISA/output/"
output_dir = "/stu02/yuxr24/CoLM-UBCM-ISA/pictures/runoff_KDE_allstations"
os.makedirs(output_dir, exist_ok=True)

datasets_pattern = {
    "ORIG": "*_sitedata/history/*.nc",
    "GAIA": "*_GAIA_hourly/history/*.nc",
    "GISA": "*_GISA_hourly/history/*.nc",
    "GISD": "*_GISD_hourly/history/*.nc",
    "WSF":  "*_WSF_hourly/history/*.nc",
}

colors = {
    "SiteData": "#6BB48F",
    "GAIA": "#00317F",
    "GISA": "#B5374E",
    "GISD": "#DB9850",
    "WSF":  "#85B7D9"
}


target_var = "f_rnof"

fixed_threshold = 10.0



def extract_station_name(filepath):
    m = re.search(r"/([A-Za-z0-9\-]+)_(?:hourly|GAIA|GISA|GISD|WSF)", filepath)
    if m:
        return m.group(1)
    fname = os.path.basename(filepath)
    m2 = re.match(r"([A-Za-z0-9\-]+)_", fname)
    return m2.group(1) if m2 else "Unknown"


def find_files_for_station(base_dir, station, src_key):
    pattern = datasets_pattern[src_key]
    fullpat = os.path.join(base_dir, pattern)
    all_matches = glob.glob(fullpat)
    station_files = [f for f in all_matches if station in f]
    station_files.sort()
    return station_files


def open_and_concat(paths):
    if not paths:
        return None
    try:
        return xr.open_mfdataset(paths, combine='by_coords', parallel=False)
    except Exception:
        try:
            ds_list = [xr.open_dataset(p) for p in paths]
            return xr.concat(ds_list, dim="time",
                             data_vars="minimal",
                             coords="minimal")
        except Exception as e:
            print(f"    ⚠ open/concat 失败：{e}")
            return None


def adjust_timecoords(ds_obj, offset_hours=0):
    try:
        time = xr.decode_cf(ds_obj).time
    except Exception:
        time = ds_obj["time"]
    time_pd = pd.to_datetime(time.values) + pd.Timedelta(hours=offset_hours)
    return ds_obj.assign_coords(time=time_pd)


# ========== 主流程 ==========
all_files = []
for key, pat in datasets_pattern.items():
    all_files.extend(glob.glob(os.path.join(base_dir, pat)))

if not all_files:
    raise SystemExit("未找到任何数据文件，请检查 base_dir 与通配符模式。")

station_files = {}
for f in all_files:
    st = extract_station_name(f)
    station_files.setdefault(st, []).append(f)

print(f"🔍 发现站点数量：{len(station_files)}")


for station in station_files.keys():
    print("\n===================================")
    print(f"▶ 正在处理站点：{station}")
    print("===================================")

    ds_sources = {}
    for src in datasets_pattern.keys():
        paths = find_files_for_station(base_dir, station, src)
        if not paths:
            continue

        ds = open_and_concat(paths)
        if ds is None:
            continue

        ds = adjust_timecoords(ds, offset_hours=2)

        if target_var not in ds.variables:
            print(f"    ⚠ {src}: 不含 {target_var}")
            continue

        key = "SiteData" if src == "ORIG" else src
        ds_sources[key] = ds
        print(f"  - {key}: {len(paths)} files loaded")

    if not ds_sources:
        print("⚠ 无有效数据源，跳过")
        continue

    # ===== 时间交集 =====
    starts = [pd.to_datetime(ds_sources[k].time.values).min()
              for k in ds_sources]
    ends = [pd.to_datetime(ds_sources[k].time.values).max()
            for k in ds_sources]

    t_start, t_end = max(starts), min(ends)
    if t_start >= t_end:
        print("⚠ 时间无交集，跳过")
        continue

    print(f"  · 共同时间段：{t_start.date()} ~ {t_end.date()}")

    available = list(ds_sources.keys())

    # ===== 提取 runoff =====
    data_all = {}
    for name, ds0 in ds_sources.items():
        ds_slice = ds0.sel(time=slice(t_start, t_end))
        var = ds_slice[target_var].where(ds_slice[target_var] != -1.e36) * 3600.0

        if "patch" in var.dims:
            var = var.isel(patch=0)

        try:
            df = var.to_dataframe().reset_index().set_index("time").sort_index()
        except Exception:
            data_all[name] = None
            continue

        df = df[df[target_var] > fixed_threshold]

        if df.empty:
            print(f"    ⚠ {name}: 无 f_rnof > {fixed_threshold}（仅保留Y轴）")
            data_all[name] = None
            continue

        data_all[name] = df
        print(f"    · {name}: 有效点数 {len(df)}")

    # ===== 绘图 =====
    y_base = np.arange(len(available))
    fig, ax = plt.subplots(figsize=(4.5, 3))

    for i, name in enumerate(available):
        df = data_all.get(name)
        color = colors.get(name, "#999999")

        # ===== 情况 1：存在数据源，但 >threshold 为空 → 画“占位脊线” =====
        if df is None or len(df) < 2:
            # 在阈值右侧画一条很短、很浅的水平线作为占位
            x0 = fixed_threshold * 1.05
            x1 = fixed_threshold * 1.25
            ax.plot(
                [x0, x1],
                [y_base[i] + 0.02, y_base[i] + 0.02],
                color=color,
                lw=0.1,
                alpha=0.01
            )
            continue

        # ===== 情况 2：有 >threshold 数据 → 正常画 KDE =====
        vals = df[target_var].values
        kde = gaussian_kde(vals)

        xs_max = max(vals.max(), fixed_threshold * 1.2)
        xs = np.linspace(fixed_threshold, xs_max * 1.25, 300)

        ys = kde(xs)
        ys = ys / ys.max() * 0.8

        ax.fill_between(xs, y_base[i], y_base[i] + ys,
                        color=color, alpha=0.5)
        ax.plot(xs, y_base[i] + ys, color=color, lw=0.9)


        vals = df[target_var].values
        kde = gaussian_kde(vals)

        xs_max = max(vals.max(), fixed_threshold * 1.2)
        xs = np.linspace(fixed_threshold, xs_max * 1.25, 300)

        ys = kde(xs)
        ys = ys / ys.max() * 0.8

        color = colors.get(name, "#999999")
        ax.fill_between(xs, y_base[i], y_base[i] + ys,
                        color=color, alpha=0.25)
        ax.plot(xs, y_base[i] + ys, color=color, lw=0.9)

    ax.set_yticks(y_base + 0.4)
    ax.set_yticklabels(available)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Runoff (mm/h)")
    ax.set_title(f"{station}")

    ax.axvline(fixed_threshold, color="k", ls="--", lw=0.8, alpha=0.6)

    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_linewidth(0.8)

    fig.tight_layout()
    fig.savefig(
        os.path.join(output_dir, f"{station}_KDE_extreme_fixed{int(fixed_threshold)}.png"),
        dpi=600, bbox_inches="tight"
    )
    plt.close()

    print("  图像已保存")

print("\n🎉 全部站点处理完成")
