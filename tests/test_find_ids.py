from pathlib import Path

from lsprotocol.types import (
    DefinitionParams,
    Location,
    Range,
    Position,
    TextDocumentIdentifier,
)
import pytest
import pytest_asyncio
from pytest_lsp import LanguageClient

from conftest import open_file

pytestmark = [
    pytest.mark.parametrize("client", ("sample_workspace",), indirect=True),
]


@pytest_asyncio.fixture
async def opened_file(
    client: LanguageClient, sample_workspace: Path, request
) -> Path:
    sls = sample_workspace / request.param
    async with open_file(client, sls):
        yield sls


@pytest.mark.asyncio
@pytest.mark.parametrize("opened_file", ("opensuse/base.sls",), indirect=True)
async def test_find_id_in_document(client: LanguageClient, opened_file: Path):
    results = await client.text_document_definition_async(
        params=DefinitionParams(
            position=Position(line=9, character=14),
            text_document=TextDocumentIdentifier(uri=f"file://{opened_file}"),
        )
    )
    assert results is not None
    assert results == Location(
        uri=f"file://{opened_file}",
        range=Range(
            start=Position(line=0, character=0),
            end=Position(line=5, character=0),
        ),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "opened_file,position",
    (
        pytest.param("bar.sls", (6, 8), id="direct"),
        pytest.param("foo.sls", (7, 8), id="indirect"),
    ),
    indirect=("opened_file",),
)
async def test_find_id_in_include(
    client: LanguageClient, opened_file: Path, position: tuple[int, int]
):
    results = await client.text_document_definition_async(
        params=DefinitionParams(
            position=Position(line=position[0], character=position[1]),
            text_document=TextDocumentIdentifier(uri=f"file://{opened_file}"),
        )
    )
    assert results is not None
    assert results == Location(
        uri=f"file://{opened_file.parent / 'quo.sls'}",
        range=Range(
            start=Position(line=0, character=0),
            end=Position(line=6, character=0),
        ),
    )
