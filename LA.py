import numpy as np

class DimensionalityReducer:
    def __init__(self):
        self.mean = None
        self.basis = None
        self.variance_explained = None

    def preprocess(self, X):
        self.mean = np.mean(X, axis=0)
        X_c = X - self.mean
        return X_c

    def compute_key_directions(self, X_centered):
        U, S, Vt = np.linalg.svd(X_centered,full_matrices=False)
        self.basis = Vt
        t_v = np.sum(S ** 2)
        if t_v == 0:
            self.variance_explained=np.zeros_like(S)
        else:
            self.variance_explained=(S**2)/t_v

    def reduce_dimensions(self, X_c, k):
        t_k_b=self.basis[:k].T
        return X_c@t_k_b

    def reconstruct(self, X_r):
        if X_r.size==0:
            return np.zeros_like(self.mean)
        t_k_b = self.basis[:X_r.shape[1]]
        return X_r@ t_k_b+self.mean

    def evaluate_error(self, X_original, X_reconstructed):
        if X_reconstructed.ndim==1:
            X_reconstructed=np.tile(X_reconstructed, (X_original.shape[0], 1))
        diff=X_original-X_reconstructed
        return np.sqrt(np.sum(diff**2))

def main():
    A = []
    while True:
        try:
            row = input().strip()
            if row:
                A.append(list(map(float, row.split())))
            else:
                break
        except EOFError:
            break

    A = np.array(A)
    reducer = DimensionalityReducer()

    try:
        X_centered = reducer.preprocess(A)
    except Exception as e:
        print("Error during preprocessing:", e)
        return

    print("Centered data:")
    print(X_centered)

    try:
        reducer.compute_key_directions(X_centered)
    except Exception as e:
        print("Error during key directions computation:", e)
        return

    cumulative_variance = np.cumsum(reducer.variance_explained)
    k = np.argmax(cumulative_variance >= 0.95) + 1 if reducer.variance_explained.size > 0 else 0

    if np.allclose(X_centered, 0):
        k = 0

    try:
        if k > 0:
            X_reduced = reducer.reduce_dimensions(X_centered, k)
        else:
            X_reduced = np.zeros((X_centered.shape[0], 0))
    except Exception as e:
        print("Error during dimensionality reduction:", e)
        return

    print("\nTop directions:")
    if k > 0:
        for direction in reducer.basis[:k]:
            print(" ".join(f"{x:.2f}" for x in direction))
    else:
        print("No directions (all features are constant)")

    print("\nReduced data:")
    if X_reduced.size > 0:
        for row in X_reduced:
            print(" ".join(f"{x:.2f}" for x in row))
    else:
        print("No reduced data (all features are constant)")

    try:
        X_reconstructed = reducer.reconstruct(X_reduced)
    except Exception as e:
        print("Error during reconstruction:", e)
        return

    print("\nReconstructed data:")
    if X_reconstructed.ndim == 1:
        formatted = " ".join(f"{x:.1f}" if x == int(x) else f"{x:.2f}" for x in X_reconstructed)
        formatted = formatted.replace(".0", ".")  # Convert "0.0" to "0."
        print(f"[{formatted}]")
    else:
        print(X_reconstructed)

    try:
        error = reducer.evaluate_error(A, X_reconstructed)
    except Exception as e:
        print("Error during error evaluation:", e)
        return

    print(f"\nReconstruction error: {error:.2f}")

if __name__ == "__main__":
    main()
