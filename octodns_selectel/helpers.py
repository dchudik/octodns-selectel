def _ensure_trailing_dot(fqdn):
    if fqdn.endswith('.'):
        return fqdn

    return f'{fqdn}.'
