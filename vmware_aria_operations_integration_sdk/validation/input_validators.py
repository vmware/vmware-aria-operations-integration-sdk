#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import os
from typing import List
from typing import Optional

from PIL import Image
from PIL import UnidentifiedImageError
from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError
from prompt_toolkit.validation import Validator


class NotEmptyValidator(Validator):  # type: ignore
    def __init__(self, label: str) -> None:
        self.label = label

    def validate(self, document: Document) -> None:
        if not document.text:
            raise ValidationError(message=f"{self.label} cannot be empty.")
        if not document.text.strip():
            raise ValidationError(message=f"{self.label} cannot be blank.")


class AdapterKeyValidator(NotEmptyValidator):
    def __init__(self) -> None:
        super().__init__("Adapter Key")

    def validate(self, document: Document) -> None:
        super().validate(document)
        string = document.text
        if string != self._strip_special_characters(string):
            raise ValidationError(
                message=f"{self.label} cannot contain special characters."
            )
        if string[0].isdigit():
            raise ValidationError(message=f"{self.label} cannot begin with a digit.")

    @classmethod
    def _strip_special_characters(cls, string: str) -> str:
        return "".join(e for e in string if e.isalnum() or e == "_")

    @classmethod
    def default(cls, string: str) -> str:
        default = cls._strip_special_characters(string)
        if default[0].isdigit():
            return "Adapter" + default
        return default


class IntegerValidator(Validator):  # type: ignore
    def __init__(self, label: str) -> None:
        self.label = label

    def validate(self, document: Document) -> None:
        try:
            if document.text.strip():
                int(document.text)
        except ValueError as e:
            raise ValidationError(message=f"{self.label} must be an integer.")


class TimeValidator(NotEmptyValidator):
    def __init__(self, label: str) -> None:
        super().__init__(label)

    def validate(self, document: Document) -> None:
        super().validate(document)
        if document.text:
            TimeValidator.get_sec(self.label, document.text)

    @classmethod
    def get_sec(cls, label: str, time_str: str) -> float:
        """Get seconds from time."""
        try:
            unit = time_str[-1]
            seconds = None
            if unit == "s":
                seconds = float(time_str[0:-1].strip())
            elif unit == "m":
                seconds = float(time_str[0:-1].strip()) * 60
            elif unit == "h":
                seconds = float(time_str[0:-1].strip()) * 3600
            else:  # no unit specified, default to minutes
                seconds = float(time_str) * 60
            if seconds <= 0:
                raise ValidationError(
                    message=f"Invalid time. {label} cannot be zero or negative."
                )
            return seconds
        except ValueError:
            raise ValidationError(
                message=f"Invalid time. {label} should be a numeric value in minutes, or a numeric value "
                "followed by the unit 'h', 'm', or 's'."
            )


class NewProjectDirectoryValidator(NotEmptyValidator):
    def __init__(self) -> None:
        super().__init__("Path")

    def validate(self, document: Document) -> None:
        super().validate(document)
        directory = os.path.expanduser(document.text)
        if os.path.exists(directory) and os.path.isfile(directory):
            raise ValidationError(message=f"{self.label} must be a directory.")
        if os.path.exists(directory) and len(os.listdir(directory)) > 0:
            raise ValidationError(
                message=f"{self.label} must be empty if it is an existing directory."
            )


class UniquenessValidator(NotEmptyValidator):
    def __init__(self, label: str, existing: List) -> None:
        self.existing = existing
        super().__init__(label)

    def validate(self, document: Document) -> None:
        super().validate(document)
        string = document.text
        if string in self.existing:
            raise ValidationError(
                message=f"A {self.label.lower()} with that name already exists."
            )


class EulaValidator(Validator):  # type: ignore
    def validate(self, document: Document) -> None:
        file = document.text
        if not file.strip():
            return
        file = os.path.expanduser(file)
        if not os.path.isfile(file) or not os.path.splitext(file)[1] == ".txt":
            raise ValidationError(message="Path must be a text file.")


class ImageValidator(Validator):  # type: ignore
    def validate(self, document: Document) -> None:
        img = document.text
        if not img.strip():
            return
        try:
            img = os.path.expanduser(img)
            if os.path.isdir(img):
                raise ValidationError(message="Path must be an image file.")
            image = Image.open(img, formats=["PNG"])
            if image.size != (256, 256):
                raise ValidationError(
                    message=f"Image must be 256x256 pixels (selected image is {image.size[0]}x{image.size[1]} pixels)."
                )
        except FileNotFoundError:
            raise ValidationError(message="Could not find image file.")
        except TypeError:
            raise ValidationError(
                message="Image must be in PNG format and 256x256 pixels."
            )
        except UnidentifiedImageError as e:
            raise ValidationError(
                message=f"{e}. Image must be in PNG format and 256x256 pixels."
            )


class ProjectValidator(NotEmptyValidator):
    def __init__(self) -> None:
        super().__init__("Path")

    def validate(self, document: Document) -> None:
        super().validate(document)
        if not self.is_project_dir(document.text):
            raise ValidationError(
                message="Path must be a valid Management Pack project directory."
            )

    @classmethod
    def is_project_dir(cls, path: Optional[str]) -> bool:
        if path is None:
            return False
        path = os.path.expanduser(path)
        return os.path.isdir(path) and os.path.isfile(
            os.path.join(path, "manifest.txt")
        )


class ChainValidator(Validator):  # type: ignore
    def __init__(self, validators: List[Validator]) -> None:
        self.validators = validators

    def validate(self, document: Document) -> None:
        for validator in self.validators:
            validator.validate(document)
