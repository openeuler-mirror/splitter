import subprocess

from typing import List

from tools.parse import parse
from tools.download import rpm
from tools.splitter.loader import SplitterLoader
from tools.logger import logger

from tools import SLICE_PATH, SLICE_REPO, SLICE_DIR

# For better extension, such as `risc-v`, etc.
ARCHES = {
    "x86_64": "x86_64",
    "amd64": "x86_64",
    "aarch64": "aarch64",
    "arm64": "aarch64"
}


def _release_check(release: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", SLICE_REPO, release],
            capture_output=True,
            text=True,
            check=True
        )
        if not bool(result.stdout.strip()):
            raise ValueError(f"Release: {release} is invalid!")
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Release: {release} is invalid!")


def _architecture_check(arch: str) -> str:
    if arch not in ARCHES:
        raise ValueError(f"Architecture: {arch} is invalid!")
    return ARCHES[arch]


def _slices_check(slices: List[str]) -> None:
    """
    The slice sdf file is required to be named
    as {packagename}_{slicename}, e.g., `python3_bins`
    """
    for sc in slices:
        if "_" not in sc:
            raise ValueError(f"Slice: {sc}'s name is invalid!")


def _clone_slices(release: str, path: str) -> None:
    clone_command = [
        "git", "clone", "-b", release, SLICE_REPO, path
    ]
    try:
        subprocess.run(
            clone_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info("Clone slice repository successful")
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Clone slice repository failed: {e.stderr}")


class Splitter:
    """
    A class to handle the splitting of packages based on specified
    slice dependencies release, and architecture.
    """
    release: str
    arch: str
    output: str
    slices: List[str]

    def __init__(self,
                 release: str,
                 arch: str,
                 output: str,
                 slices: List[str]
        ):
        self.release = f"openEuler-{release.upper()}"
        self.output = output
        self.slices = slices
        # checks
        _slices_check(self.slices)
        _release_check(self.release)
        self.arch = _architecture_check(arch)
        # initialize loader
        _clone_slices(self.release, SLICE_PATH)
        self.loader = SplitterLoader(
            sdf_dir=SLICE_DIR,
            release=self.release
        )

    def cut(self):
        """
        Parse slice configurations and extract the necessary
        files for the specified slice dependencies.

        Steps:
        1. Normalize and validata the architecture parameter.
        2. Load required slices and their contents.
        3. Download and extract the required files.
        4. Perform extra operations if any.
        """
        all_slices = set()
        logger.info(f"Splitting packages from {self.release} ({self.arch}) to {self.output}")
        for sc in self.slices:
            deps = self.loader.get_deps(sc, None)
            all_slices.update(deps)
            all_slices.add(sc)
        logger.info(f"Total: {len(all_slices)} slices:")
        logger.info(f"{all_slices}")

        # create DNF API client
        dnf_client = rpm.init_dnf_client(self.arch, self.release, self.output)
        for sc in all_slices:
            sdf_pkg, contents = self.loader.get_contents(sc)
            if not contents:
                continue
            local_pkg = rpm.download(dnf_client, sdf_pkg)
            parse.extract_files(local_pkg, self.output, contents)
            """
            slice content extra operations
            """
            extras = self.loader.get_extras(sc)
            for extra in extras:
                (
                    extra
                    .linux_arm64_handler(local_pkg, self.output)
                    .linux_amd64_handler(local_pkg, self.output)
                    .copy_handler(self.output)
                    .text_handler(self.output)
                    .manifest_handler(self.output)
                )

        # clear cache and close dnf.Base
        rpm.clear(dnf_client)
