import os
import re
import glob
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 7
})

# ================================
# 配置部分
# ================================
base_dir = "/stu02/yuxr24/CoLM-UBCM-ISA/output"

obs_dir = (
    "/tera12/yuanhua/data/CoLMpointdata/"
    "Urban-PLUMBER2/Observation"
)

output_dir = (
    "/stu02/yuxr24/CoLM-UBCM-ISA/pictures"
)

os.makedirs(output_dir, exist_ok=True)

datasets = {
    "GAIA":
        f"{base_dir}/*_GAIA_hourly/history/*.nc",

    "GISA":
        f"{base_dir}/*_GISA_hourly/history/*.nc",

    "GISD30":
        f"{base_dir}/*_GISD_hourly/history/*.nc",

    "WSF Evolution":
        f"{base_dir}/*_WSF_hourly/history/*.nc",

    "SiteData":
        f"{base_dir}/*_sitedata/history/*.nc",
}

stations = [
    "AU-Preston",
    "AU-SurreyHills",
    "CA-Sunset",
    "FR-Capitole",
    "GR-HECKOR",
    "KR-Jungnang",
    "KR-Ochang",
    "MX-Escandon",
    "NL-Amsterdam",
    "PL-Lipowa",
    "PL-Narutowicza",
    "SG-TelokKurau06",
    "UK-KingsCollege",
    "UK-Swindon",
    "US-Baltimore",
    "US-WestPhoenix",
]

colors = {
    "OBS": "black",
    "GAIA": "#00317F",
    "GISA": "#B5374E",
    "GISD30": "#DB9850",
    "WSF Evolution": "#85B7D9",
    "SiteData": "#6BB48F"
}

# ================================
# 提取站点名称
# ================================
def extract_station_name(filepath):

    match = re.search(
        r"/([A-Z]{2}-[A-Za-z0-9]+)_",
        filepath
    )

    return match.group(1) if match else "Unknown"


def extract_station_name_obs(filepath):

    basename = os.path.basename(filepath)

    match = re.match(
        r"([A-Z]{2}-[A-Za-z0-9]+)_",
        basename
    )

    return match.group(1) if match else "Unknown"


# ================================
# OBS 数据处理（增强版：打印有效时间和时间步长）
# ================================
def compute_obs_monthly_series(filepath, print_info=True):
    """
    OBS:
        Qle (W/m²)
        -> mm/s
        -> mm/hour
        -> monthly sum (mm/month)

    返回:
        monthly_series, time_info_dict
    """

    try:

        ds = xr.open_dataset(filepath)

        if "Qle" not in ds.variables:

            print(
                f"⚠️ 无变量 Qle: "
                f"{os.path.basename(filepath)}"
            )

            ds.close()

            return None, None

        qle = ds["Qle"]

        if "time" not in qle.dims:

            print(
                f"⚠️ 无 time 维度: "
                f"{os.path.basename(filepath)}"
            )

            ds.close()

            return None, None

        # 提取时间信息
        time_coord = ds["time"]
        time_values = pd.to_datetime(time_coord.values)
        
        # 计算时间步长（小时）
        if len(time_values) > 1:
            time_diff = np.diff(time_values)
            # 转换为小时
            time_diff_hours = time_diff.astype('timedelta64[h]').astype(float)
            median_time_step = np.median(time_diff_hours)
            unique_time_steps = np.unique(time_diff_hours)
        else:
            median_time_step = np.nan
            unique_time_steps = np.array([np.nan])
        
        # 有效时间范围
        valid_times = time_values[np.isfinite(qle.values)]
        
        if len(valid_times) > 0:
            start_time = valid_times.min()
            end_time = valid_times.max()
            n_valid = len(valid_times)
            total_times = len(time_values)
            data_coverage = (n_valid / total_times) * 100
        else:
            start_time = None
            end_time = None
            n_valid = 0
            total_times = len(time_values)
            data_coverage = 0
        
        time_info = {
            "start_time": start_time,
            "end_time": end_time,
            "n_valid": n_valid,
            "total_times": total_times,
            "data_coverage": data_coverage,
            "time_step_hours": median_time_step,
            "unique_time_steps": unique_time_steps
        }
        
        # 打印时间信息
        if print_info:
            print(f"\n  📅 OBS 时间信息 [{os.path.basename(filepath)}]:")
            print(f"     有效时间范围: {start_time} -> {end_time}")
            print(f"     有效数据点: {n_valid}/{total_times} ({data_coverage:.1f}%)")
            print(f"     时间步长: {median_time_step:.1f} 小时")
            if len(unique_time_steps) > 1:
                print(f"     注意: 检测到不同时间步长 {unique_time_steps}")

        # 删除缺测
        qle = qle.where(
            np.isfinite(qle)
        )

        Lv = 2.45e6

        # W/m² -> mm/s
        evap_mm_s = qle / Lv

        # mm/s -> mm/hour
        evap_mm_h = evap_mm_s * 3600.0

        # 月累计
        monthly_sum = evap_mm_h.resample(
            time="1ME"
        ).sum(skipna=True)

        # 统计每个月有效值数量
        valid_count = evap_mm_h.resample(
            time="1ME"
        ).count()

        # 有效值为0的月份剔除
        monthly_sum = monthly_sum.where(
            valid_count > 0
        )

        monthly_sum = monthly_sum.dropna(
            dim="time"
        )

        ds.close()

        return monthly_sum, time_info

    except Exception as e:

        print(f"❌ OBS 文件读取失败 {filepath}")
        print(e)

        return None, None


