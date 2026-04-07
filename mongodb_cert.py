from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass
class CheckResult:
#Represents the outcome of an individual verification step.

    name: str
    status: str
    details: str
    expected: Optional[str] = None
    observed: Optional[str] = None

    def as_row(self) -> Tuple[str, str, str, str, str]:
        return (
            self.name,
            self.expected or "",
            self.observed or "",
            self.status,
            self.details,
        )


def compute_backup_size(mgdb_data_value: Any) -> Optional[str]:
#Return backup size (data size * 2) if mgdbData can be parsed as an int.ß
    if mgdb_data_value is None:
        return None
    try:
        size = int(str(mgdb_data_value).strip())
    except (TypeError, ValueError):
        return None
    return str(size * 2)


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=True)


def run_command(cmd: Sequence[str]) -> Tuple[int, str, str]:
#Execute a command and capture its exit code, stdout and stderr.ßß
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return (127, "", f"{cmd[0]} not found")
    except Exception as exc:  
        return (1, "", str(exc))

    return (completed.returncode, completed.stdout.strip(), completed.stderr.strip())


def check_mongodb_binary() -> CheckResult:
    binary_path = shutil.which("mongod")
    print(f"Binary path: {binary_path}")
    if not binary_path:
        return CheckResult(
            name="MongoDB binary",
            status="FAIL",
            details="mongod binary not found in PATH.",
            expected="mongod",
            observed="missing",
        )
    return CheckResult(
        name="MongoDB binary",
        status="PASS",
        details="mongod binary located.",
        expected="mongod",
        observed=binary_path,
    )


def check_mongodb_version(expected_version: Optional[str]) -> CheckResult:
    binary_path = shutil.which("mongod")
    if not binary_path:
        return CheckResult(
            name="MongoDB version",
            status="FAIL",
            details="mongod binary not found. Unable to gather version.",
            expected=expected_version,
            observed="unknown",
        )

    code, stdout, stderr = run_command([binary_path, "--version"])
    if code != 0:
        return CheckResult(
            name="MongoDB version",
            status="FAIL",
            details=f"mongod --version failed: {stderr or stdout}",
            expected=expected_version,
            observed="unknown",
        )

    match = re.search(r"db version v?([\d\.]+)", stdout)
    observed_version = match.group(1) if match else stdout.splitlines()[0]

    if expected_version:
        status = "PASS" if observed_version.startswith(expected_version) else "FAIL"
        detail = (
            "Version matches request."
            if status == "PASS"
            else "Detected version does not match requested version."
        )
    else:
        status = "WARN"
        detail = "No requested version provided; reporting detected version only."

    return CheckResult(
        name="MongoDB version",
        status=status,
        details=detail,
        expected=expected_version,
        observed=observed_version,
    )


def check_service_status(service_name: str) -> CheckResult:
    if shutil.which("systemctl"):
        code, stdout, stderr = run_command(["systemctl", "is-active", service_name])
        observed = stdout.strip() or stderr or "unknown"
        if code == 0 and observed == "active":
            status = "PASS"
            detail = "Service is running."
        elif code == 3 and observed == "inactive":
            status = "FAIL"
            detail = "Service installed but not running."
        else:
            status = "FAIL"
            detail = f"systemctl returned {code}: {observed}"
    else:
        code, stdout, stderr = run_command(["service", service_name, "status"])
        combined = "\n".join(filter(None, [stdout, stderr]))
        if code == 0 and "running" in combined.lower():
            status = "PASS"
            detail = "Service is running (legacy service command)."
        else:
            status = "FAIL"
            detail = f"service command returned {code}: {combined or 'unknown'}"
        observed = "running" if status == "PASS" else "not running"

    return CheckResult(
        name=f"{service_name} service",
        status=status,
        details=detail,
        expected="active",
        observed=observed,
    )


def check_port_listening(port: int) -> CheckResult:
    listeners: List[str] = []
    status = "FAIL"
    details = "Port not found in listener list."

    if shutil.which("ss"):
        code, stdout, stderr = run_command(["ss", "-ltnp"])
        if code == 0:
            listeners = stdout.splitlines()
        else:
            details = f"ss failed: {stderr or stdout}"
    elif shutil.which("netstat"):
        code, stdout, stderr = run_command(["netstat", "-ltnp"])
        if code == 0:
            listeners = stdout.splitlines()
        else:
            details = f"netstat failed: {stderr or stdout}"
    else:
        return CheckResult(
            name=f"Port {port}",
            status="WARN",
            details="Neither ss nor netstat available; cannot verify listeners.",
            expected=f"Listening on {port}",
            observed="unknown",
        )

    for line in listeners:
        if f":{port}" in line and "LISTEN" in line.upper():
            status = "PASS"
            details = "Port is listening."
            break

    observed = "listening" if status == "PASS" else "closed"
    return CheckResult(
        name=f"Port {port}",
        status=status,
        details=details,
        expected="LISTEN",
        observed=observed,
    )


