import logging
import os

logger = logging.getLogger(__name__)

_warned_missing_pushover_config = False

def get_pushover_config(settings):
    global _warned_missing_pushover_config
    pushover_cfg = settings.get('integrations', {}).get('pushover', {})
    enabled = pushover_cfg.get('enabled', False)
    api_token = pushover_cfg.get('api_token')
    user_token = pushover_cfg.get('user_token')
    if not enabled:
        return None, None, False
    if (not api_token or not user_token) and not _warned_missing_pushover_config:
        logger.warning("Pushover API token or user token not configured (warned once per run)")
        _warned_missing_pushover_config = True
    return api_token, user_token, enabled 