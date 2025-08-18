import json
import pickle
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional, Union

from salt_lsp.base_types import StateNameCompletion


def dump_state_name_completions(target: Optional[Union[str, Path]] = None) -> None:
    state_completions: Dict[str, StateNameCompletion] = {}

    with tempfile.TemporaryDirectory() as tmpdirname:
        salt_dest = Path(tmpdirname) / "salt"
        salt_dest.mkdir()

        with open(salt_dest / "minion", "w", encoding="utf-8") as minion_file:
            minion_file.write(f"root_dir: {tmpdirname}")

        try:
            mod_list, docs = (
                json.loads(
                    str(
                        subprocess.run(
                            shlex.split(
                                f"salt-call --local -c {salt_dest} --out json "
                                f"baredoc.{mod_name}"
                            ),
                            capture_output=True,
                            check=True,
                        ).stdout,
                        encoding="utf-8",
                    )
                )
                for mod_name in ("list_states", "state_docs")
            )
        except subprocess.CalledProcessError as err:
            if not shutil.which("salt-call"):
                raise RuntimeError(
                    "Unable to find 'salt-call' in PATH, which is required to dump state metadata. "
                    "Please ensure that Salt is installed and available in the salt_lsp PATH."
                    f"retcode: {err.returncode}\n\nstdout: {err.stdout}\n\nstderr: {err.stderr}"
                ) from err
            raise RuntimeError(
                f"Failed to run salt-call for dumping state metadata: {err}"
                f"retcode: {err.returncode}\n\nstdout: {err.stdout}\n\nstderr: {err.stderr}"
            ) from err

        for module in mod_list["local"]:
            state_completions[module] = StateNameCompletion(
                module, mod_list["local"][module], docs["local"]
            )

    target = Path(target or Path(__file__).resolve().parent / "data" / "states.pickle")
    if not target.parent.exists():
        target.parent.mkdir(parents=True)
    elif not target.parent.is_dir():
        raise ValueError(f"Target parent path '{target.parent}' is not a directory")

    with open(target, "wb") as states_file:
        pickle.dump(state_completions, states_file)
