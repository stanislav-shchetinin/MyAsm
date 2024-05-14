import contextlib
import io
import logging
import os
import tempfile

import machine
import pytest
import translator


@pytest.mark.golden_test("golden/*.yml")
def test_translator_asm_and_machine(golden, caplog):
    """Почти полная копия test_translator_and_machine из golden_bf_test. Детали
    см. там."""
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as tmpdirname:
        source = os.path.join(tmpdirname, "source")
        input_stream = os.path.join(tmpdirname, "input")
        target_data = os.path.join(tmpdirname, "target_data.o")
        target_code = os.path.join(tmpdirname, "target_code.o")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["in_source"])
        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["in_stdin"])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main(source, target_data, target_code)
            print("============================================================")
            machine.main(target_code, target_data, input_stream)

        with open(target_code, mode="rb") as file:
            code = file.read()

        with open(target_data, mode="rb") as file:
            data = file.read()

        assert data == golden.out["out_data"]
        assert code == golden.out["out_code"]
        assert stdout.getvalue() == golden.out["out_stdout"]
        assert caplog.text == golden.out["out_log"]
