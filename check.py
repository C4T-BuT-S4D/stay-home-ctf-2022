#!/usr/bin/env python3

import argparse
import json
import os
import random
import secrets
import string
import subprocess
import time
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from pathlib import Path
from threading import Lock, current_thread
from typing import List, Tuple

import yaml
from dockerfile_parse import DockerfileParser

BASE_DIR = Path(__file__).resolve().absolute().parent
SERVICES_PATH = BASE_DIR / 'services'
CHECKERS_PATH = BASE_DIR / 'checkers'
MAX_THREADS = int(os.getenv('MAX_THREADS', default=2 * os.cpu_count()))
RUNS = int(os.getenv('RUNS', default=10))
HOST = os.getenv('HOST', default='127.0.0.1')
OUT_LOCK = Lock()
DISABLE_LOG = False

DC_REQUIRED_OPTIONS = ['version', 'services']
DC_ALLOWED_OPTIONS = DC_REQUIRED_OPTIONS + ['volumes']

CONTAINER_REQUIRED_OPTIONS = ['restart']
CONTAINER_ALLOWED_OPTIONS = CONTAINER_REQUIRED_OPTIONS + [
    'pids_limit', 'mem_limit', 'cpus',
    'build', 'image',
    'ports', 'volumes',
    'environment', 'env_file',
    'depends_on',
    'sysctls', 'privileged', 'security_opt',
]
SERVICE_REQUIRED_OPTIONS = ['pids_limit', 'mem_limit', 'cpus']
SERVICE_ALLOWED_OPTIONS = CONTAINER_ALLOWED_OPTIONS
DATABASES = [
    'redis', 'postgres', 'mysql', 'mariadb',
    'mongo', 'mssql', 'clickhouse', 'tarantool',
]
PROXIES = ['nginx', 'envoy']
CLEANERS = ['dedcleaner']

VALIDATE_DIRS = ['checkers', 'services', 'internal', 'sploits']

ALLOWED_CHECKER_PATTERNS = [
    "import requests",
    "requests.exceptions",
    "s: requests.Session",
    "sess: requests.Session",
    "session: requests.Session",
    "Got requests connection error",
]
FORBIDDEN_CHECKER_PATTERNS = [
    "requests"
]

class ColorType(Enum):
    INFO = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

    def __str__(self):
        return self.value


def generate_flag(name):
    alph = string.ascii_uppercase + string.digits
    return name[0].upper() + ''.join(random.choices(alph, k=30)) + '='


def colored_log(*messages, color: ColorType = ColorType.INFO):
    ts = datetime.utcnow().isoformat(sep=' ', timespec='milliseconds')
    print(f'{color}{color.name} [{current_thread().name} {ts}]{ColorType.ENDC}', *messages)


class BaseValidator:
    def _log(self, message: str):
        with OUT_LOCK:
            if not DISABLE_LOG:
                colored_log(f'{self}: {message}')

    def _fatal(self, cond, message):
        global DISABLE_LOG

        with OUT_LOCK:
            if not cond:
                if not DISABLE_LOG:
                    colored_log(f'{self}: {message}', color=ColorType.FAIL)
                DISABLE_LOG = True
                raise AssertionError

    def _warning(self, cond: bool, message: str) -> bool:
        with OUT_LOCK:
            if not cond and not DISABLE_LOG:
                colored_log(f'{self}: {message}', color=ColorType.WARNING)
        return not cond

    def _error(self, cond, message) -> bool:
        with OUT_LOCK:
            if not cond and not DISABLE_LOG:
                colored_log(f'{self}: {message}', color=ColorType.FAIL)
        return not cond


