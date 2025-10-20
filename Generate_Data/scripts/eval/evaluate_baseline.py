# Minimal evaluation placeholder.
# Keeps code comments in English only.
import os

def evaluate_baseline(ckpt_path: str = "outputs/checkpoints/baseline.ckpt", out_path: str = "outputs/metrics/metrics.json"):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # TODO: implement metrics computation
    import json
    metrics = {"accuracy": 0.0, "notes": "placeholder"}
    with open(out_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print("Saved metrics:", out_path)

if __name__ == "__main__":
    evaluate_baseline()