# ================================
# 模拟数据处理
# ================================
def compute_sim_monthly_series(
    filepath,
    obs_months=None
):
    """
    模拟:
        f_fevpa (mm/s)
        -> mm/hour
        -> monthly sum

    仅保留 OBS 存在的月份
    """

    try:

        ds = xr.open_dataset(filepath)

        if "f_fevpa" not in ds:

            print(
                f"⚠️ 无变量 f_fevpa: "
                f"{os.path.basename(filepath)}"
            )

            ds.close()

            return None

        da = ds["f_fevpa"]

        if "time" not in da.dims:

            print(
                f"⚠️ 无 time 维度: "
                f"{os.path.basename(filepath)}"
            )

            ds.close()

            return None

        # mm/s -> mm/hour
        da_hourly = da * 3600.0

        # 月累计
        monthly_sum = da_hourly.resample(
            time="1ME"
        ).sum(skipna=True)

        # 转换月份
        sim_months = pd.to_datetime(
            monthly_sum["time"].values
        ).to_period("M")

        # 保留 OBS 存在月份
        if obs_months is not None:

            mask = np.isin(
                sim_months,
                obs_months
            )

            monthly_sum = monthly_sum.isel(
                time=mask
            )

        monthly_sum = monthly_sum.dropna(
            dim="time"
        )

        ds.close()

        return monthly_sum

    except Exception as e:

        print(f"❌ 文件读取失败 {filepath}")
        print(e)

        return None


# ================================
# 主流程
# ================================
records = []

obs_month_dict = {}
obs_time_info_dict = {}  # 存储时间信息

# ================================
# 读取 OBS
# ================================
obs_pattern = os.path.join(
    obs_dir,
    "*_clean_observations_v1.nc"
)

obs_files = sorted(glob.glob(obs_pattern))

if obs_files:

    print(f"\n📡 找到 {len(obs_files)} 个 OBS 文件")

    for obs_file in obs_files:

        station = extract_station_name_obs(
            obs_file
        )

        if station not in stations:

            print(f"⚠️ 跳过站点: {station}")

            continue

        monthly_series, time_info = (
            compute_obs_monthly_series(
                obs_file,
                print_info=True  # 打印时间信息
            )
        )

        if monthly_series is None:
            continue

        # 存储时间信息
        obs_time_info_dict[station] = time_info

        mean_month = (
            monthly_series.mean().item()
        )

        obs_months = pd.to_datetime(
            monthly_series["time"].values
        ).to_period("M")

        obs_month_dict[station] = obs_months

        records.append({
            "Station": station,
            "Dataset": "OBS",
            "Value": mean_month
        })

        print(
            f"  ✅ OBS: {station} -> "
            f"{mean_month:.2f} mm/month"
        )

else:

    print("⚠️ 未找到 OBS 文件")

# ================================
# 打印 OBS 时间信息汇总
# ================================
print("\n" + "="*80)
print("📊 OBS 数据时间信息汇总")
print("="*80)