class Checker(BaseValidator):
    def __init__(self, name: str):
        self._name = name
        self._exe_path = CHECKERS_PATH / self._name / 'checker.py'
        self._fatal(
            os.access(self._exe_path, os.X_OK),
            f'{self._exe_path.relative_to(BASE_DIR)} must be executable',
        )
        self._timeout = 3
        self._get_info()

    def _get_info(self):
        self._log('running info action')
        cmd = [str(self._exe_path), 'info', HOST]
        out, _ = self._run_command(cmd)
        info = json.loads(out)
        self._log(f'got info: {info}')

        self._vulns = int(info['vulns'])
        self._timeout = int(info['timeout'])
        self._attack_data = bool(info['attack_data'])

        self._fatal(
            60 > self._timeout > 0,
            f'invalid timeout: {self._timeout}',
        )

    @property
    def info(self):
        return {
            'vulns': self._vulns,
            'timeout': self._timeout,
            'attack_data': self._attack_data,
        }

    def _run_command(self, command: List[str], env=None) -> Tuple[str, str]:
        action = command[1].upper()
        cmd = ['timeout', str(self._timeout)] + command

        start = time.monotonic()
        p = subprocess.run(cmd, capture_output=True, check=False, env=env)
        elapsed = time.monotonic() - start

        out = p.stdout.decode()
        err = p.stderr.decode()

        out_s = out.rstrip('\n')
        err_s = err.rstrip('\n')

        self._log(f'action: {action}\ntime: {elapsed:.2f}s\nstdout:\n{out_s}\nstderr:\n{err_s}')
        self._fatal(
            p.returncode != 124,
            f'action {action}: bad return code: 124, probably {ColorType.BOLD}timeout{ColorType.ENDC}',
        )
        self._fatal(p.returncode == 101, f'action {action}: bad return code: {p.returncode}')
        return out, err

    def check(self):
        self._log('running CHECK')
        cmd = [str(self._exe_path), 'check', HOST]
        self._run_command(cmd)

    def put(self, flag: str, flag_id: str, vuln: int):
        self._log(f'running PUT, flag={flag} flag_id={flag_id} vuln={vuln}')
        cmd = [str(self._exe_path), 'put', HOST, flag_id, flag, str(vuln)]
        out, err = self._run_command(cmd)

        self._fatal(out, 'stdout is empty')

        new_flag_id = err
        self._fatal(new_flag_id, 'returned flag_id is empty')

        if self._attack_data:
            self._fatal(flag not in out, 'flag is leaked in public data')

        return new_flag_id

    def get(self, flag: str, flag_id: str, vuln: int):
        self._log(f'running GET, flag={flag} flag_id={flag_id} vuln={vuln}')
        cmd = [str(self._exe_path), 'get', HOST, flag_id, flag, str(vuln)]
        self._run_command(cmd)

    def run_all(self, step: int):
        self._log(f'running all actions (run {step} of {RUNS})')
        self.check()

        for vuln in range(1, self._vulns + 1):
            flag = generate_flag(self._name)
            flag_id = self.put(
                flag=flag, flag_id=secrets.token_hex(16), vuln=vuln)
            flag_id = flag_id.strip()
            self.get(flag, flag_id, vuln)

    def __str__(self):
        return f'checker {self._name}'


