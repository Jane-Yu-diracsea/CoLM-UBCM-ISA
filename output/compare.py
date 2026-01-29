import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
import os

# 文件路径
file1 = "/stu02/yuxr24/CoLM202X/output/MX-Escandon_sitedata/history/MX-Escandon_sitedata_hist_2012.nc"
file2 = "/stu02/yuxr24/CoLM202X/output/MX-Escandon_GISA_hourly/history/MX-Escandon_GISA_hourly_hist_2012.nc"

# 输出路径
output_dir = "/stu02/yuxr24/CoLM202X_ISA/pictures"
os.makedirs(output_dir, exist_ok=True)  # 如果目录不存在就创建

# 变量列表
variables = [
 "f_fsena"
]

# 时间段
start_date = "2012-07-01"
end_date = "2012-07-01"

# 打开 NetCDF 文件
ds1 = xr.open_dataset(file1)
ds2 = xr.open_dataset(file2)

# 选择时间段
ds1_sel = ds1.sel(time=slice(start_date, end_date))
ds2_sel = ds2.sel(time=slice(start_date, end_date))

# 创建绘图
n_vars = len(variables)
ncols = 4
nrows = (n_vars + ncols - 1) // ncols

fig, axes = plt.subplots(nrows, ncols, figsize=(20, 10), constrained_layout=True)
axes = axes.flatten()

for i, var in enumerate(variables):
    if var in ds1_sel and var in ds2_sel:
        ax = axes[i]
        ds1_sel[var].plot(ax=ax, label='sitedata', color='blue')
        ds2_sel[var].plot(ax=ax, label='GISA_hourly', color='red')
        ax.set_title(var)
        ax.legend()
        ax.grid(True)  # 添加网格
    else:
        print(f"变量 {var} 不存在于数据集")

# 删除多余的空子图
for j in range(i+1, len(axes)):
    fig.delaxes(axes[j])

plt.suptitle("2012-06-01 to 2012-08-31 Variable Comparison", fontsize=16)

# 保存图片
output_file = os.path.join(output_dir, "old_variable_comparison_2012_summer.png")
plt.savefig(output_file, dpi=300)
print(f"图片已保存到 {output_file}")

plt.show()