for station in stations:
    if station in obs_time_info_dict:
        info = obs_time_info_dict[station]
        print(f"\n站点: {station}")
        print(f"  有效时间范围: {info['start_time']} -> {info['end_time']}")
        print(f"  有效数据点: {info['n_valid']}/{info['total_times']} ({info['data_coverage']:.1f}%)")
        print(f"  时间步长: {info['time_step_hours']:.1f} 小时")
        if len(info['unique_time_steps']) > 1:
            print(f"  不同时间步长: {info['unique_time_steps']}")
    else:
        print(f"\n站点: {station} - 无有效 OBS 数据")

print("="*80)

# ================================
# 读取模拟数据
# ================================
for dataset_name, pattern in datasets.items():

    files = sorted(glob.glob(pattern))

    if not files:

        print(f"⚠️ 未找到文件: {dataset_name}")

        continue

    for f in files:

        station = extract_station_name(f)

        if station not in stations:
            continue

        if station not in obs_month_dict:

            print(
                f"⚠️ {station} 无 OBS 月份"
            )

            continue

        monthly_series = (
            compute_sim_monthly_series(
                f,
                obs_months=(
                    obs_month_dict[station]
                )
            )
        )

        if monthly_series is None:
            continue

        if monthly_series.size == 0:

            print(
                f"⚠️ 无共同月份: "
                f"{os.path.basename(f)}"
            )

            continue

        mean_month = (
            monthly_series.mean().item()
        )

        records.append({
            "Station": station,
            "Dataset": dataset_name,
            "Value": mean_month
        })


# ================================
# DataFrame
# ================================
df = pd.DataFrame(records)

if df.empty:
    raise ValueError("❌ 无可用数据")

df_mean = (
    df.groupby(
        ["Station", "Dataset"]
    )["Value"]
    .mean()
    .reset_index()
)

# ================================
# 输出站点结果
# ================================
print("\n📊 各站点平均值")

for station in stations:

    print(f"\n站点: {station}")

    subset = df_mean[
        df_mean["Station"] == station
    ]

    for dataset in (
        list(datasets.keys()) + ["OBS"]
    ):

        val = subset[
            subset["Dataset"] == dataset
        ]["Value"]

        val_str = (
            f"{val.values[0]:.2f}"
            if not val.empty else "NA"
        )

        print(f"  {dataset}: {val_str}")


# ================================
# 各数据集总和
# ================================
dataset_sums = (
    df_mean.groupby("Dataset")["Value"]
    .sum()
)

print("\n📊 数据集总和")

for dataset, total in dataset_sums.items():

    print(f"  {dataset}: {total:.2f}")


# ================================
# OBS 统计分析（最小修复版）
# ================================
print("\n📊 相对于 OBS 的统计指标")

compare_datasets = [
    "SiteData",
    "GAIA",
    "GISA",
    "GISD30",
    "WSF Evolution"
]

stats_records = []

obs_df = df_mean[df_mean["Dataset"] == "OBS"][["Station", "Value"]]
obs_df = obs_df.rename(columns={"Value": "OBS_Value"})

for dataset in compare_datasets:

    sim_df = df_mean[df_mean["Dataset"] == dataset][["Station", "Value"]]
    sim_df = sim_df.rename(columns={"Value": "SIM_Value"})

    merged = pd.merge(obs_df, sim_df, on="Station", how="inner")

    # ================================
    # 🔥 FIX 1：防空
    # ================================
    if merged.shape[0] < 2:
        print(f"⚠️ {dataset}: 有效站点不足，跳过")
        continue

    obs = merged["OBS_Value"].to_numpy()
    sim = merged["SIM_Value"].to_numpy()

    diff = sim - obs

    # ================================
    # 基本统计
    # ================================
    mbe = np.nanmean(diff)
    std = np.nanstd(diff, ddof=1)
    rmse = np.sqrt(np.nanmean(diff ** 2))
    mae = np.nanmean(np.abs(diff))

    # ================================
    # 🔥 FIX 2：相关系数防崩
    # ================================
    if np.std(obs) > 1e-12 and np.std(sim) > 1e-12:
        corr = np.corrcoef(obs, sim)[0, 1]
    else:
        corr = np.nan

    r2 = corr ** 2 if np.isfinite(corr) else np.nan

    stats_records.append({
        "Dataset": dataset,
        "MBE": mbe,
        "STD": std,
        "RMSE": rmse,
        "MAE": mae,
        "R": corr,
        "R2": r2
    })

    print(
        f"{dataset:15s} | "
        f"MBE={mbe:8.2f} | "
        f"STD={std:8.2f} | "
        f"RMSE={rmse:8.2f} | "
        f"MAE={mae:8.2f} | "
        f"R={corr:6.3f} | "
        f"R²={r2:6.3f}"
    )