class Service(BaseValidator):
    def __init__(self, name: str):
        self._name = name
        self._path = SERVICES_PATH / self._name
        self._dc_path = self._path / 'docker-compose.yml'
        self._fatal(
            self._dc_path.exists(),
            f'{self._dc_path.relative_to(BASE_DIR)} missing',
        )

        self._checker = Checker(self._name)

    @property
    def name(self):
        return self._name

    @property
    def checker_info(self):
        return self._checker.info

    def _run_dc(self, *args):
        cmd = ['docker-compose', '-f', str(self._dc_path)] + list(args)
        subprocess.run(cmd, check=True)

    def up(self):
        self._log('starting')
        self._run_dc('up', '--build', '-d')

    def logs(self):
        self._log('printing logs')
        self._run_dc('logs', '--tail', '2000')

    def down(self):
        self._log('stopping')
        self._run_dc('down', '-v')

    def validate_checker(self):
        self._log('validating checker')

        cnt_threads = max(1, min(MAX_THREADS, RUNS // 10))
        self._log(f'starting {cnt_threads} checker threads')
        with ThreadPoolExecutor(
                max_workers=cnt_threads,
                thread_name_prefix='Executor',
        ) as executor:
            for _ in executor.map(self._checker.run_all, range(1, RUNS + 1)):
                pass

    def __str__(self):
        return f'service {self._name}'


class StructureValidator(BaseValidator):
    def __init__(self, d: Path, service: Service):
        self._dir = d
        self._was_error = False
        self._service = service

    def _error(self, cond, message):
        err = super()._error(cond, message)
        self._was_error |= err
        return err

    def validate(self):
        for d in VALIDATE_DIRS:
            self.validate_dir(self._dir / d / self._service.name)
        return not self._was_error

    def validate_dir(self, d: Path):
        if not d.exists():
            return
        for f in d.iterdir():
            if f.is_file():
                self.validate_file(f)
            elif f.name[0] != '.':
                self.validate_dir(f)

    def validate_file(self, f: Path):
        path = f.relative_to(BASE_DIR)
        self._error(f.suffix != '.yaml', f'file {path} has .yaml extension')
        self._error(f.name != '.gitkeep', f'{path} found, should be named .keep')

        if f.name == 'docker-compose.yml':
            with f.open() as file:
                dc = yaml.safe_load(file)

            if self._error(isinstance(dc, dict), f'{path} is not dict'):
                return

            for opt in DC_REQUIRED_OPTIONS:
                if self._error(opt in dc, f'required option {opt} not in {path}'):
                    return

            if self._error(isinstance(dc['version'], str), f'version option in {path} is not string'):
                return

            try:
                dc_version = float(dc['version'])
            except ValueError:
                self._error(False, f'version option in {path} is not float')
                return

            self._error(
                2.4 <= dc_version < 3,
                f'invalid version in {path}, need >=2.4 and <3, got {dc_version}',
            )

            for opt in dc:
                self._error(
                    opt in DC_ALLOWED_OPTIONS,
                    f'option {opt} in {path} is not allowed',
                )

            services = []
            databases = []
            proxies = []
            dependencies = defaultdict(list)

            if self._error(isinstance(dc['services'], dict), f'services option in {path} is not dict'):
                return

            for container, container_conf in dc['services'].items():
                if self._error(isinstance(container_conf, dict), f'config in {path} for container {container} is not dict'):
                    continue

                for opt in CONTAINER_REQUIRED_OPTIONS:
                    self._error(
                        opt in container_conf,
                        f'required option {opt} not in {path} for container {container}',
                    )

                self._error('restart' in container_conf and container_conf['restart'] == 'unless-stopped', f'restart option in {path} for container {container} must be equal to "unless-stopped"')

                for opt in container_conf:
                    self._error(
                        opt in CONTAINER_ALLOWED_OPTIONS,
                        f'option {opt} in {path} is not allowed for container {container}',
                    )

                if self._error(
                        'image' not in container_conf or 'build' not in container_conf,
                        f'both image and build options in {path} for container {container}'):
                    continue

                if self._error(
                        'image' in container_conf or 'build' in container_conf,
                        f'both image and build options not in {path} for container {container}'):
                    continue

                if 'image' in container_conf:
                    image = container_conf['image']
                else:
                    build = container_conf['build']
                    if isinstance(build, str):
                        dockerfile = f.parent / build / 'Dockerfile'
                    else:
                        context = build['context']
                        if 'dockerfile' in build:
                            dockerfile = f.parent / context / build['dockerfile']
                        else:
                            dockerfile = f.parent / context / 'Dockerfile'

                    if self._error(dockerfile.exists(), f'no dockerfile found in {dockerfile}'):
                        continue

                    with dockerfile.open() as file:
                        dfp = DockerfileParser(fileobj=file)
                        image = dfp.baseimage

                    if self._error(image is not None, f'no image option in {dockerfile}'):
                        continue

                if 'depends_on' in container_conf:
                    for dependency in container_conf['depends_on']:
                        dependencies[container].append(dependency)

                is_service = True
                for database in DATABASES:
                    if database in image:
                        databases.append(container)
                        is_service = False

                for proxy in PROXIES:
                    if proxy in image:
                        proxies.append(container)
                        is_service = False

                for cleaner in CLEANERS:
                    if cleaner in image:
                        is_service = False

                if is_service:
                    services.append(container)
                    for opt in SERVICE_REQUIRED_OPTIONS:
                        self._error(
                            opt in container_conf,
                            f'required option {opt} not in {path} for service {container}',
                        )

                    for opt in container_conf:
                        self._error(
                            opt in SERVICE_ALLOWED_OPTIONS,
                            f'option {opt} in {path} is not allowed for service {container}',
                        )

            for service in services:
                for database in databases:
                    self._error(
                        service in dependencies and database in dependencies[service],
                        f'service {service} may need to depends_on database {database}')

            for proxy in proxies:
                for service in services:
                    self._error(
                        proxy in dependencies and service in dependencies[proxy],
                        f'proxy {proxy} may need to depends_on service {service}')

        elif BASE_DIR / "checkers" in f.parents and f.suffix == ".py":
            checker_code = f.read_text()
            for p in ALLOWED_CHECKER_PATTERNS:
                checker_code = checker_code.replace(p, "")
            for p in FORBIDDEN_CHECKER_PATTERNS:
                self._error(p not in checker_code, f'forbidden pattern "{p}" in {path}')

    def __str__(self):
        return f'Structure validator for {self._service.name}'


def get_services() -> List[Service]:
    if os.getenv('SERVICE') in ['all', None]:
        result = list(
            Service(service_path.name) for service_path in SERVICES_PATH.iterdir()
            if service_path.name[0] != '.' and service_path.is_dir()
        )
    else:
        result = [Service(os.environ['SERVICE'])]

    with OUT_LOCK:
        colored_log('Got services:', ', '.join(map(str, result)))
    return result


def list_services(_args):
    get_services()


def start_services(_args):
    for service in get_services():
        service.up()


def stop_services(_args):
    for service in get_services():
        service.down()


def logs_services(_args):
    for service in get_services():
        service.logs()


def validate_checkers(_args):
    for service in get_services():
        service.validate_checker()


def validate_structure(_args):
    was_error = False
    for service in get_services():
        validator = StructureValidator(BASE_DIR, service)
        if not validator.validate():
            was_error = True

    if was_error:
        with OUT_LOCK:
            colored_log('Structure validator: failed', color=ColorType.FAIL)
            raise AssertionError


def dump_tasks(_args):
    result = {'tasks': []}
    for service in get_services():
        info = service.checker_info
        checker_type = 'gevent'
        if info['attack_data']:
            checker_type += '_pfr'

        result['tasks'].append({
            'name': service.name,
            'checker': f'{service.name}/checker.py',
            'checker_timeout': info['timeout'],
            'checker_type': checker_type,
            'places': info['timeout'],
            'puts': 1,
            'gets': 1,
        })

    colored_log('\n' + yaml.safe_dump(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Validate checkers for A&D. '
                    'Host & number of runs are passed with HOST and RUNS env vars'
    )
    subparsers = parser.add_subparsers()

    list_parser = subparsers.add_parser(
        'list',
        help='List services to test',
    )
    list_parser.set_defaults(func=list_services)

    up_parser = subparsers.add_parser(
        'up',
        help='Start services',
    )
    up_parser.set_defaults(func=start_services)

    down_parser = subparsers.add_parser(
        'down',
        help='Stop services',
    )
    down_parser.set_defaults(func=stop_services)

    logs_parser = subparsers.add_parser(
        'logs',
        help='Print logs for services',
    )
    logs_parser.set_defaults(func=logs_services)

    check_parser = subparsers.add_parser(
        'check',
        help='Run checkers validation',
    )
    check_parser.set_defaults(func=validate_checkers)

    validate_parser = subparsers.add_parser(
        'validate',
        help='Run structure validation',
    )
    validate_parser.set_defaults(func=validate_structure)

    dump_parser = subparsers.add_parser(
        'dump_tasks',
        help='Dump tasks in YAML for ForcAD',
    )
    dump_parser.set_defaults(func=dump_tasks)

    parsed = parser.parse_args()

    if "func" not in parsed:
        print("Type -h")
        exit(1)

    try:
        parsed.func(parsed)
    except AssertionError:
        exit(1)
    except Exception as e:
        tb = traceback.format_exc()
        print('Got exception, report it:', e, tb)
        exit(1)
