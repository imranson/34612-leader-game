import numpy as np


class AdaptiveStackelbergLeader(Leader):

    def __init__(self, name, engine):
        super().__init__(name, engine)
        self.c_L = 1.0
        self.theta = np.array([1.0, 0.5])
        self.P = np.eye(2) * 100.0
        self.lam = 0.95
        self.price_lb = 1.0
        self.price_ub = 15.0

    def start_simulation(self):
        u_L_hist, u_F_hist = [], []
        for day in range(1, 101):
            lp, fp = self.get_price_from_date(day)
            u_L_hist.append(lp)
            u_F_hist.append(fp)

        u_L_hist = np.array(u_L_hist, dtype=float)
        u_F_hist = np.array(u_F_hist, dtype=float)

        median_fp = np.median(u_F_hist)
        mad = np.median(np.abs(u_F_hist - median_fp))
        threshold = 6.0 * (mad + 0.01)
        clean_mask = np.abs(u_F_hist - median_fp) < threshold
        u_L_clean = u_L_hist[clean_mask]
        u_F_clean = u_F_hist[clean_mask]

        if len(u_L_clean) < 5:
            u_L_clean = u_L_hist
            u_F_clean = u_F_hist

        n_seed = min(30, len(u_L_clean))
        X = np.column_stack([np.ones(n_seed), u_L_clean[-n_seed:]])
        self.theta, _, _, _ = np.linalg.lstsq(X, u_F_clean[-n_seed:], rcond=None)

        self.P = np.eye(2) * 10.0
        for i in range(len(u_L_clean)):
            phi = np.array([1.0, u_L_clean[i]])
            self._rls_update(phi, u_F_clean[i])

        estimated_slope = self.theta[1]
        median_fp = np.median(u_F_clean)
        if estimated_slope < 0.6 or median_fp < 2.0:
            self.price_ub = 15.0
        else:
            self.price_ub = 50.0

    def _rls_update(self, phi, y):
        e = y - phi @ self.theta
        denom = self.lam + phi @ self.P @ phi
        K = (self.P @ phi) / denom
        self.theta = self.theta + K * e
        self.P = (self.P - np.outer(K, phi) @ self.P) / self.lam
        self.P = 0.5 * (self.P + self.P.T)

    def _compute_optimal_price(self):
        a, b = self.theta
        A = 100.0 + 3.0 * a
        B = 3.0 * b - 5.0

        if B >= -1e-10:
            return self.price_ub

        u_star = (B - A) / (2.0 * B)
        return float(np.clip(u_star, self.price_lb, self.price_ub))

    def new_price(self, date):
        if date > 101:
            prev_lp, prev_fp = self.get_price_from_date(date - 1)
            phi = np.array([1.0, prev_lp])
            predicted_fp = phi @ self.theta
            if abs(prev_fp - predicted_fp) < 50.0:
                self._rls_update(phi, prev_fp)

        optimal = self._compute_optimal_price()

        play_day = date - 100
        if play_day <= 3 and optimal > 10.0:
            safe_start = 10.0
            ramp = play_day / 3.0
            optimal = safe_start + ramp * (optimal - safe_start)

        return max(self.price_lb, min(self.price_ub, optimal))
