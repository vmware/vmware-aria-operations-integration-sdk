#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import os
from pathlib import Path

import pytest
from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError, Validator

from vmware_aria_operations_integration_sdk.validation.input_validators import NotEmptyValidator, AdapterKeyValidator, \
    IntegerValidator, TimeValidator, NewProjectDirectoryValidator, UniquenessValidator, ChainValidator, \
    ProjectValidator, EulaValidator, ImageValidator

rel_path = Path(__file__).resolve().parent


def test_not_empty_validator_pass():
    nev = NotEmptyValidator("NEV")
    nev.validate(Document("Not Empty"))


def test_not_empty_validator_fail_empty():
    nev = NotEmptyValidator("NEV")
    with pytest.raises(ValidationError):
        nev.validate(Document(""))


def test_not_empty_validator_fail_blank():
    nev = NotEmptyValidator("NEV")
    with pytest.raises(ValidationError):
        nev.validate(Document(" \t"))


def test_adapter_key_validator_pass():
    acv = AdapterKeyValidator()
    acv.validate(Document("valid_adapter_KEY"))


def test_adapter_key_validator_fail_blank():
    acv = AdapterKeyValidator()
    with pytest.raises(ValidationError):
        acv.validate(Document(" "))


def test_adapter_key_validator_fail_special_characters():
    acv = AdapterKeyValidator()
    with pytest.raises(ValidationError):
        acv.validate(Document("invalid_adapter(key)"))


def test_adapter_key_validator_fail_stars_with_number():
    acv = AdapterKeyValidator()
    with pytest.raises(ValidationError):
        acv.validate(Document("4_invalid_adapter"))


def test_integer_validator_pass_blank():
    iv = IntegerValidator("IV")
    iv.validate(Document(" "))


def test_integer_validator_pass_integer():
    iv = IntegerValidator("IV")
    iv.validate(Document("45"))


def test_integer_validator_fail_float():
    iv = IntegerValidator("IV")
    with pytest.raises(ValidationError):
        iv.validate(Document("45.3"))


def test_integer_validator_fail_string():
    iv = IntegerValidator("IV")
    with pytest.raises(ValidationError):
        iv.validate(Document("two"))


def test_time_validator_pass_no_unit():
    tv = TimeValidator("TV")
    tv.validate(Document("12"))


def test_time_validator_pass_s_unit():
    tv = TimeValidator("TV")
    tv.validate(Document("12s"))


def test_time_validator_pass_m_unit():
    tv = TimeValidator("TV")
    tv.validate(Document("12m"))


def test_time_validator_pass_h_unit():
    tv = TimeValidator("TV")
    tv.validate(Document("12.5h"))


def test_time_validator_fail_empty():
    tv = TimeValidator("TV")
    with pytest.raises(ValidationError):
        tv.validate(Document(""))


def test_time_validator_fail_invalid_unit():
    tv = TimeValidator("TV")
    with pytest.raises(ValidationError):
        tv.validate(Document("12r"))


def test_time_validator_fail_non_numeric():
    tv = TimeValidator("TV")
    with pytest.raises(ValidationError):
        tv.validate(Document("1two"))


def test_time_validator_fail_negative():
    tv = TimeValidator("TV")
    with pytest.raises(ValidationError):
        tv.validate(Document("-12m"))


def test_new_project_directory_validator_pass():
    npdv = NewProjectDirectoryValidator()
    npdv.validate(Document(os.path.join(rel_path, "non-existing-directory")))


def test_new_project_directory_validator_fail_file():
    npdv = NewProjectDirectoryValidator()
    with pytest.raises(ValidationError):
        npdv.validate(Document(os.path.join(rel_path, "test_input_validators.py")))


def test_new_project_directory_validator_fail_non_empty_directory():
    npdv = NewProjectDirectoryValidator()
    with pytest.raises(ValidationError):
        npdv.validate(Document(os.path.join(rel_path, "..", "validation")))


def test_uniqueness_validator_pass():
    uv = UniquenessValidator("UV", ["one", "two"])
    uv.validate(Document("three"))


def test_uniqueness_validator_fail():
    uv = UniquenessValidator("UV", ["one", "two"])
    with pytest.raises(ValidationError):
        uv.validate(Document("two"))


def test_eula_validator_pass():
    ev = EulaValidator()
    ev.validate(Document(os.path.join(rel_path, "test_mp", "eula.txt")))


def test_eula_validator_pass_empty():
    ev = EulaValidator()
    ev.validate(Document(""))


def test_eula_validator_non_existing_file():
    ev = EulaValidator()
    with pytest.raises(ValidationError):
        ev.validate(Document(os.path.join(rel_path, "test_mp", "eula_fake.txt")))


def test_eula_validator_wrong_file_type():
    ev = EulaValidator()
    with pytest.raises(ValidationError):
        ev.validate(Document(os.path.join(rel_path, "test_mp", "circle-256.png")))


def test_image_validator_pass():
    iv = ImageValidator()
    iv.validate(Document(os.path.join(rel_path, "test_mp", "circle-256.png")))


def test_image_validator_pass_empty():
    iv = ImageValidator()
    iv.validate(Document(""))


def test_image_validator_fail_non_existing_file():
    iv = ImageValidator()
    with pytest.raises(ValidationError):
        iv.validate(Document(os.path.join(rel_path, "test_mp", "square-256.png")))


def test_image_validator_fail_wrong_image_type():
    iv = ImageValidator()
    with pytest.raises(ValidationError):
        iv.validate(Document(os.path.join(rel_path, "test_mp", "circle-256.jpg")))


def test_image_validator_fail_wrong_image_size():
    iv = ImageValidator()
    with pytest.raises(ValidationError):
        iv.validate(Document(os.path.join(rel_path, "test_mp", "circle-128.png")))


def test_project_validator_pass():
    pv = ProjectValidator()
    pv.validate(Document(os.path.join(rel_path, "test_mp")))


def test_project_validator_fail_non_project_dir():
    pv = ProjectValidator()
    with pytest.raises(ValidationError):
        pv.validate(Document(os.path.join(rel_path)))


def test_project_validator_fail_non_existing_dir():
    pv = ProjectValidator()
    with pytest.raises(ValidationError):
        pv.validate(Document(os.path.join(rel_path, "fake_mp")))


class ConstValidator(Validator):
    def __init__(self, return_value):
        self.return_value = return_value

    def validate(self, document: Document):
        if not self.return_value:
            raise ValidationError()


def test_chain_validator_pass():
    cv = ChainValidator([ConstValidator(True), ConstValidator(True)])
    cv.validate(Document())


def test_chain_validator_fail():
    cv = ChainValidator([ConstValidator(True), ConstValidator(False)])
    with pytest.raises(ValidationError):
        cv.validate(Document())


def test_chain_validator_pass_document_pass():
    cv = ChainValidator([ConstValidator(True), ConstValidator(True), NotEmptyValidator("NEV")])
    cv.validate(Document("Not Empty"))


def test_chain_validator_pass_document_fail():
    cv = ChainValidator([ConstValidator(True), ConstValidator(True), NotEmptyValidator("NEV")])
    with pytest.raises(ValidationError):
        cv.validate(Document(""))
