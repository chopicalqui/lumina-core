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
from fastapi.requests import Request

from ..models.account import Account

# Obtain the log level, log file, and log broker host from the environment variables.
log_file = os.getenv('LOG_FILE')
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_format = os.getenv(
    'LOG_FORMAT',
    '%(asctime)s [%(levelname)-8s] - %(client_addr)s / %(account_name)s - %(method)s %(path)s - %(message)s'
)
log_date_format = os.getenv('LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S')
log_broker_host = os.getenv('LOG_BROKER_HOST')


class InjectingFilter(logging.Filter):
    """
    This is a custom logging filter that adds an account name field to the log record.
    """

    def __init__(self, account: Account | None = None, request: Request | None = None):
        super().__init__()
        self.account = account
        self.request = request
        self.email = account.email if account else None
        self.client_addr = request.headers.get("X-Real-IP") if request else None
        self.path = request.url.path if request else None
        self.method = request.method if request else None

    def filter(self, record):
        record.account_name = self.email or 'n/a'
        record.client_addr = self.client_addr or 'n/a'
        record.method = self.method or "n/a"
        record.path = self.path or "n/a"
        return True


def record_factory(*args, **kwargs):
    """
    This function is used to create a log record with the account name and client IP.
    """
    record = old_factory(*args, **kwargs)
    if not hasattr(record, 'account_name'):
        record.account_name = "n/a"
    if not hasattr(record, 'client_addr'):
        record.client_addr = "n/a"
    if not hasattr(record, 'method'):
        record.method = "n/a"
    if not hasattr(record, 'path'):
        record.path = "n/a"
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


def get_logger() -> logging.Logger:
    """
    Returns a logger with the current account injected.
    """
    return logger
