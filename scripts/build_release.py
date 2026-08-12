#!/usr/bin/env python3
"""Build and validate a deterministic Voice Notify release ZIP.

The archive is built from the current working tree, including modified tracked
files and untracked files that are not ignored by Git. Ignored files (including
``dist/``) are never included. Two independent ZIPs are produced and compared
before the final artifact is installed atomically.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from typing import Mapping


ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PACKAGE_ROOT = "codex-voice-notify"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
MAX_RELEASE_FILES = 200
MAX_ARCHIVE_ENTRIES = 256
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_FILE_BYTES = 64 * 1024 * 1024
MAX_ARCHIVE_BYTES = 72 * 1024 * 1024
MAX_PATH_BYTES = 300
MAX_PATH_PARTS = 8
VOICES = ("female", "male")
LANGUAGES = ("ko", "ja", "en", "ru", "zh-CN")
EVENT_AUDIO_FILES = (
    "permission-request.wav",
    "post-compact.wav",
    "post-tool-use.wav",
    "pre-compact.wav",
    "pre-tool-use.wav",
    "session-start.wav",
    "stop.wav",
    "subagent-start.wav",
    "subagent-stop.wav",
    "user-prompt-submit.wav",
)
ROOT_RELEASE_FILES = frozenset(
    {
        ".gitattributes",
        ".gitignore",
        "ASSET_LICENSE.md",
        "CHANGELOG.md",
        "FISH_AUDIO_RESEARCH_LICENSE.md",
        "LICENSE",
        "PRIVACY.md",
        "README.ko.md",
        "README.md",
        "SECURITY.md",
        "SUBMISSION.md",
        "SUPPORT.md",
        "TERMS.md",
        "THIRD_PARTY_NOTICES.md",
    }
)
STRUCTURAL_RELEASE_FILES = frozenset(
    {
        ".agents/plugins/marketplace.json",
        ".codex-plugin/plugin.json",
        ".github/workflows/ci.yml",
        "assets/audio/manifest.json",
        "assets/audio/phrases.json",
        "assets/composer-icon.png",
        "assets/icon.svg",
        "assets/logo.png",
        "evals/cases.json",
        "hooks/hooks.json",
        "hooks/play_notify.ps1",
        "hooks/play_notify.py",
        "hooks/play_notify.sh",
        "scripts/build_audio_manifest.py",
        "scripts/build_release.py",
        "scripts/validate_package.py",
        "scripts/voice_notify_config.ps1",
        "scripts/voice_notify_config.py",
        "scripts/voice_notify_config.sh",
        "skills/voice-notify-settings/SKILL.md",
        "tests/test_voice_notify.py",
    }
)
EXPECTED_AUDIO_FILES = frozenset(
    "assets/audio/%s/%s/%s" % (voice, language, filename)
    for voice in VOICES
    for language in LANGUAGES
    for filename in EVENT_AUDIO_FILES
)
EXPECTED_RELEASE_FILES = (
    ROOT_RELEASE_FILES | STRUCTURAL_RELEASE_FILES | EXPECTED_AUDIO_FILES
)
FORBIDDEN_FILE_NAMES = frozenset(
    {
        ".DS_Store",
        ".env",
        "credentials.json",
        "id_dsa",
        "id_ed25519",
        "id_rsa",
    }
)
FORBIDDEN_SUFFIXES = (".key", ".pem", ".pyc", ".pyo")
BINARY_RELEASE_SUFFIXES = (".png", ".wav")
PRIVATE_PATH_PATTERNS = (
    re.compile(r"(?i)/" + r"Users/[^/\s]+/"),
    re.compile(r"(?i)/" + r"home/[^/\s]+/"),
    re.compile(r"(?i)[a-z]:[\\/]+" + r"Users[\\/]+[^\\/\s]+[\\/]"),
)
PRIVATE_PATH_BYTE_PATTERNS = (
    re.compile(b"(?i)/" + b"Users/" + rb"[^/\s\x00]+/"),
    re.compile(b"(?i)/" + b"home/" + rb"[^/\s\x00]+/"),
    re.compile(
        rb"(?i)[a-z]:[\\/]+" + b"Users" + rb"[\\/]+[^\\/\s\x00]+[\\/]"
    ),
)


class ReleaseBuildError(RuntimeError):
    """Raised when the working tree or release artifact is unsafe."""


def _run_git(*arguments: str) -> bytes:
    try:
        return subprocess.check_output(
            ("git", "-C", str(ROOT), *arguments),
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        detail = getattr(error, "stderr", b"").decode("utf-8", "replace").strip()
        raise ReleaseBuildError("Git file discovery failed: %s" % detail) from error


def _path_collision_key(path: str) -> str:
    """Return the cross-platform collision key used by release portals."""

    return unicodedata.normalize("NFC", path).casefold()


def _check_path_collisions(paths: list[str], *, context: str) -> None:
    seen: dict[str, str] = {}
    for path in paths:
        key = _path_collision_key(path)
        previous = seen.get(key)
        if previous is not None:
            raise ReleaseBuildError(
                "%s paths collide after Unicode NFC normalization and case folding: "
                "%s, %s" % (context, previous, path)
            )
        seen[key] = path


def _check_release_path(relative: pathlib.PurePosixPath) -> None:
    parts = relative.parts
    if relative.is_absolute() or ".." in parts or relative.as_posix() in {"", "."}:
        raise ReleaseBuildError("Unsafe release path: %s" % relative)
    if parts[0] in {".git", "dist"}:
        raise ReleaseBuildError("Release path is forbidden: %s" % relative)
    relative_text = relative.as_posix()
    if relative_text not in EXPECTED_RELEASE_FILES:
        raise ReleaseBuildError(
            "Unexpected release path (not in the exact release contract): %s"
            % relative
        )
    if unicodedata.normalize("NFC", relative_text) != relative_text:
        raise ReleaseBuildError("Release paths must use Unicode NFC: %s" % relative)
    if len(relative_text.encode("utf-8")) > MAX_PATH_BYTES:
        raise ReleaseBuildError("Release path is too long: %s" % relative)
    if len(parts) > MAX_PATH_PARTS:
        raise ReleaseBuildError("Release path is too deep: %s" % relative)
    for index, component in enumerate(parts):
        if component in FORBIDDEN_FILE_NAMES or component.endswith(FORBIDDEN_SUFFIXES):
            raise ReleaseBuildError("Sensitive or generated file is forbidden: %s" % relative)
        if component == "__pycache__":
            raise ReleaseBuildError("Python cache is forbidden: %s" % relative)
        if component.startswith(".") and not (
            index == 0
            and component
            in {".agents", ".codex-plugin", ".github", ".gitattributes", ".gitignore"}
        ):
            raise ReleaseBuildError("Unexpected hidden release path: %s" % relative)


def _discover_release_paths() -> tuple[pathlib.PurePosixPath, ...]:
    raw = _run_git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    discovered: list[pathlib.PurePosixPath] = []
    for encoded_path in raw.split(b"\0"):
        if not encoded_path:
            continue
        try:
            text_path = encoded_path.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ReleaseBuildError("Release paths must be valid UTF-8") from error
        relative = pathlib.PurePosixPath(text_path)
        if relative.parts and relative.parts[0] == "dist":
            # dist/ is intentionally ignored and must never nest inside itself.
            continue
        _check_release_path(relative)
        discovered.append(relative)
    discovered_text = [item.as_posix() for item in discovered]
    if len(discovered_text) != len(set(discovered_text)):
        raise ReleaseBuildError("Git returned duplicate release paths")
    _check_path_collisions(discovered_text, context="Source")
    return tuple(sorted(discovered, key=lambda item: item.as_posix().encode("utf-8")))


def _check_snapshot_limits(snapshot: Mapping[str, bytes]) -> None:
    if len(snapshot) > MAX_RELEASE_FILES:
        raise ReleaseBuildError(
            "Release has too many files: %d > %d" % (len(snapshot), MAX_RELEASE_FILES)
        )
    total_bytes = 0
    for relative, payload in snapshot.items():
        payload_size = len(payload)
        if payload_size > MAX_FILE_BYTES:
            raise ReleaseBuildError(
                "Release file is too large: %s (%d bytes)" % (relative, payload_size)
            )
        total_bytes += payload_size
        if any(pattern.search(payload) is not None for pattern in PRIVATE_PATH_BYTE_PATTERNS):
            raise ReleaseBuildError(
                "Private absolute user path found in release content: %s" % relative
            )

        # Binary assets may still leak paths through metadata. Decode their raw
        # bytes both ways so unmarked UTF-16 paths are caught as well as ASCII.
        even_payload = payload[: len(payload) - (len(payload) % 2)]
        for encoding in ("utf-16-le", "utf-16-be"):
            decoded_payload = even_payload.decode(encoding, errors="ignore")
            if any(
                pattern.search(decoded_payload) is not None
                for pattern in PRIVATE_PATH_PATTERNS
            ):
                raise ReleaseBuildError(
                    "Private absolute user path found in release content: %s" % relative
                )

        if not relative.endswith(BINARY_RELEASE_SUFFIXES):
            try:
                payload.decode("utf-8")
            except UnicodeDecodeError as error:
                raise ReleaseBuildError(
                    "Release text file must be valid UTF-8: %s" % relative
                ) from error
    if total_bytes > MAX_TOTAL_FILE_BYTES:
        raise ReleaseBuildError(
            "Release content is too large: %d > %d bytes"
            % (total_bytes, MAX_TOTAL_FILE_BYTES)
        )


def _capture_working_tree() -> dict[str, bytes]:
    snapshot: dict[str, bytes] = {}
    for relative in _discover_release_paths():
        source = ROOT.joinpath(*relative.parts)
        try:
            file_stat = source.lstat()
        except FileNotFoundError:
            # A tracked deletion is represented by the file being absent.
            continue
        if stat.S_ISLNK(file_stat.st_mode):
            raise ReleaseBuildError("Symbolic links are not allowed: %s" % relative)
        if not stat.S_ISREG(file_stat.st_mode):
            raise ReleaseBuildError("Only regular files may be packaged: %s" % relative)
        snapshot[relative.as_posix()] = source.read_bytes()
    actual_files = set(snapshot)
    if actual_files != EXPECTED_RELEASE_FILES:
        missing = sorted(EXPECTED_RELEASE_FILES - actual_files)
        extra = sorted(actual_files - EXPECTED_RELEASE_FILES)
        raise ReleaseBuildError(
            "Working tree does not match the exact release file contract "
            "(missing=%s, extra=%s)" % (missing, extra)
        )
    _check_snapshot_limits(snapshot)
    return snapshot


def _snapshot_digest(snapshot: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(snapshot, key=lambda item: item.encode("utf-8")):
        path_bytes = relative.encode("utf-8")
        payload = snapshot[relative]
        digest.update(len(path_bytes).to_bytes(8, "big"))
        digest.update(path_bytes)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _release_version(snapshot: Mapping[str, bytes]) -> str:
    manifest_path = ".codex-plugin/plugin.json"
    try:
        manifest = json.loads(snapshot[manifest_path].decode("utf-8"))
    except (KeyError, UnicodeError, ValueError, TypeError) as error:
        raise ReleaseBuildError("The plugin manifest is missing or invalid") from error
    version = manifest.get("version")
    if not isinstance(version, str) or re.fullmatch(r"\d+\.\d+\.\d+", version) is None:
        raise ReleaseBuildError("The plugin version must be a three-part SemVer")
    return version


def _directory_names(snapshot: Mapping[str, bytes]) -> tuple[str, ...]:
    directories = {PACKAGE_ROOT}
    for relative in snapshot:
        parts = pathlib.PurePosixPath(relative).parts[:-1]
        for count in range(1, len(parts) + 1):
            directories.add("/".join((PACKAGE_ROOT, *parts[:count])))
    return tuple(
        sorted(
            directories,
            key=lambda item: (item.count("/"), item.encode("utf-8")),
        )
    )


def _write_archive(
    destination: pathlib.Path,
    snapshot: Mapping[str, bytes],
    source_digest: str,
) -> None:
    with zipfile.ZipFile(
        destination,
        mode="w",
        # Stored entries avoid zlib-version-dependent output and make the ZIP
        # byte-reproducible across the supported macOS and Windows builders.
        compression=zipfile.ZIP_STORED,
        allowZip64=True,
    ) as archive:
        archive.comment = (
            "format=voice-notify-working-tree-v1\nsource-sha256=%s" % source_digest
        ).encode("ascii")
        for directory in _directory_names(snapshot):
            info = zipfile.ZipInfo(directory + "/", FIXED_ZIP_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = ((stat.S_IFDIR | 0o755) << 16) | 0x10
            archive.writestr(info, b"")
        for relative in sorted(snapshot, key=lambda item: item.encode("utf-8")):
            info = zipfile.ZipInfo(
                "%s/%s" % (PACKAGE_ROOT, relative),
                FIXED_ZIP_TIME,
            )
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, snapshot[relative])


def _validate_archive(
    archive_path: pathlib.Path,
    expected_snapshot: Mapping[str, bytes],
    expected_source_digest: str,
) -> str:
    expected_files = {
        "%s/%s" % (PACKAGE_ROOT, relative) for relative in expected_snapshot
    }
    expected_directories = {directory + "/" for directory in _directory_names(expected_snapshot)}
    expected_comment = (
        "format=voice-notify-working-tree-v1\nsource-sha256=%s"
        % expected_source_digest
    ).encode("ascii")
    archive_size = archive_path.stat().st_size
    if archive_size > MAX_ARCHIVE_BYTES:
        raise ReleaseBuildError(
            "ZIP is too large: %d > %d bytes" % (archive_size, MAX_ARCHIVE_BYTES)
        )
    with zipfile.ZipFile(archive_path, "r") as archive:
        if archive.comment != expected_comment:
            raise ReleaseBuildError("ZIP provenance comment is invalid")
        entries = archive.infolist()
        if len(entries) > MAX_ARCHIVE_ENTRIES:
            raise ReleaseBuildError(
                "ZIP has too many entries: %d > %d"
                % (len(entries), MAX_ARCHIVE_ENTRIES)
            )
        names = [info.filename for info in entries]
        if len(names) != len(set(names)):
            raise ReleaseBuildError("ZIP contains duplicate entries")
        collision_names = [
            info.filename[:-1] if info.is_dir() else info.filename
            for info in entries
        ]
        _check_path_collisions(collision_names, context="ZIP")
        actual_files: set[str] = set()
        actual_directories: set[str] = set()
        total_uncompressed_bytes = 0
        for info in entries:
            name = info.filename
            if "\\" in name:
                raise ReleaseBuildError("ZIP paths must use forward slashes: %s" % name)
            trimmed = name[:-1] if info.is_dir() else name
            if unicodedata.normalize("NFC", trimmed) != trimmed:
                raise ReleaseBuildError("ZIP paths must use Unicode NFC: %s" % name)
            if len(trimmed.encode("utf-8")) > MAX_PATH_BYTES:
                raise ReleaseBuildError("ZIP path is too long: %s" % name)
            pure = pathlib.PurePosixPath(trimmed)
            if (
                pure.is_absolute()
                or ".." in pure.parts
                or not pure.parts
                or pure.parts[0] != PACKAGE_ROOT
                or pure.as_posix() != trimmed
            ):
                raise ReleaseBuildError("Unsafe or non-canonical ZIP entry: %s" % name)
            if len(pure.parts) > MAX_PATH_PARTS:
                raise ReleaseBuildError("ZIP path is too deep: %s" % name)
            entry_type = (info.external_attr >> 16) & 0o170000
            if entry_type == stat.S_IFLNK:
                raise ReleaseBuildError("ZIP symbolic links are forbidden: %s" % name)
            if info.flag_bits & 0x1:
                raise ReleaseBuildError("Encrypted ZIP entries are forbidden: %s" % name)
            if info.date_time != FIXED_ZIP_TIME:
                raise ReleaseBuildError("ZIP timestamps must be fixed: %s" % name)
            if info.compress_type != zipfile.ZIP_STORED:
                raise ReleaseBuildError("ZIP entries must use stored mode: %s" % name)
            if info.is_dir():
                if entry_type != stat.S_IFDIR:
                    raise ReleaseBuildError(
                        "ZIP directory has an invalid entry type: %s" % name
                    )
                if info.file_size != 0:
                    raise ReleaseBuildError("ZIP directory must be empty: %s" % name)
                actual_directories.add(name)
                continue
            if entry_type != stat.S_IFREG:
                raise ReleaseBuildError("ZIP file has an invalid entry type: %s" % name)
            if info.compress_size != info.file_size:
                raise ReleaseBuildError(
                    "Stored ZIP entry size mismatch: %s" % name
                )
            if info.file_size > MAX_FILE_BYTES:
                raise ReleaseBuildError(
                    "ZIP entry is too large: %s (%d bytes)" % (name, info.file_size)
                )
            total_uncompressed_bytes += info.file_size
            if total_uncompressed_bytes > MAX_TOTAL_FILE_BYTES:
                raise ReleaseBuildError(
                    "ZIP content exceeds %d bytes" % MAX_TOTAL_FILE_BYTES
                )
            actual_files.add(name)
            relative_name = pathlib.PurePosixPath(*pure.parts[1:]).as_posix()
            if archive.read(info) != expected_snapshot.get(relative_name):
                raise ReleaseBuildError("ZIP content differs from the source snapshot: %s" % name)
        if archive.testzip() is not None:
            raise ReleaseBuildError("ZIP CRC validation failed: %s" % archive_path)
        if actual_files != expected_files:
            missing = sorted(expected_files - actual_files)
            extra = sorted(actual_files - expected_files)
            raise ReleaseBuildError(
                "ZIP file set mismatch (missing=%s, extra=%s)" % (missing, extra)
            )
        if actual_directories != expected_directories:
            missing = sorted(expected_directories - actual_directories)
            extra = sorted(actual_directories - expected_directories)
            raise ReleaseBuildError(
                "ZIP directory set mismatch (missing=%s, extra=%s)" % (missing, extra)
            )

        with tempfile.TemporaryDirectory(prefix="voice-notify-artifact-") as directory:
            extraction_root = pathlib.Path(directory)
            archive.extractall(extraction_root)
            packaged_root = extraction_root / PACKAGE_ROOT
            validator = packaged_root / "scripts" / "validate_package.py"
            completed = subprocess.run(
                (sys.executable, str(validator)),
                cwd=packaged_root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                raise ReleaseBuildError(
                    "Packaged artifact validation failed:\n%s" % completed.stdout.rstrip()
                )
    return hashlib.sha256(archive_path.read_bytes()).hexdigest()


def _validate_source() -> None:
    checks = (
        (
            "Source unit tests",
            (sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"),
        ),
        (
            "Source package validation",
            (sys.executable, str(ROOT / "scripts" / "validate_package.py")),
        ),
    )
    for label, command in checks:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            check=False,
        )
        if completed.returncode != 0:
            raise ReleaseBuildError("%s failed" % label)


def build_release(*, check_only: bool, force: bool) -> int:
    _validate_source()

    first_snapshot = _capture_working_tree()
    second_snapshot = _capture_working_tree()
    first_digest = _snapshot_digest(first_snapshot)
    source_digest = _snapshot_digest(second_snapshot)
    if first_digest != source_digest or first_snapshot.keys() != second_snapshot.keys():
        raise ReleaseBuildError("The working tree changed while it was being captured")

    version = _release_version(second_snapshot)
    output = DIST / ("%s-%s.zip" % (PACKAGE_ROOT, version))
    temporary_parent: str | None = None
    if not check_only:
        DIST.mkdir(parents=True, exist_ok=True)
        temporary_parent = str(DIST)

    with tempfile.TemporaryDirectory(
        prefix="voice-notify-release-",
        dir=temporary_parent,
    ) as directory:
        build_directory = pathlib.Path(directory)
        first_archive = build_directory / "build-a.zip"
        second_archive = build_directory / "build-b.zip"
        _write_archive(first_archive, second_snapshot, source_digest)
        _write_archive(second_archive, second_snapshot, source_digest)

        first_archive_digest = _validate_archive(
            first_archive,
            second_snapshot,
            source_digest,
        )
        second_archive_digest = _validate_archive(
            second_archive,
            second_snapshot,
            source_digest,
        )
        if (
            first_archive_digest != second_archive_digest
            or first_archive.read_bytes() != second_archive.read_bytes()
        ):
            raise ReleaseBuildError("The two release ZIPs are not byte-identical")

        final_snapshot = _capture_working_tree()
        if (
            final_snapshot.keys() != second_snapshot.keys()
            or _snapshot_digest(final_snapshot) != source_digest
        ):
            raise ReleaseBuildError("The working tree changed during the release build")

        if check_only:
            print(
                "PASS: deterministic artifact check for %s (%d files, sha256=%s)"
                % (version, len(second_snapshot), first_archive_digest)
            )
            return 0

        if output.exists():
            existing_digest = hashlib.sha256(output.read_bytes()).hexdigest()
            if existing_digest == first_archive_digest:
                print(
                    "PASS: existing release artifact already matches: %s (sha256=%s)"
                    % (output, existing_digest)
                )
                return 0
            if not force:
                raise ReleaseBuildError(
                    "Release artifact already exists with different bytes; rerun with "
                    "--force only after reviewing it: %s" % output
                )
        os.replace(first_archive, output)
        os.chmod(output, 0o644)
        print(
            "PASS: wrote %s (%d files, sha256=%s)"
            % (output, len(second_snapshot), first_archive_digest)
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build the current tracked and non-ignored working tree twice, "
            "validate both ZIPs, compare them, and write dist/<name>-<version>.zip."
        )
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Build, validate, and compare in a temporary directory without writing dist/.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing same-version ZIP after all checks pass.",
    )
    arguments = parser.parse_args()
    if arguments.check_only and arguments.force:
        parser.error("--force cannot be combined with --check-only")
    try:
        return build_release(check_only=arguments.check_only, force=arguments.force)
    except ReleaseBuildError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