def check_firewall_rule(port: int, protocol: str = "tcp") -> CheckResult:
    cmd = shutil.which("firewall-cmd")
    if cmd:
        code, stdout, stderr = run_command([cmd, "--list-ports"])
        if code != 0:
            return CheckResult(
                name="Firewall rule",
                status="WARN",
                details=f"firewall-cmd failed: {stderr or stdout}",
                expected=f"{port}/{protocol}",
                observed="unknown",
            )
        ports = stdout.split()
        if any(p.startswith(f"{port}/{protocol}") for p in ports):
            return CheckResult(
                name="Firewall rule",
                status="PASS",
                details="Port allowed via firewalld.",
                expected=f"{port}/{protocol}",
                observed="allowed",
            )
        return CheckResult(
            name="Firewall rule",
            status="FAIL",
            details="Port not found in firewalld allowed list.",
            expected=f"{port}/{protocol}",
            observed="blocked",
        )

    if shutil.which("ufw"):
        code, stdout, stderr = run_command(["ufw", "status"])
        if code != 0:
            return CheckResult(
                name="Firewall rule",
                status="WARN",
                details=f"ufw status failed: {stderr or stdout}",
                expected=f"{port}/{protocol}",
                observed="unknown",
            )
        combined = "\n".join([stdout, stderr])
        if str(port) in combined:
            return CheckResult(
                name="Firewall rule",
                status="PASS",
                details="Port found in UFW allow rules.",
                expected=f"{port}/{protocol}",
                observed="allowed",
            )
        return CheckResult(
            name="Firewall rule",
            status="FAIL",
            details="Port not listed in UFW allow rules.",
            expected=f"{port}/{protocol}",
            observed="blocked",
        )

    return CheckResult(
        name="Firewall rule",
        status="WARN",
        details="firewall-cmd/ufw not available; unable to inspect firewall.",
        expected=f"{port}/{protocol}",
        observed="unknown",
    )


def get_mongo_shell() -> Optional[str]:
    return shutil.which("mongosh") or shutil.which("mongo")


def run_mongo_eval(
    js_snippet: str,
    host: str,
    port: int,
    username: Optional[str],
    password: Optional[str],
    auth_db: str,
) -> Tuple[int, str, str]:
    shell = get_mongo_shell()
    if not shell:
        return (127, "", "Neither mongosh nor mongo client were found in PATH.")

    cmd = [
        shell,
        "--quiet",
        "--host",
        host,
        "--port",
        str(port),
        "--authenticationDatabase",
        auth_db,
        "--eval",
        js_snippet,
    ]
    if username:
        cmd.extend(["--username", username])
    if password:
        cmd.extend(["--password", password])

    return run_command(cmd)


def check_database_exists(
    db_name: Optional[str],
    host: str,
    port: int,
    username: Optional[str],
    password: Optional[str],
    auth_db: str,
) -> CheckResult:
    if not db_name:
        return CheckResult(
            name="Application database",
            status="WARN",
            details="No application database name provided.",
            expected="Provided",
            observed="missing",
        )

    snippet = (
        "const names = db.getMongo().getDBNames();"
        f'print(names.indexOf("{db_name}") !== -1 ? "FOUND" : "MISSING");'
    )

    code, stdout, stderr = run_mongo_eval(
        snippet, host, port, username, password, auth_db
    )
    if code != 0:
        return CheckResult(
            name="Application database",
            status="WARN",
            details=f"Unable to query MongoDB: {stderr or stdout}",
            expected=db_name,
            observed="unknown",
        )

    observed = stdout.strip().splitlines()[-1] if stdout else ""
    status = "PASS" if observed == "FOUND" else "FAIL"
    details = "Database exists." if status == "PASS" else "Database not found."
    return CheckResult(
        name="Application database",
        status=status,
        details=details,
        expected=db_name,
        observed="present" if status == "PASS" else "missing",
    )


