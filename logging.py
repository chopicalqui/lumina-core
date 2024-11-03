# This file is part of Lumina.
#
# Lumina is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Lumina is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Lumina. If not, see <https://www.gnu.org/licenses/>.

__author__ = "Lukas Reiter"
__copyright__ = "Copyright (C) 2024 Lukas Reiter"
__license__ = "GPLv3"

import os
import sys
import logging
from .models.user.user import User

# Obtain the log level, log file, and log broker host from the environment variables.
log_file = os.getenv('LOG_FILE')
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_format = os.getenv(
    'LOG_FORMAT',
    '%(asctime)s [%(levelname)-8s] %(client_ip)-15s %(user_name)s - %(name)s - %(message)s'
)
log_date_format = os.getenv('LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S')
log_broker_host = os.getenv('LOG_BROKER_HOST')


class InjectingFilter(logging.Filter):
    """
    This is a custom logging filter that adds a username field to the log record.
    """
    def __init__(self, user: User | None = None):
        super().__init__()
        self.user = user
        self.email = user.email if user else None
        self.client_ip = user.client_ip if user else None

    def filter(self, record):
        record.user_name = self.email or 'n/a'
        record.client_ip = self.client_ip or 'n/a'
        return True


def record_factory(*args, **kwargs):
    """
    This function is used to create a log record with the username and client IP.
    """
    record = old_factory(*args, **kwargs)
    if not hasattr(record, 'user_name'):
        record.user_name = "n/a"
    if not hasattr(record, 'client_ip'):
        record.client_ip = "n/a"
    return record


# Define the handlers for the logger.
handlers = [logging.StreamHandler(sys.stdout)]
if log_file:
    handlers.append(logging.FileHandler(log_file))


# We set up a basic logger.
logging.basicConfig(
    format=log_format,
    datefmt=log_date_format,
    handlers=handlers,
    level=log_level
)

old_factory = logging.getLogRecordFactory()
logging.setLogRecordFactory(record_factory)
logger = logging.getLogger(__name__)
