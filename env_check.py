# env_check.py
import os
def show_env_info():
    for name in ("BB_CLIENT_ID", "BB_CLIENT_SECRET"):
        v = os.getenv(name)
        if v is None:
            print(f"{name}: NOT SET")
        else:
            # mostra apenas comprimento e se começa/termina com espaço
            starts = v[0].isspace()
            ends = v[-1].isspace()
            print(f"{name}: set, length={len(v)}, startswith_space={starts}, endswith_space={ends}")

if __name__ == "__main__":
    show_env_info()
