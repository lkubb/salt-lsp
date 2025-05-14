from pathlib import Path

from lsprotocol.types import (
    CompletionContext,
    CompletionList,
    CompletionParams,
    CompletionTriggerKind,
    Position,
    TextDocumentIdentifier,
)
import pytest
import pytest_asyncio
from pytest_lsp import LanguageClient

from conftest import MODULE_DOCS, open_file
from salt_lsp.base_types import StateNameCompletion


TEST_FILE = """saltmaster.packages:
  pkg.installed:
    - pkgs:
      - salt-master

/srv/git/salt-states:
  file.:
    - target: /srv/salt

git -C /srv/salt pull -q:
  cron.:
    - user: root
    - minute: '*/5'
"""


@pytest_asyncio.fixture
async def slsfile(client: LanguageClient, tmp_path: Path) -> Path:
    sls = tmp_path / "test.sls"
    sls.write_text(TEST_FILE)
    async with open_file(client, sls):
        yield sls


@pytest.mark.asyncio
async def test_complete_of_file(
    client: LanguageClient,
    slsfile: Path,
    state_completions: dict[str, StateNameCompletion],
):
    results = await client.text_document_completion_async(
        params=CompletionParams(
            position=Position(line=6, character=7),
            text_document=TextDocumentIdentifier(uri=f"file://{slsfile}"),
            context=CompletionContext(
                trigger_kind=CompletionTriggerKind.TriggerCharacter,
                trigger_character=".",
            ),
        )
    )
    assert results is not None

    if isinstance(results, CompletionList):
        items = results.items
    else:
        items = results

    expected_completions = [
        (submod_name, MODULE_DOCS[f"file.{submod_name}"])
        for submod_name in state_completions["file"].state_sub_names
    ]
    completions = [(item.label, item.documentation) for item in items]
    assert completions == expected_completions
