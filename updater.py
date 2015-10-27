from os import path, remove
import logging

from sh import git, ErrorReturnCode
from requests import get as req_get
from requests import RequestException

from settings import config_dir

UPDATE_FILE_NAME = path.join(config_dir(), 'need_update')

logging.basicConfig(level=logging.DEBUG,
                    filename='/tmp/updater.log',
                    format='%(asctime)s %(name)s#%(levelname)s: %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
log = logging.getLogger('updater')


def get_last_sha():
    try:
        resp = req_get('http://stats.screenlyapp.com/latest')
        if resp.status_code == 200:
            return resp.content.strip()
    except RequestException:
        pass

    return None


def local_version_has(sha):
    try:
        return 'master' in git('branch', '--contains', sha)
    except ErrorReturnCode:
        return False


def set_need_update(need_update):
    if need_update:
        with open(UPDATE_FILE_NAME, 'w'):
            pass
    else:
        try:
            remove(UPDATE_FILE_NAME)
        except OSError:
            pass


def is_up_to_date():
    return not path.exists(UPDATE_FILE_NAME)


if __name__ == '__main__':
    last = get_last_sha()
    if not last:
        log.error('cannot connect to server for version check')
        exit(1)

    log.info('last sha: %s', last)

    need = not local_version_has(last)
    log.info('update %s needed', '' if need else 'not')
    set_need_update(need)