def check_database_user(
    db_name: Optional[str],
    user: Optional[str],
    host: str,
    port: int,
    username: Optional[str],
    password: Optional[str],
    auth_db: str,
) -> CheckResult:
    if not db_name or not user:
        return CheckResult(
            name="Application user",
            status="WARN",
            details="Database name or user missing; cannot validate user.",
            expected=user or "Provided",
            observed="unknown",
        )

    snippet = (
        f'const usr = db.getSiblingDB("{db_name}").getUser("{user}");'
        'print(usr ? "FOUND" : "MISSING");'
    )
    code, stdout, stderr = run_mongo_eval(
        snippet, host, port, username, password, auth_db
    )
    if code != 0:
        return CheckResult(
            name="Application user",
            status="WARN",
            details=f"Unable to query MongoDB: {stderr or stdout}",
            expected=user,
            observed="unknown",
        )

    observed = stdout.strip().splitlines()[-1] if stdout else ""
    status = "PASS" if observed == "FOUND" else "FAIL"
    details = "User exists." if status == "PASS" else "User not found."
    return CheckResult(
        name="Application user",
        status=status,
        details=details,
        expected=user,
        observed="present" if status == "PASS" else "missing",
    )


def build_table(rows: Iterable[Tuple[str, str, str, str, str]]) -> List[str]:
    lines = [
        "| Item | Requested | Observed | Status | Details |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        safe_row = [cell.replace("\n", "<br>") for cell in row]
        lines.append("| " + " | ".join(safe_row) + " |")
    return lines


def build_kv_table(records: Dict[str, Any]) -> List[str]:
    if not records:
        return ["No custom options were provided."]
    lines = [
        "| Key | Value |",
        "| --- | --- |",
    ]
    for key in sorted(records):
        lines.append(f"| {key} | {format_value(records[key])} |")
    return lines


def generate_markdown(
    custom_options: Dict[str, Any],
    install_results: Sequence[CheckResult],
    config_results: Sequence[CheckResult],
) -> str:
    lines: List[str] = []
    host = socket.gethostname()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append("# MongoDB Installation Verification")
    lines.append("")
    lines.append(f"- Host: `{host}`")
    lines.append(f"- Generated: `{timestamp}`")
    lines.append("")
    lines.append("## User request details")
    lines.extend(build_kv_table(custom_options))
    lines.append("")
    lines.append("## Install verification")
    lines.extend(build_table(result.as_row() for result in install_results))
    lines.append("")
    lines.append("## Configuration verification")
    lines.extend(build_table(result.as_row() for result in config_results))
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    # Access morpheus dict directly (loaded by Morpheus Data UI)
    try:
        custom_options = morpheus.get("customOptions", {})
    except NameError:
        raise SystemExit(
            "morpheus variable not found. "
            "Ensure this script is run within Morpheus Data UI context."
        )

    if not custom_options:
        raise SystemExit("No customOptions found in morpheus payload.")

    expected_version_value = custom_options.get("mongodbVersion")
    expected_version = (
        str(expected_version_value).strip() if expected_version_value else None
    )

    requested_app_db = custom_options.get("mgApp")
    requested_app_user = custom_options.get("mgAppUser")
    requested_app_password = custom_options.get("mgAppPass")

    mongo_username = requested_app_user
    mongo_password = requested_app_password
    mongo_auth_db = requested_app_db or custom_options.get("mongodbAuthDb") or "admin"

    display_options = dict(custom_options)
    derived_backup_size = compute_backup_size(custom_options.get("mgdbData"))
    if derived_backup_size is not None:
        display_options.setdefault("mongodb_backup_size", derived_backup_size)

    mongo_service = os.environ.get("MONGODB_SERVICE", "mongod")
    mongo_host = os.environ.get("MONGODB_HOST", "127.0.0.1")
    mongo_port = int(os.environ.get("MONGODB_PORT", "27017"))

    install_results = [
        check_mongodb_binary(),
        check_mongodb_version(expected_version),
    ]

    config_results = [
        check_service_status(mongo_service),
        check_port_listening(mongo_port),
        check_firewall_rule(mongo_port, protocol="tcp"),
        check_database_exists(
            requested_app_db,
            host=mongo_host,
            port=mongo_port,
            username=mongo_username,
            password=mongo_password,
            auth_db=mongo_auth_db,
        ),
        check_database_user(
            requested_app_db,
            requested_app_user,
            host=mongo_host,
            port=mongo_port,
            username=mongo_username,
            password=mongo_password,
            auth_db=mongo_auth_db,
        ),
    ]

    markdown = generate_markdown(display_options, install_results, config_results)

    output_path = os.environ.get("MONGODB_VERIFICATION_OUTPUT")
    if output_path:
        Path(output_path).expanduser().write_text(markdown, encoding="utf-8")

    print(markdown)


if __name__ == "__main__":
    main()