from .config import get_profile, load_profiles, save_profiles, list_profile_names, DEFAULT_PROFILE

def get_connection(profile=None):
    prof = get_profile(profile)
    return f"{prof['user']}@{prof['host']}:{prof['port']} [{prof['database']}]"

def list_profiles():
    return list_profile_names()

def create_or_update_profile(name, host, port, user, db):
    profiles = load_profiles()
    profiles[name] = {"host": host, "port": int(port), "user": user, "database": db}
    save_profiles(profiles)

def remove_profile(name):
    profiles = load_profiles()
    if name in profiles:
        del profiles[name]
        save_profiles(profiles)
        return True
    return False
