import json
import os
import hashlib
import subprocess
from pathlib import Path

import pytest


ROOT = Path("/workspace/textd")
SAMPLE = "alpha beta gamma"
LATEST_GENERATION = 24

PRISTINE_HASHES = {
    "bin/build": "d30c8c505f3771343176879ee02bef48b272c7abb2f73c317aabb516d3c2289f",
    "bin/integration": "6c77011e97beb056d141550a0082f540c53fb662e495e281581a8060cdf607da",
    "bin/run-suite": "037ad0eade3428f31b2e659017dd76ca55611fb606ca1364bc09cc721337d749",
    "bin/stress": "047e45b1b3d2cbef0a871e422a45c4aecb6a92e5cb3d27233d4d3f4e368cd2fa",
    "src/main/java/io/harbor/textd/cli/HotReloadIntegrationRunner.java": "42b743fa308066b053f31cc3fd62afd769fa8b2789f905b669f2e2042e7ecec6",
    "src/main/java/io/harbor/textd/cli/HotReloadStressRunner.java": "1b43b517f29cb280e3f171b49abf2b35e4ff4f231990eacf5bc37d9c8b1ca595",
    "src/main/java/io/harbor/textd/cli/RuntimeDigestRunner.java": "ec3e81a86d4e9658234349b0c8d38b992405637461c421f98c355f634a3c83a8",
    "src/main/java/io/harbor/textd/cli/SessionReplayRunner.java": "740e0ad612b7f277560437a5a0edd2c7dea2a9f63f44ef281ad129a9450d563e",
}


def expected_output(revision: int) -> str:
    return f"GEN-{revision:03d}|ALPHA>BETA>GAMMA|PIPE-18528"


def run_command(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
        timeout=600,
        env=merged_env,
    )


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="session")
def pristine_surfaces() -> None:
    for relative_path, expected_hash in PRISTINE_HASHES.items():
        actual_hash = file_hash(ROOT / relative_path)
        assert actual_hash == expected_hash, f"unexpected contents for {relative_path}"


@pytest.fixture(scope="session")
def build_once(pristine_surfaces: None) -> None:
    assert ROOT.exists(), f"project directory missing: {ROOT}"
    run_command(["bash", "./bin/build"])


@pytest.fixture(scope="session")
def stress_result(build_once: None) -> subprocess.CompletedProcess[str]:
    return run_command(["bash", "./bin/stress", "500"], env={"TEXTD_SKIP_BUILD": "1"})


@pytest.fixture(scope="session")
def integration_result(build_once: None) -> dict:
    completed = run_command(["bash", "./bin/integration", str(LATEST_GENERATION)], env={"TEXTD_SKIP_BUILD": "1"})
    return json.loads(completed.stdout)


@pytest.fixture(scope="session")
def digest_result(build_once: None) -> dict:
    completed = run_command(
        [
            "java",
            "-cp",
            str(ROOT / "build/main-classes"),
            "io.harbor.textd.cli.RuntimeDigestRunner",
            str(ROOT / "build/plugins/customer-default.jar"),
            str(LATEST_GENERATION),
        ]
    )
    return json.loads(completed.stdout)


@pytest.fixture(scope="session")
def suite_result() -> subprocess.CompletedProcess[str]:
    return run_command(["bash", "./bin/run-suite"])


def test_public_runner_surfaces_are_pristine(pristine_surfaces: None) -> None:
    pass


def test_stress_runner_completes(stress_result: subprocess.CompletedProcess[str]) -> None:
    assert "stress-ok cycles=500" in stress_result.stdout


def test_stress_runner_has_no_metaspace_oom(stress_result: subprocess.CompletedProcess[str]) -> None:
    combined = stress_result.stdout + stress_result.stderr
    assert "java.lang.OutOfMemoryError" not in combined
    assert "Metaspace" not in combined


def test_generation_one_output(integration_result: dict) -> None:
    assert integration_result["input"] == SAMPLE
    assert integration_result["baseline"] == expected_output(1)


def test_current_output(integration_result: dict) -> None:
    assert integration_result["revision"] == LATEST_GENERATION
    assert integration_result["current"] == expected_output(LATEST_GENERATION)


def test_runtime_digest_reports_stable_run(digest_result: dict) -> None:
    assert digest_result["sample"] == SAMPLE
    assert digest_result["first"] == expected_output(1)
    assert digest_result["rev"] == LATEST_GENERATION
    assert digest_result["last"] == expected_output(LATEST_GENERATION)
    assert digest_result["start"] == ["textd-worker-1", "textd-worker-2", "textd-worker-3", "textd-worker-4"]
    assert digest_result["end"] == ["textd-worker-1", "textd-worker-2", "textd-worker-3", "textd-worker-4"]
    assert digest_result["same_workers"] is True
    assert digest_result["before_close"] is True
    assert digest_result["after_close"] is True


def test_full_suite_passes(suite_result: subprocess.CompletedProcess[str]) -> None:
    assert suite_result.stdout.strip() == "suite-ok"


@pytest.fixture(scope="session")
def replay_result(build_once: None) -> dict:
    completed = run_command(
        [
            "java",
            "-cp",
            str(ROOT / "build/main-classes"),
            "io.harbor.textd.cli.SessionReplayRunner",
            str(ROOT / "build/plugins/customer-default.jar"),
            str(LATEST_GENERATION),
        ]
    )
    return json.loads(completed.stdout)


def test_first_replay_session_stays_clean(replay_result: dict) -> None:
    first = replay_result["first"]
    assert first["first"] == expected_output(1)
    assert first["last"] == expected_output(LATEST_GENERATION)
    assert first["start"] == ["textd-worker-1", "textd-worker-2", "textd-worker-3", "textd-worker-4"]
    assert first["end"] == ["textd-worker-1", "textd-worker-2", "textd-worker-3", "textd-worker-4"]
    assert first["same_workers"] is True
    assert first["before_close"] is True
    assert first["after_close"] is True


def test_second_replay_session_stays_clean(replay_result: dict) -> None:
    second = replay_result["second"]
    assert second["first"] == expected_output(1)
    assert second["last"] == expected_output(LATEST_GENERATION)
    assert second["start"] == ["textd-worker-1", "textd-worker-2", "textd-worker-3", "textd-worker-4"]
    assert second["end"] == ["textd-worker-1", "textd-worker-2", "textd-worker-3", "textd-worker-4"]
    assert second["same_workers"] is True
    assert second["before_close"] is True
    assert second["after_close"] is True


def test_replay_sessions_unload_classes(replay_result: dict) -> None:
    first = replay_result["first"]
    second = replay_result["second"]
    assert first["unloaded_after_close"] > first["unloaded_before_close"]
    assert second["unloaded_after_close"] > second["unloaded_before_close"]


def test_replay_sessions_do_not_regress_unloading(replay_result: dict) -> None:
    first = replay_result["first"]
    second = replay_result["second"]
    assert second["unloaded_after_close"] >= first["unloaded_after_close"]
