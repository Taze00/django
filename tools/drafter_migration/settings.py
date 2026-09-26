"""Migration preview settings: same scorer/DB, only Drafter routes exposed."""
from meinprojekt.settings import *  # noqa: F403
ROOT_URLCONF = 'tools.drafter_migration.urls'
