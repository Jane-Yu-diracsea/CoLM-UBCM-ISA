import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import numpy as np
import os

# === 绘图风格 ===
plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 13,
    'axes.labelsize': 16,
    'axes.titlesize': 18,
    'xtick.labelsize': 13,
    'ytick.labelsize': 13,
    'legend.fontsize': 12,
    'figure.dpi': 600,
    'savefig.dpi': 600,
    'axes.edgecolor': 'black',
    'axes.linewidth': 0.9,
    'axes.facecolor': 'white',
    'figure.facecolor': 'white',
    'legend.frameon': False,
})

# === 文件路径 ===
file_gaia = "/stu02/yuxr24/CoLM202X_ISA/output/NL-Amsterdam_GAIA_hourly/history/NL-Amsterdam_GAIA_hourly_hist_2019.nc"
file_gisa = "/stu02/yuxr24/CoLM202X_ISA/output/NL-Amsterdam_GISA_hourly/history/NL-Amsterdam_GISA_hourly_hist_2019.nc"
file_gisd = "/stu02/yuxr24/CoLM202X_ISA/output/NL-Amsterdam_GISD_hourly/history/NL-Amsterdam_GISD_hourly_hist_2019.nc"
file_wsf  = "/stu02/yuxr24/CoLM202X_ISA/output/NL-Amsterdam_WSF_hourly/history/NL-Amsterdam_WSF_hourly_hist_2019.nc"
file_orig = "/stu02/yuxr24/CoLM202X_ISA/output/NL-Amsterdam_sitedata/history/NL-Amsterdam_sitedata_hist_2019.nc"

output_dir = "/stu02/yuxr24/CoLM202X_ISA/pictures/NL-Amsterdam_compare"
os.makedirs(output_dir, exist_ok=True)

datasets = {
    "GAIA": file_gaia,
    "GISA": file_gisa,
    "GISD": file_gisd,
    "WSF": file_wsf,
    "SiteData": file_orig
}

colors = {
    "GAIA": "#00317F",
    "GISA": "#B5374E",
    "GISD": "#DB9850",
    "WSF": "#85B7D9",
    "SiteData": "#6BB48F"
}

# === 读取数据（安全加载，自动跳过不存在文件）===
ds = {}
for name, path in datasets.items():
    if not os.path.exists(path):
        print(f"[跳过] 文件不存在: {path}")
        continue
    try:
        ds[name] = xr.open_dataset(path, engine='netcdf4')
        print(f"[加载成功] {name}")
    except Exception as e:
        print(f"[错误] {name} 打开失败 -> {e}")
        continue

if len(ds) == 0:
    raise SystemExit("[❌] 没有找到任何输入文件")

# === 时间修正（UTC+2） ===
for name, d in ds.items():
    if "time" in d.variables:
        ds[name]["time"] = xr.decode_cf(d[["time"]]).time + np.timedelta64(2, "h")

# === 夏季时间段 ===
for name in ds:
    ds[name] = ds[name].sel(time=slice("2019-06-01", "2019-08-31"))

# === 目标变量 ===
target_vars = ["f_tref", "fsen"]

for var in target_vars:
    data_all = {}

    for name, d in ds.items():
        try:
            if var == "fsen":
                comps = [
                    "f_fsengimp",
                    "f_fsengper",
                    "f_fsenurbl",
                    "f_fsenroof",
                    "f_fsenwsun",
                    "f_fsenwsha",
                ]
                existing = [v for v in comps if v in d.variables]
                if not existing:
                    print(f"[WARN] {name}: 没有任何有效 fsen 分量，已跳过")
                    continue

                comp_data = [d[v].where(d[v] != -1.e36) for v in existing]
                data = xr.concat(comp_data, dim="component").sum(dim="component", skipna=True)

            else:
                if var not in d.variables:
                    print(f"[WARN] {name}: 不包含变量 {var}，已跳过")
                    continue
                data = d[var].where(d[var] != -1.e36)

            if "patch" in data.dims:
                data = data.isel(patch=0)

            data_all[name] = data

        except Exception as e:
            print(f"[ERROR] {name}: 读取 {var} 失败 -> {e}")
            continue

    if "SiteData" not in data_all:
        print(f"[跳过] {var}: 缺少 SiteData（观测或参考数据）")
        continue

    if len(data_all) < 2:
        print(f"[跳过] {var}: 有效数据集不足（{list(data_all.keys())}）")
        continue

    # === 逐小时统计 ===
    hourly_stats = {}
    for name, data in data_all.items():
        g = data.groupby(data.time.dt.hour)
        hourly_stats[name] = {
            "mean": g.mean(),
            "p05": g.quantile(0.05),
            "p95": g.quantile(0.95),
        }

    # === 找最大差异（按小时） ===
    site_mean = hourly_stats["SiteData"]["mean"].values
    max_diff = None
    max_hour = None
    max_dataset = None
    isa_value = None
    site_value = None

    for h in range(24):
        site_val = site_mean[h]
        for name, stats in hourly_stats.items():
            if name == "SiteData":
                continue
            isa_val = stats["mean"].values[h]
            if np.isnan(isa_val) or np.isnan(site_val):
                continue
            diff = isa_val - site_val
            if max_diff is None or abs(diff) > abs(max_diff):
                max_diff = diff
                max_hour = h
                max_dataset = name
                isa_value = isa_val
                site_value = site_val

    if max_dataset is not None and max_hour is not None:
        print(f"[{var}] 最大差异: {max_dataset} vs SiteData | {max_hour:02d}:00 | Δ = {max_diff:.2f}")
    else:
        print(f"[{var}] 没有找到有效的最大差异数据")

    # === 绘图 ===
    hours = np.arange(24)
    fig, ax = plt.subplots(figsize=(4.5, 3))

    for name in ["GAIA", "GISA", "GISD", "WSF", "SiteData"]:
        if name not in hourly_stats:
            continue
        mean = hourly_stats[name]["mean"].values
        p05  = hourly_stats[name]["p05"].values
        p95  = hourly_stats[name]["p95"].values
        ax.fill_between(hours, p05, p95, color=colors[name], alpha=0.1, linewidth=0)
        ax.plot(hours, mean, color=colors[name], linewidth=1.3, label=name)

    if max_dataset is not None:
        x = max_hour
        y_offset = -1
        y_start = site_value + y_offset
        y_end   = isa_value - y_offset
        ax.annotate(
            "",
            xy=(x, y_end),
            xytext=(x, y_start),
            arrowprops=dict(arrowstyle="<->", lw=1.0, color='red')
        )
        y_text = max(y_start, y_end) + 0.02 * (ax.get_ylim()[1] - ax.get_ylim()[0])
        ax.text(x, y_text, f"Δmax = {max_diff:.1f}", color='black', fontsize=16, ha="center", va="bottom")

    if var == "f_tref":
        ax.set_ylabel("2-m Air Temperature")
        unit = "(K)"
    else:
        ax.set_ylabel("Sensible Heat Flux")
        unit = "(W m$^{-2}$)"
    ax.text(-0.01, 1.01, unit, transform=ax.transAxes, ha="left", va="bottom", fontsize=14)
    ax.set_xlabel("Hour of Day")
    ax.set_xticks(np.arange(0, 24, 2))
    ax.set_title("NL-Amsterdam")

    y_min, y_max = ax.get_ylim()
    if abs(y_max) > 999:
        ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))

    ax.legend(loc="upper left")
    fig.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{var}_diurnalavg_2019_hourly.png"), bbox_inches="tight")
    plt.close()

print("\n✅ 所有变量绘制完成")
print(f"📁 输出目录：{output_dir}")
