def plot_hists(
    df,
    id_column,
    columns_to_plot,
    column_to_divide,
    specified_columns_dict={},
    logged=None,
    n_bins=None,
    without_zeros=False,
    not_outliers_percent=0,
    is_kde=False,
):
    """Plotting various distribution histograms

    Args:
        df (pd.DataFrame): Dataset
        id_column (str): column with id
        columns_to_plot (list[str]): columns to plot, unavailable would be excluded
        column_to_divide (str): column to divide for 2 histograms on each plot
        specified_columns_dict (dict, str:value, optional): here you can specify the columns and valuesthat it should have, dataset will be cutted. Defaults to {}.
        logged (bool, optional): is values to histogram need to be logged. Defaults to None.
        n_bins (int, optional): count of bins in each histogram. Defaults to None.
        without_zeros (bool, optional): if zero-values need to be excluded, each plot would be divided in 2. Defaults to False.
        not_outliers_percent (int, optional): percent of not outliers labels, outliers detected with iqr-method. Defaults to 0. Default means no outlier detection
        is_kde (bool, optional): if you need kernel density estimation (__default kde__) to be on plot. Defaults to False.

    Returns:
        figure of pyplot
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np

    # clear cols to plot
    columns_to_plot = [
        col
        for col in columns_to_plot
        if col != column_to_divide
        and col not in specified_columns_dict.keys()
        and col != id_column
    ]

    if logged is None:
        logged = []

    # slice dataset with specified cols and values
    for k, v in specified_columns_dict.items():
        if type(v) is type([1, 2]):
            df = df[df[k].isin(v)]
        else:
            df = df[df[k] == v]

    values_to_divide = df[column_to_divide].unique()

    # func to remove outliers
    def remove_outliers(values, threshold):
        diff = (100 - threshold) / 2.0
        minval, maxval = np.percentile(values, [diff, 100 - diff])
        tf_ary = (values < minval) | (values > maxval)
        return [v for i, v in enumerate(values) if not tf_ary[i]]

    # func for one col
    def plot_one_col(df, col, ax, is_log=False, add_info=""):
        for v in values_to_divide:
            vals = df[df[column_to_divide] == v][col].dropna().values
            if remove_outliers != 0:
                vals = remove_outliers(vals, not_outliers_percent)
            sns.histplot(
                vals,
                label=f"{column_to_divide} = {v}",
                kde=is_kde,  # True,
                alpha=0.35,
                log=is_log,
                ax=ax,
                stat="probability",
                bins=n_bins,
            )
        l, s = ", logged", ""
        i = f", {add_info}" if len(add_info) != 0 else ""
        ax.set_title(
            f"Distribution of {col} by {column_to_divide}{l if is_log else s}{i}"
        )
        ax.set_xlabel(f"{col}")
        ax.set_ylabel("Frequency")
        ax.legend()

    # plot all cols
    fig, axs = plt.subplots(
        len(columns_to_plot),
        1 if not without_zeros else 2,
        figsize=(20, 8 * len(columns_to_plot)),
    )
    for i, ax in enumerate(axs):
        plot_one_col(
            df, columns_to_plot[i], ax[0] if without_zeros else ax, is_log=False
        )  # columns_to_plot[i] in logged)
        if without_zeros:
            plot_one_col(
                df[df[columns_to_plot[i]] != 0],
                columns_to_plot[i],
                ax[1],
                is_log=columns_to_plot[i] in logged,
                add_info="w/o zeros",
            )
    plt.tight_layout()

    return fig


def plot_dynamics_dates_doubled(
    df,
    specified_column_value,
    iter_axes_by,
    date_col,
    main_col,
    cols_to_plot=None,
    colormap=None,
    renaming=dict(),
    order_for_column=None,
    av_for_period=None,
    bars_cnt=None,
    yticks_cnt=None,
):
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from utilities import date_range

    from matplotlib import colormaps
    import matplotlib.colors as mcolors

    import random

    spec_col, spec_val = specified_column_value
    dr = None

    def filter(date, ranges):
        for i in range(len(ranges)):
            if date >= ranges[i][0] and date < ranges[i][1]:
                return ranges[i][0]

    for c in df.columns:
        if c not in renaming:
            renaming[c] = c
    for v in df[iter_axes_by].unique():
        if v not in renaming:
            renaming[v] = v
    if order_for_column is None:
        order_for_column = list(df[iter_axes_by].unique())
    if yticks_cnt is None:
        yticks_cnt = 8
    if colormap is None:
        colormap = colormaps["Pastel1"]

    df = df[df[spec_col] == spec_val]
    fig, axs = plt.subplots(nrows=df[iter_axes_by].nunique(), ncols=1, figsize=(15, 20))
    for i, ax in enumerate(axs):
        event_type = order_for_column[i]
        filtered_df = df[df[iter_axes_by] == event_type]
        if av_for_period is not None and bars_cnt is None:
            dr = date_range(
                filtered_df[date_col].min(),
                filtered_df[date_col].max(),
                freq=av_for_period,
            )
            filtered_df[date_col] = filtered_df[date_col].apply(filter, ranges=dr)
            dc = av_for_period
        if bars_cnt is not None:
            dc = filtered_df[date_col].nunique() // bars_cnt
            dr = date_range(
                filtered_df[date_col].min(),
                filtered_df[date_col].max(),
                freq=dc,
            )
            filtered_df[date_col] = filtered_df[date_col].apply(filter, ranges=dr)

        grouped = filtered_df.groupby(date_col)
        summed_data = grouped[
            [c for c in df.columns if c not in [iter_axes_by, date_col, spec_col]]
        ].mean()

        css_colors = [mcolors.rgb2hex(colormap(i)) for i in range(colormap.N)]
        colors = random.sample(css_colors, 1 + len(cols_to_plot))

        xs = np.arange(len(summed_data.index))

        cols = cols_to_plot
        if cols is None:
            cols = [
                i for i in df.columns if i not in [spec_col, iter_axes_by, date_col]
            ]

        doubled_cols_divide_idx = len(cols) // 2

        for col in cols:
            summed_data[f"{col}_percent"] = (
                summed_data[col] / summed_data[main_col] * 100
            )

        for i in range(doubled_cols_divide_idx):
            col1, col2 = cols[i], cols[doubled_cols_divide_idx + i]
            ax.plot(
                xs,
                summed_data[f"{col1}_percent"],
                label=renaming[col1],
                alpha=1,
                color=colors[i],
            )
            ax.plot(
                xs,
                summed_data[f"{col2}_percent"],
                label=renaming[col2],
                alpha=1,
                color=colors[i],
                linestyle=":",
            )
            ax.scatter(
                xs,
                summed_data[f"{col1}_percent"],
                marker="x",
                alpha=0.7,
                color=colors[i],
            )
            ax.scatter(
                xs,
                summed_data[f"{col2}_percent"],
                marker="x",
                alpha=0.7,
                color=colors[i],
            )
            ax.fill_between(
                xs,
                summed_data[f"{col1}_percent"],
                summed_data[f"{col2}_percent"],
                alpha=0.3,
                color=colors[i],
            )

        cnt = 0
        if dr is not None:
            drf = [i for i, _ in dr]
            j = 0
            for i, datee in enumerate(summed_data.index.date):
                if pd.Timestamp(datee) != drf[j]:
                    if cnt == 0:
                        ax.axvspan(
                            i - 1, i, color="salmon", alpha=0.2, label="Разрыв в данных"
                        )
                    else:
                        ax.axvspan(i - 1, i, color="salmon", alpha=0.2)
                    cnt += 1
                    while pd.Timestamp(datee) != drf[j]:
                        j += 1
                j += 1

        if bars_cnt is not None or av_for_period is not None:
            substr = f", Days in point: {dc}"
        ax.set_title(
            f"Data for {renaming[spec_col]}: {spec_val}, {renaming[iter_axes_by]}: {renaming[event_type]}{substr if bars_cnt is not None or av_for_period is not None else ''}"
        )
        ax.set_xlabel(renaming[date_col])
        ax.set_ylabel(renaming[main_col])
        ax.set_xticks(xs)

        yticks = ax.get_yticks()
        mi, ma = yticks[1], yticks[-1]
        delta = (ma - mi) // yticks_cnt
        ytn = []
        ytn = list(np.arange(mi, ma, delta))
        ytn.append(yticks[-1])
        ax.set_yticks(ytn)

        ax.set_xticklabels(summed_data.index.date.astype(str), rotation=45)
        ax.grid(
            visible=True,
            axis="both",
            linestyle="--",
            color="black",
            alpha=0.3,
            linewidth=0.3,
        )
        ax.legend()

    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_bars_with_percentiles_lower_doubled(
    df,
    specified_column_value,
    iter_axes_by,
    date_col,
    main_col,
    cols_to_plot=None,
    colormap=None,
    renaming=dict(),
    order_for_column=None,
    av_for_period=None,
    bars_cnt=None,
):
    import matplotlib.pyplot as plt
    import numpy as np
    from utilities import date_range

    from matplotlib import colormaps
    import matplotlib.colors as mcolors

    import random

    spec_col, spec_val = specified_column_value

    def filter(date, ranges):
        for i in range(len(ranges)):
            if date >= ranges[i][0] and date < ranges[i][1]:
                return ranges[i][0]

    for c in df.columns:
        if c not in renaming:
            renaming[c] = c
    for v in df[iter_axes_by].unique():
        if v not in renaming:
            renaming[v] = v
    if order_for_column is None:
        order_for_column = list(df[iter_axes_by].unique())
    if colormap is None:
        colormap = colormaps["Pastel1"]

    df = df[df[spec_col] == spec_val]
    fig, axs = plt.subplots(nrows=df[iter_axes_by].nunique(), ncols=1, figsize=(15, 20))
    for i, ax in enumerate(axs):
        event_type = order_for_column[i]
        filtered_df = df[df[iter_axes_by] == event_type]
        if av_for_period is not None and bars_cnt is None:
            dr = date_range(
                filtered_df[date_col].min(),
                filtered_df[date_col].max(),
                freq=av_for_period,
            )
            filtered_df[date_col] = filtered_df[date_col].apply(filter, ranges=dr)
        if bars_cnt is not None:
            dc = filtered_df[date_col].nunique() // bars_cnt
            dr = date_range(
                filtered_df[date_col].min(),
                filtered_df[date_col].max(),
                freq=dc,
            )
            filtered_df[date_col] = filtered_df[date_col].apply(filter, ranges=dr)

        grouped = filtered_df.groupby(date_col)
        summed_data = grouped[
            [c for c in df.columns if c not in [iter_axes_by, date_col, spec_col]]
        ].mean()

        css_colors = [mcolors.rgb2hex(colormap(i)) for i in range(colormap.N)]
        colors = random.sample(css_colors, 1 + len(cols_to_plot))

        base_width = 0.9
        semi_width = base_width / 2.15
        between = base_width - 2.0 * semi_width

        shift = base_width / 2.0

        xs = np.arange(len(summed_data.index))

        ax.bar(
            xs,
            summed_data[main_col],
            width=base_width,
            label=renaming[main_col],
            color="whitesmoke",
            edgecolor="dimgray",
        )

        cols = cols_to_plot
        if cols is None:
            cols = [
                i for i in df.columns if i not in [spec_col, iter_axes_by, date_col]
            ]

        doubled_cols_divide_idx = len(cols) // 2

        for i, col in enumerate(cols[:doubled_cols_divide_idx]):
            ax.bar(
                xs - shift,
                summed_data[col],
                width=semi_width,
                label=renaming[col],
                alpha=1,
                align="edge",
                color=colors[i],
            )
        for i, col in enumerate(cols[doubled_cols_divide_idx:]):
            ax.bar(
                xs + between / 2.0,
                summed_data[col],
                width=semi_width,
                label=renaming[col],
                alpha=1,
                align="edge",
                color=colors[3 + i],
            )

        for col in cols:
            summed_data[f"{col}_percent"] = (
                summed_data[col] / summed_data[main_col] * 100
            )

        for left_col in cols[:doubled_cols_divide_idx]:
            for i in range(len(xs)):
                id = list(summed_data.index)[i]
                val = summed_data.at[id, left_col]
                val_p = summed_data.at[id, f"{left_col}_percent"]
                ax.text(
                    xs[i] - shift + between / 2,
                    val,
                    f"{val_p:.0f}",
                    ha="left",
                    va="bottom",
                    fontsize=7,
                    fontweight="bold",
                )

        for right_col in cols[doubled_cols_divide_idx:]:
            for i in range(len(xs)):
                id = list(summed_data.index)[i]
                val = summed_data.at[id, right_col]
                val_p = summed_data.at[id, f"{right_col}_percent"]
                ax.text(
                    xs[i] + shift - between / 2,
                    val,
                    f"{val_p:.0f}",
                    ha="right",
                    va="bottom",
                    fontsize=7,
                    fontweight="bold",
                )

        for i in range(len(xs)):
            id = list(summed_data.index)[i]
            val = summed_data.at[id, main_col]
            ax.text(xs[i], val, f"{val:.0f}", ha="center", va="bottom", fontsize=8)

        if bars_cnt is not None or av_for_period is not None:
            substr = f", Days in bar: {dc}"
        ax.set_title(
            f"Data for {renaming[spec_col]}: {spec_val}, {renaming[iter_axes_by]}: {renaming[event_type]}{substr if bars_cnt is not None or av_for_period is not None else ''}"
        )
        ax.set_xlabel(renaming[date_col])
        ax.set_ylabel(renaming[main_col])
        ax.set_xticks(xs)
        ax.set_xticklabels(summed_data.index.date.astype(str), rotation=45)
        ax.legend()

    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()
