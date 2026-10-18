# 黑珍珠餐厅数据分析

本项目分析233家黑珍珠上榜餐厅。餐厅信息和公开评分字段由人工从大众点评/美团页面整理。

## 项目定位

数据整理和统计分析先完成，文字报告后形成。本仓库只保留数据、代码、结果和方法说明。

## 下载数据

| 文件 | 用途 |
|---|---|
| [`data/public/black_pearl_restaurants.csv`](data/public/black_pearl_restaurants.csv) | 标准分析版，适合 Python、R 和 SQL |
| [`data/public/black_pearl_restaurants.xlsx`](data/public/black_pearl_restaurants.xlsx) | 单工作表 Excel 版，适合直接查看和筛选 |
| [`data/raw/black_pearl_2024.xlsx`](data/raw/black_pearl_2024.xlsx) | 原始工作簿，包含历史 Excel 统计输出 |

公开版每行一家餐厅，包含稳定 ID、规范化中英文地区和城市、原始标签，以及拆分后的菜系字段。无标题的“食材评分”备注已转为数值字段；`hello` 列未保留，因为它等于收藏量除以1,000。

数据来源、覆盖范围和使用注意事项见 [`DATASET_CARD.md`](DATASET_CARD.md)，字段定义见 [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md)。

## 主要结果

总评分对口味、环境和服务评分的 OLS 模型为：

$$
\widehat{总评分}=0.1817+0.6174(口味)+0.1963(环境)+0.1436(服务)
$$

- $R^2=0.8925$，调整后 $R^2=0.8911$。
- 标准化系数约为0.676、0.189和0.151。
- 使用 HC3 稳健标准误后，口味和环境仍显著；服务评分为边缘显著（$p=0.051$）。
- VIF 介于2.54和4.38之间。
- 奖项次数的配对 Wilcoxon 检验 $p=1.51\times10^{-5}$，Spearman $\rho=0.709$。
- 地区与菜系的 Cramér's V=0.616，但97.1%的期望频数小于5。5,000次置换中没有超过观测统计量的结果，因此 $1/5001$ 只是蒙特卡洛分辨率下界，不是精确总体 p 值。
- 钻级样本不平衡：一钻198家、二钻30家、三钻5家。

这些结果描述的是手工样本中的关联，不能解释为因果关系，也不能据此声称还原了黑珍珠内部评选权重。

## 数据注意事项

- 1条记录缺失菜系。
- 有3组“同城同名”键重复，保留待人工确认，没有静默删除。
- 城市字段中有2条 `江西 Jiangxi`，它是省级标签；公开版保留并明确说明。
- 精确采集日期和逐条来源链接没有留存，本项目不会补写或猜测。

## 运行

建议使用 Python 3.12：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/analysis.py
python -m unittest discover -s tests -v
```

完整的可运行分析见 `notebooks/black_pearl_analysis.ipynb`。
