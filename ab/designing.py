def ab_group_size(alpha, power, base, mde):
    from scipy.stats import norm
    import math

    base_plus_delta = base + mde
    beta = 1 - power
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(1 - beta)

    n = (
        (
            z_alpha * math.sqrt(2 * base * (1 - base))
            + z_beta
            * math.sqrt(base * (1 - base) + base_plus_delta * (1 - base_plus_delta))
        )
        / mde
    ) ** 2
    return n


def abc_binomial_group_size(
    means,
    n_sim,
    sample_size_start,
    sample_size_step,
    power,
    plot=True,
    alpha=0.05,
    method="bonferroni",
):
    """Shows group sizes for multiple test groups (> 2) with specified correction method with alpha and power declared.

    Args:
        means (list[float]): Mean values of each group with MDE. The first one is test (=historical BCR).
        n_sim (int): Number of simulations.
        sample_size_start (int): Group size to start with.
        sample_size_step (int): Step in group size search.
        power (float): Power to reach.
        plot (bool, optional): Plotting the chart. Defaults to True.
        alpha (float, optional): Statistical value. Defaults to 0.05.
        method (str, optional): Method to correct alpha and group size with (during multiple testing). Defaults to "bonferroni".

    Returns:
        dict: Sample sizes and corresponding power values.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    from scipy.stats import ttest_ind
    from statsmodels.stats.weightstats import ztest
    import numpy as np
    from statsmodels.stats.multitest import multipletests

    def z_test(group_a, group_b):
        from scipy.stats import norm
        import numpy as np

        mean_a, mean_b = np.mean(group_a), np.mean(group_b)
        n_a, n_b = len(group_a), len(group_b)
        std_a, std_b = np.std(group_a, ddof=1), np.std(group_b, ddof=1)
        pooled_se = np.sqrt((std_a**2 / n_a) + (std_b**2 / n_b))
        z_score = (mean_b - mean_a) / pooled_se
        p_value = 2 * (1 - norm.cdf(abs(z_score)))

        return z_score, p_value

    sample_size_list = []
    power_value_list = []
    power_value_corrected_list = []

    while True:
        p_value_list = []
        for i in range(n_sim):
            group_a = np.random.binomial(n=1, p=means[0], size=sample_size_start)
            group_b = np.random.binomial(n=1, p=means[1], size=sample_size_start)
            group_c = np.random.binomial(n=1, p=means[2], size=sample_size_start)

            # ab_t_stat, ab_p_value = ttest_ind(group_a, group_b)
            # ac_t_stat, ac_p_value = ttest_ind(group_a, group_c)
            # bc_t_stat, bc_p_value = ttest_ind(group_b, group_c)

            z_score, ab_p_value = z_test(group_a, group_b)
            z_score, ac_p_value = z_test(group_a, group_c)
            z_score, bc_p_value = z_test(group_b, group_c)

            p_value_list.append((ab_p_value, ac_p_value, bc_p_value))

        tp = np.logical_and(
            np.array(p_value_list)[:, 0] < alpha,
            np.array(p_value_list)[:, 1] < alpha,
            np.array(p_value_list)[:, 2] < alpha,
        )

        hypothesys = []
        for i in range(len(p_value_list)):
            hypothesys.append(
                multipletests(p_value_list[i], alpha=alpha, method=method)[0]
            )
        tp_corrected = np.logical_and(
            np.array(hypothesys)[:, 0],
            np.array(hypothesys)[:, 1],
            np.array(hypothesys)[:, 2],
        )

        power_value = tp.mean()
        power_value_corrected = tp_corrected.mean()
        power_value_list.append(power_value)
        power_value_corrected_list.append(power_value_corrected)
        sample_size_list.append(sample_size_start)
        if power_value_corrected > power + 0.05:
            break
        else:
            sample_size_start += sample_size_step

    non_corrected_power = power_value_list[
        np.argmax(np.array(power_value_list) >= power)
    ]
    corrected_power = power_value_corrected_list[
        np.argmax(np.array(power_value_corrected_list) >= power)
    ]
    non_corrected_sample_size = sample_size_list[
        np.argmax(np.array(power_value_list) >= power)
    ]
    corrected_sample_size = sample_size_list[
        np.argmax(np.array(power_value_corrected_list) >= power)
    ]

    if plot:
        plt.figure(figsize=(16, 8))
        plt.plot(sample_size_list, power_value_list, label="Non corrected power")
        plt.plot(sample_size_list, power_value_corrected_list, label="Corrected power")
        plt.axhline(y=0.8, linestyle="--", color="red")
        plt.axvline(x=non_corrected_sample_size, linestyle="--", color="red")
        plt.axvline(x=corrected_sample_size, linestyle="--", color="blue")
        plt.legend()

        plt.text(
            x=round(non_corrected_sample_size * 0.97),
            y=0.3,
            s="Размер выборки без коррекции ~ {}".format(non_corrected_sample_size),
            rotation="vertical",
            color="red",
        )
        plt.text(
            x=round(corrected_sample_size * 0.97),
            y=0.3,
            s="Размер выборки c коррекцией ~ {}".format(corrected_sample_size),
            rotation="vertical",
            color="blue",
        )
        plt.tight_layout()

    return_object = {
        "non_corrected sample_size": non_corrected_sample_size,
        "corrected sample size": corrected_sample_size,
        "non corrected power": non_corrected_power,
        "corrected power": corrected_power,
    }

    return return_object
