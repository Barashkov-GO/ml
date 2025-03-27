class Distribution:
    def __init__(self, data):
        """

        Args:
            data (_type_): _description_
        """
        pass

    def __plot_data(data):
        """Private. Plots the data

        Args:
            data (pd.Series): Data to be plotted.
        """
        pass

    def is_norm(self, bootstrap_cnt=None, bootstrap_samples=None):
        """Checks if the distribution of given data is Gauss's (normal)

        Args:
            bootstrap_cnt (int, optional): Number of bootstrap iterations. If None then no bootstrap is operating. Defaults to None.
            bootstrap_samples (int, optional): Number of samples to put in one bootstrap iteration. If None then no bootstrap is operating. Defaults to None.
        """
        pass

    def predict_distribution(based=True, advanced=True, count_data=True, plot=False):
        """Predicts the true distribution of data, sample of which was given.

        Args:
            based (bool, optional): Gauss, LogNormal and Weibull distributions to check. Defaults to True.
            advanced (bool, optional): Many other distributions to check. Defaults to True.
            count_data (bool, optional): ___. Defaults to True.
            plot (bool, optional): Whether to plot given data with descriptive statistics. Defaults to False.
        """
        pass

    def is_same_population():
        """Welch, Fischer, Stewdent, Levene, 
        """
        pass
