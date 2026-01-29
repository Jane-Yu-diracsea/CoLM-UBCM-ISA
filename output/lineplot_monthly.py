import os
import re
import glob
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde


plt.rcParams.update({
    "font.size": 18,
    "axes.labelsize": 18,
    "axes.titlesize": 18,
    "xtick.labelsize": 19,
    "ytick.labelsize": 20,
    "legend.fontsize": 15
})

# ================================
# 配置部分
# ================================
base_dir = "/stu02/yuxr24/CoLM202X_ISA/output"
output_dir = "/stu02/yuxr24/CoLM202X_ISA/pictures"
os.makedirs(output_dir, exist_ok=True)

datasets = {
    "GAIA": f"{base_dir}/*_GAIA_hourly/history/*.nc",
    "GISA": f"{base_dir}/*_GISA_hourly/history/*.nc",
    "GISD": f"{base_dir}/*_GISD_hourly/history/*.nc",
    "WSF":  f"{base_dir}/*_WSF_hourly/history/*.nc",
    "SiteData": f"{base_dir}/*_sitedata/history/*.nc",
}

stations = [
    "AU-Preston", "AU-SurreyHills", "CA-Sunset", "FR-Capitole",
    "GR-HECKOR", "KR-Jungnang", "KR-Ochang", "MX-Escandon","NL-Amsterdam",
    "PL-Lipowa", "PL-Narutowicza", "SG-TelokKurau06", "UK-KingsCollege",
    "UK-Swindon", "US-Baltimore", "US-WestPhoenix",
]

colors = {
    "GAIA": "#00317F",  
    "GISA": "#B5374E",  
    "GISD": "#DB9850",  
    "WSF": "#85B7D9",   
    "SiteData": "#6BB48F"   
}

# ================================
# 函数定义
# ================================
def compute_mean_monthly_value(filepath):
    """
    计算单个文件中 f_assim 的平均月总量（mm/month）
    - 原单位: mm/s
    - 先换算为 mm/hour，然后对每月累计
    - 最后对所有月取平均
    """
    try:
        ds = xr.open_dataset(filepath)
        if "f_assim" not in ds:
            print(f"⚠️ 跳过: 无变量 f_assim -> {os.path.basename(filepath)}")
            ds.close()
            return None

        da = ds["f_assim"]
        if "time" not in da.dims:
            print(f"⚠️ 跳过: 无 time 维度 -> {os.path.basename(filepath)}")
            ds.close()
            return None

        # === 单位换算: mm/s → mm/hour ===
        da_hourly = da * 3600.0

        # === 按月累积求总量 ===
        da_monthly_sum = da_hourly.resample(time="1ME").sum(skipna=True)

        # === 对所有月取平均值 ===
        mean_month_val = da_monthly_sum.mean().item()

        ds.close()
        return mean_month_val

    except Exception as e:
        print(f"❌ 文件读取出错 {filepath}: {e}")
        return None


def extract_station_name(filepath):
    """从路径中提取站点名"""
    match = re.search(r"/([A-Z]{2}-[A-Za-z0-9]+)_", filepath)
    return match.group(1) if match else "Unknown"

# ================================
# 主计算流程
# ================================
records = []

for dataset_name, pattern in datasets.items():
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"⚠️ 未找到文件: {dataset_name}")
        continue

    for f in files:
        station = extract_station_name(f)
        if station not in stations:
            continue
        mean_val = compute_mean_monthly_value(f)
        if mean_val is not None:
            records.append({
                "Station": station,
                "Dataset": dataset_name,
                "Value": mean_val
            })

df = pd.DataFrame(records)
if df.empty:
    raise ValueError("❌ 没有可用数据，请检查路径和变量名。")

# ================================
# 绘图
# ================================
df_mean = df.groupby(["Station", "Dataset"])["Value"].mean().reset_index()

# 输出每个站点每个数据集的平均值
print("\n📊 每个站点每个数据集的月平均值 (mm/month):")
for station in stations:
    print(f"\n站点: {station}")
    subset = df_mean[df_mean["Station"] == station]
    for dataset in datasets.keys():
        val = subset[subset["Dataset"] == dataset]["Value"]
        val_str = f"{val.values[0]:.2f}" if not val.empty else "NA"
        print(f"  {dataset}: {val_str}")

# 计算每个数据集在所有站点上的总和
dataset_sums = df_mean.groupby("Dataset")["Value"].sum()
print("\n📊 每个数据集在所有站点上的总和 (mm/month):")
for dataset, total in dataset_sums.items():
    print(f"  {dataset}: {total:.2f}")
    
    
# ================================
# 计算各数据集总量相对于SiteData总量的相对误差
# ================================
site_total = dataset_sums.get("SiteData", np.nan)
print("\n📊 各数据集总量相对于SiteData总量的相对误差 (%):")

dataset_total_rel_error = {}
for dataset, total in dataset_sums.items():
    if dataset == "SiteData":
        continue
    if np.isnan(site_total) or site_total == 0:
        rel_error = np.nan
    else:
        rel_error = abs(total - site_total) / site_total * 100
    dataset_total_rel_error[dataset] = rel_error
    print(f"  {dataset}: {rel_error:.2f}%")


# ================================
# 计算最大相对误差
# ================================
print("\n📊 每个站点与SiteData相比的最大相对误差 (%):")
max_rel_errors = {}

for station in stations:
    subset = df_mean[df_mean["Station"] == station]
    site_val = subset[subset["Dataset"] == "SiteData"]["Value"]
    if site_val.empty or site_val.values[0] == 0:
        print(f"  {station}: NA (SiteData缺失或为0)")
        continue
    site_val = site_val.values[0]

    # 对除SiteData以外的数据集计算相对误差
    rel_errors = []
    for dataset in datasets.keys():
        if dataset == "SiteData":
            continue
        val = subset[subset["Dataset"] == dataset]["Value"]
        if val.empty:
            continue
        error = abs(val.values[0] - site_val) / site_val * 100
        rel_errors.append(error)

    max_error = max(rel_errors) if rel_errors else np.nan
    max_rel_errors[station] = max_error
    print(f"  {station}: {max_error:.2f}%")


# ================================
# 绘图
# ================================
fig, ax = plt.subplots(figsize=(5, 12))

datasets_order = ["SiteData", "GAIA", "GISA", "GISD", "WSF"]
y = np.arange(len(stations))
bar_height = 0.15

for i, dataset in enumerate(datasets_order):
    subset = df_mean[df_mean["Dataset"] == dataset]
    x_vals = [subset[subset["Station"] == s]["Value"].values[0] if s in subset["Station"].values else 0 for s in stations]
    ax.barh(y + i * bar_height, x_vals, height=bar_height,
            label=dataset, color=colors[dataset], edgecolor="none", alpha=0.85)

# === 图形美化 ===
ax.set_yticks(y + 2 * bar_height)
ax.set_yticklabels(stations, fontsize=20, rotation=45)
ax.tick_params(axis="x", labelsize=19)
ax.invert_yaxis()
ax.set_xlabel(
    "Canopy Assimilation\nRate(mol m$^{-2}$month$^{-1}$)",
    fontsize=18
)


ax.legend(
    title="Dataset",
    fontsize=18,
    loc="center right",
    bbox_to_anchor=(1.0, 0.72)
)
# ax.grid(axis="x", linestyle="--", alpha=0.5)

plt.tight_layout()

output_path = os.path.join(output_dir, "f_assim_mean_monthly_comparison_vertical.png")
plt.savefig(output_path, dpi=600)
plt.close()
print(f"\n✅ 图像已保存到: {output_path}")

