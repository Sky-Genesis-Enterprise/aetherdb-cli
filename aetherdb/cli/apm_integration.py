def apm_install(package):
    # Implement real install logic (for now, just mock)
    return f"[APM] Installed {package}"

def apm_remove(package):
    return f"[APM] Removed {package}"

def apm_update(package):
    return f"[APM] Updated {package}"

def apm_list():
    # Simulate some extensions
    return ["analytics", "uuid-ossp", "postgis", "apm-utils"]