# ================================
# 保存统计结果
# ================================
stats_df = pd.DataFrame(
    stats_records
)

stats_csv = os.path.join(
    output_dir,
    "OBS_statistics_comparison.csv"
)

stats_df.to_csv(
    stats_csv,
    index=False
)

print("\n✅ 统计结果已保存")
print(stats_csv)

# ================================
# 保存 OBS 时间信息
# ================================
obs_time_records = []
for station in stations:
    if station in obs_time_info_dict:
        info = obs_time_info_dict[station]
        obs_time_records.append({
            "Station": station,
            "Start_Time": info["start_time"],
            "End_Time": info["end_time"],
            "Valid_Data_Points": info["n_valid"],
            "Total_Data_Points": info["total_times"],
            "Data_Coverage_Percent": info["data_coverage"],
            "Time_Step_Hours": info["time_step_hours"]
        })

if obs_time_records:
    obs_time_df = pd.DataFrame(obs_time_records)
    obs_time_csv = os.path.join(
        output_dir,
        "OBS_time_information.csv"
    )
    obs_time_df.to_csv(
        obs_time_csv,
        index=False
    )
    print("\n✅ OBS 时间信息已保存")
    print(obs_time_csv)

# ================================
# 绘图
# ================================
fig, ax = plt.subplots(
    figsize=(12, 4.8)
)

datasets_order = [
    "OBS",
    "SiteData",
    "GAIA",
    "GISA",
    "GISD30",
    "WSF Evolution"
]

x = np.arange(len(stations))

bar_width = 0.14

# ================================
# 柱状图
# ================================
for i, dataset in enumerate(
    datasets_order
):

    subset = df_mean[
        df_mean["Dataset"] == dataset
    ]

    y_vals = []

    for s in stations:

        val = subset[
            subset["Station"] == s
        ]["Value"]

        y_vals.append(
            val.values[0]
            if not val.empty else 0
        )

    color = colors.get(
        dataset,
        "gray"
    )

    edgecolor = (
        "black"
        if dataset == "OBS"
        else "none"
    )

    alpha = (
        1.0
        if dataset == "OBS"
        else 0.85
    )

    label = (
        "OBS (Qle)"
        if dataset == "OBS"
        else dataset
    )

    ax.bar(
        x + i * bar_width,
        y_vals,
        width=bar_width,
        label=label,
        color=color,
        edgecolor=edgecolor,
        alpha=alpha,
        linewidth=0.5
    )

# ================================
# 图形美化
# ================================
ax.set_xticks(
    x + 2.5 * bar_width
)

ax.set_xticklabels(
    stations,
    fontsize=13,
    rotation=45,
    ha="right"
)

ax.tick_params(
    axis="y",
    labelsize=13
)

ax.set_ylabel(
    "Evapotranspiration\n"
    "(mm month$^{-1}$)",
    fontsize=15
)

# y轴留白
ymax = df_mean["Value"].max()

ax.set_ylim(
    0,
    ymax * 1.45
)

# ================================
# 统计指标文本
# ================================
stats_lines = []

for _, row in stats_df.iterrows():
    dataset = row["Dataset"]
    mbe = row["MBE"]
    rmse = row["RMSE"]
    r2 = row["R2"]
    
    stats_lines.append(
        f"{dataset} vs OBS: "
        f"MBE={mbe:.1f}, "
        f"RMSE={rmse:.1f}, "
    )

stats_text = "\n".join(stats_lines)

# ================================
# 图中添加统计信息
# ================================
ax.text(
    0.03,
    0.95,
    stats_text,
    transform=ax.transAxes,
    fontsize=12,
    va="top",
    ha="left",
    linespacing=1.4,
    bbox=dict(
        facecolor="none",
        edgecolor="none",
        alpha=0,
        boxstyle="round,pad=0"
    )
)

plt.tight_layout()

# ================================
# 保存图像
# ================================
output_path = os.path.join(
    output_dir,
    "f_fevpa_mean_monthly_comparison_with_obs.png"
)

plt.savefig(
    output_path,
    dpi=600,
    bbox_inches="tight"
)

plt.close()

print("\n✅ 图像已保存")
print(output_path)
