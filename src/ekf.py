import numpy as np

class ExtendedKalmanFilter:
    # https://www.youtube.com/watch?v=9X3jGGnbcvU & https://automaticaddison.com/extended-kalman-filter-ekf-with-python-code-example/ taught me the math behind the Extended Kalman Filter 
    # Implementation was done by me

    def __init__(self, dt=1.0, process_noise_std=1.0, measurement_noise_std=1.0):
        # State vector [x, y, vx, vy]
        self.x = np.zeros((4, 1))  # Initial state

        # State transition matrix
        self.F = np.array([[1, 0, dt, 0],
                           [0, 1, 0, dt],
                           [0, 0, 1,  0],
                           [0, 0, 0,  1]])

        # Control input matrix (assuming no control input)
        self.B = np.zeros((4, 1))

        # Measurement matrix
        self.H = np.array([[1, 0, 0, 0],
                           [0, 1, 0, 0]])

        # Initial covariance matrix
        self.P = np.eye(4) * 500.

        # Process noise covariance
        q = process_noise_std
        self.Q = np.array([[q, 0, 0, 0],
                           [0, q, 0, 0],
                           [0, 0, q, 0],
                           [0, 0, 0, q]])

        # Measurement noise covariance
        r = measurement_noise_std
        self.R = np.array([[r, 0],
                           [0, r]])

        self.is_initialized = False
        self.state = None

    def predict(self):
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

    def update(self, z):
        if not self.is_initialized:
            self.x[:2] = z.reshape(2, 1)
            self.is_initialized = True
            return

        y = z.reshape(2, 1) - self.H @ self.x  # Measurement residual
        S = self.H @ self.P @ self.H.T + self.R  # Residual covariance
        K = self.P @ self.H.T @ np.linalg.inv(S)  # Kalman gain

        self.x = self.x + K @ y
        I = np.eye(self.F.shape[0])
        self.P = (I - K @ self.H) @ self.P

    def set_state(self, x, y, est_x, est_y):
        self.state = np.array([[x], [y], [est_x], [est_y]])

    def get_state(self, x, y):
        return x, y, self.x[2][0], self.x[3][0]
