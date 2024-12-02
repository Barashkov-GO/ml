def experiment_groups_division(
    group_sizes, num_groups, stratas_counter, df, df_strata_col, df_group_col, df_id_col
):
    import numpy as np
    import random

    df[df_group_col] = "Undefined"

    target_size_per_group = group_sizes
    total_target = target_size_per_group * num_groups

    total_clients = sum(size for _, size in dict(stratas_counter).items())

    s = "ABCDEFGHIJKLMNOP"
    final_groups = dict([(s[i], []) for i in range(num_groups)])
    remaining_clients = {key: size for key, size in dict(stratas_counter).items()}

    for stratum, size in dict(stratas_counter).items():
        group_sizes = np.round((size / total_clients) * target_size_per_group).astype(
            int
        )

        group_sizes = np.maximum(
            group_sizes, [1] * num_groups
        )  # Минимум по 1 клиенту на группу
        group_sizes = np.minimum(group_sizes, size)  # Не больше, чем есть

        if (group_sizes < 1).any():
            continue

        remaining_cli = list(df.loc[df[df_strata_col] == stratum][df_id_col].unique())

        if len(remaining_cli) < sum(group_sizes):
            continue

        for ind in range(len(group_sizes)):
            gr = random.sample(remaining_cli, group_sizes[ind])
            remaining_cli = list(set(remaining_cli) - set(gr))

            df.loc[df[df_id_col].isin(gr), df_group_col] = s[ind]
            final_groups[s[ind]].extend(gr)

        remaining_clients[stratum] -= sum(group_sizes)

    return df, final_groups


def quantile_factoring(df, quantile_bins, binarize_cols, suffix="_group"):
    import pandas as pd

    df.drop(columns=[i for i in df.columns if suffix in i], inplace=True)
    for col in df.columns:
        print()
        if col in binarize_cols:
            df[f"{col}{suffix}"] = df[col].apply(lambda x: x > 0).astype(int)
            print(f"Column: {col}\n\tBins: 0")
            continue
        df[f"{col}{suffix}"], bins = pd.qcut(
            df[col],
            q=quantile_bins,
            labels=[i for i in range(len(quantile_bins) - 1)],
            retbins=True,
        )
        print(f"Column: {col}\n\tBins: {bins}")

    return df


def collapse_factors_into_groups(df, df_group_col="group_id", suffix="_group"):
    m = 0
    for factor in [col for col in df.columns if suffix in col]:
        m = max(m, df[factor].max())
    df[df_group_col] = df[[col for col in df.columns if suffix in col]].agg(
        lambda x: "".join([str(i) for i in x.values]), axis=1
    )
    df[f"{df_group_col}_decimal"] = df[df_group_col].apply(lambda x: int(x, m))
    return df


def get_counter(df, df_group_col, df_id_col, num_groups_limit):
    from collections import Counter

    grs = dict()

    for gr in df[df_group_col].unique():
        cnt = df[df[df_group_col] == gr][df_id_col].nunique()
        grs[gr] = cnt

    bad = []
    for gr in grs.keys():
        if grs[gr] < num_groups_limit:
            bad.append(gr)

    for bad_str in bad:
        del grs[bad_str]

    return Counter(grs)
